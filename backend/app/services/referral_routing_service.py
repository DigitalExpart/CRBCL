"""Referral routing service executing case creation and disposition assignments on approval."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.case import Case
from app.models.case_management import CaseAssignment, CasePerson, CaseStatusHistory
from app.models.client import Client
from app.models.person import Person
from app.models.referral import Referral
from app.repositories.case_repo import CaseRepository
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class ReferralRoutingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def route_approved_referral(
        self,
        referral: Referral,
        supervisor_id: uuid.UUID,
    ) -> list[Case]:
        """Atomically create resulting cases and update disposition approval states."""
        created_cases: list[Case] = []

        for disp in referral.dispositions:
            disp.approval_state = "APPROVED"

            # Retrieve person/child details
            person_stmt = select(Person).where(Person.id == disp.person_id)
            person_res = await self.db.execute(person_stmt)
            person = person_res.scalar_one_or_none()
            child_name = f"{person.first_name} {person.last_name}" if person else "Child"

            # Check if person is already linked to a client
            client_stmt = (
                select(Client).where((Client.first_name == person.first_name) & (Client.last_name == person.last_name))
                if person
                else None
            )
            client_id = None
            if client_stmt is not None:
                client_res = await self.db.execute(client_stmt)
                client = client_res.scalar_one_or_none()
                if client:
                    client_id = client.id

            if disp.decision == "PROTECTION":
                # Check for existing case to ensure idempotency
                existing_stmt = select(Case).where(Case.origin_disposition_id == disp.id)
                existing_res = await self.db.execute(existing_stmt)
                existing_case = existing_res.scalar_one_or_none()

                if not existing_case:
                    case_num = await self.case_repo.generate_case_number()
                    case = await self.case_repo.create(
                        case_number=case_num,
                        title=f"Child Safety Investigation: {child_name}",
                        case_type="Child Safety (Protection)",
                        status="Open",
                        stage="INVESTIGATION",
                        priority="High",
                        risk_level=referral.risk_level or "High",
                        description=f"Initiated from Referral {referral.referral_number}. Primary Reason: {disp.reason}",
                        client_id=client_id,
                        assigned_worker_id=referral.assigned_worker_id,
                        assigned_worker_name=referral.assigned_worker_name,
                        assigned_team_id=disp.destination_team_id or referral.assigned_team_id,
                        referral_source=referral.received_method,
                        intake_date=referral.received_date,
                        origin_referral_id=referral.id,
                        origin_disposition_id=disp.id,
                        created_by=supervisor_id,
                    )

                    # Relational subject child attachment
                    if person:
                        self.db.add(
                            CasePerson(
                                case_id=case.id,
                                person_id=person.id,
                                role="subject_child",
                                is_primary=True,
                                start_date=referral.received_date,
                                created_by=supervisor_id,
                            )
                        )

                    # Baseline assignment
                    if referral.assigned_worker_id:
                        self.db.add(
                            CaseAssignment(
                                case_id=case.id,
                                user_id=referral.assigned_worker_id,
                                role="primary_investigator",
                                is_active=True,
                                assigned_by=supervisor_id,
                            )
                        )

                    # Status History
                    self.db.add(
                        CaseStatusHistory(
                            case_id=case.id,
                            previous_status=None,
                            new_status="Open",
                            reason=f"Created on approval of Referral {referral.referral_number}",
                            changed_by=supervisor_id,
                        )
                    )

                    disp.resulting_case_id = case.id
                    created_cases.append(case)

                    # Timeline & Audit
                    await self.timeline.record_event(
                        event_type="CASE_CREATED_FROM_INTAKE",
                        title=f"Protection Case {case.case_number} Created",
                        description=f"Generated from Intake {referral.referral_number} for {child_name}.",
                        entity_type="case",
                        entity_id=case.id,
                        case_id=case.id,
                        client_id=client_id,
                        created_by=supervisor_id,
                    )

            elif disp.decision in ("PREVENTION", "POST_MAJORITY"):
                case_type = "Family Prevention" if disp.decision == "PREVENTION" else "Post-Majority Support"
                existing_stmt = select(Case).where(Case.origin_disposition_id == disp.id)
                existing_res = await self.db.execute(existing_stmt)
                existing_case = existing_res.scalar_one_or_none()

                if not existing_case:
                    case_num = await self.case_repo.generate_case_number()
                    case = await self.case_repo.create(
                        case_number=case_num,
                        title=f"{case_type}: {child_name}",
                        case_type=case_type,
                        status="Open",
                        stage="SERVICE_DELIVERY",
                        priority="Medium",
                        risk_level=referral.risk_level or "Medium",
                        description=f"Initiated from Referral {referral.referral_number}. Services Goal: {disp.reason}",
                        client_id=client_id,
                        assigned_worker_id=referral.assigned_worker_id,
                        assigned_worker_name=referral.assigned_worker_name,
                        assigned_team_id=disp.destination_team_id or referral.assigned_team_id,
                        referral_source=referral.received_method,
                        intake_date=referral.received_date,
                        origin_referral_id=referral.id,
                        origin_disposition_id=disp.id,
                        created_by=supervisor_id,
                    )

                    # Relational subject child attachment
                    if person:
                        self.db.add(
                            CasePerson(
                                case_id=case.id,
                                person_id=person.id,
                                role="subject_child",
                                is_primary=True,
                                start_date=referral.received_date,
                                created_by=supervisor_id,
                            )
                        )

                    # Baseline assignment
                    if referral.assigned_worker_id:
                        self.db.add(
                            CaseAssignment(
                                case_id=case.id,
                                user_id=referral.assigned_worker_id,
                                role="caseworker",
                                is_active=True,
                                assigned_by=supervisor_id,
                            )
                        )

                    # Status History
                    self.db.add(
                        CaseStatusHistory(
                            case_id=case.id,
                            previous_status=None,
                            new_status="Open",
                            reason=f"Created on approval of Referral {referral.referral_number}",
                            changed_by=supervisor_id,
                        )
                    )

                    disp.resulting_case_id = case.id
                    created_cases.append(case)

                    await self.timeline.record_event(
                        event_type="CASE_CREATED_FROM_INTAKE",
                        title=f"{case_type} Case {case.case_number} Opened",
                        description=f"Voluntary wellness case opened from Referral {referral.referral_number} for {child_name}.",
                        entity_type="case",
                        entity_id=case.id,
                        case_id=case.id,
                        client_id=client_id,
                        created_by=supervisor_id,
                    )

            elif disp.decision == "EXTERNAL_REFERRAL":
                await self.timeline.record_event(
                    event_type="EXTERNAL_REFERRAL_RECORDED",
                    title=f"External Referral Recorded for {child_name}",
                    description=f"Referred to {disp.external_agency_name or 'External Agency'}. Notes: {disp.reason}",
                    entity_type="referral",
                    entity_id=referral.id,
                    created_by=supervisor_id,
                )

            elif disp.decision == "SCREEN_OUT":
                await self.timeline.record_event(
                    event_type="CHILD_DISPOSITION_APPROVED",
                    title=f"Screened Out: {child_name}",
                    description=f"No formal case required. Assessment reason: {disp.reason}",
                    entity_type="referral",
                    entity_id=referral.id,
                    created_by=supervisor_id,
                )

        await self.db.flush()
        return created_cases
