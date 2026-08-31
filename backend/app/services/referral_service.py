"""Referral service handling domain operations, privacy redactions, and state transitions."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.referral import Referral
from app.repositories.referral_repo import ReferralRepository
from app.schemas.referral import (
    ChildDispositionResponse,
    IntakeDecisionResponse,
    ReferralConcernResponse,
    ReferralDetailResponse,
    ReferralIncidentResponse,
    ReferralLinkResponse,
    ReferralPersonResponse,
    ReferralReporterResponse,
)
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class ReferralService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReferralRepository(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def create_referral(self, data: dict, created_by: uuid.UUID | None = None) -> Referral:
        """Create a new referral in DRAFT state."""
        reporter_data = data.pop("reporter", None)
        people_data = data.pop("people", [])
        concerns_data = data.pop("concerns", [])
        incidents_data = data.pop("incidents", [])

        data["status"] = "DRAFT"
        data["created_by"] = created_by
        data["updated_by"] = created_by

        referral = await self.repo.create(data)

        # Save nested items if provided
        if reporter_data:
            await self.repo.save_reporter(referral.id, reporter_data)

        for p in people_data:
            await self.repo.add_person(
                referral_id=referral.id,
                person_id=p["person_id"],
                role=p["role"],
                relationship_to_child=p.get("relationship_to_child"),
                is_primary_caregiver=p.get("is_primary_caregiver", False),
                is_subject_of_concern=p.get("is_subject_of_concern", False),
                notes=p.get("notes"),
            )

        for c in concerns_data:
            await self.repo.add_concern(referral.id, c)

        for inc in incidents_data:
            await self.repo.add_incident(referral.id, inc)

        # Audit & Timeline
        await self.audit.log_event(
            event_type="REFERRAL_CREATED",
            user_id=created_by,
            entity_type="referral",
            entity_id=referral.id,
            after_data={"referral_number": referral.referral_number, "status": referral.status},
        )

        await self.timeline.record_event(
            event_type="REFERRAL_RECEIVED",
            title=f"Intake Referral {referral.referral_number} Logged",
            description=f"Referral received via {referral.received_method} for community {referral.community or 'Unspecified'}.",
            entity_type="referral",
            entity_id=referral.id,
            created_by=created_by,
        )

        return referral

    async def get_referral_detail(
        self,
        referral_id: uuid.UUID,
        can_read_reporter: bool = False,
    ) -> ReferralDetailResponse | None:
        """Retrieve 360° referral detail with backend reporter redaction if unauthorized."""
        referral = await self.repo.get_by_id(referral_id)
        if not referral:
            return None

        # Build people responses
        people_responses = []
        children_count = 0
        for rp in referral.people:
            if rp.role == "child":
                children_count += 1
            people_responses.append(
                ReferralPersonResponse(
                    id=rp.id,
                    referral_id=rp.referral_id,
                    person_id=rp.person_id,
                    role=rp.role,
                    relationship_to_child=rp.relationship_to_child,
                    is_primary_caregiver=rp.is_primary_caregiver,
                    is_subject_of_concern=rp.is_subject_of_concern,
                    notes=rp.notes,
                    created_at=rp.created_at,
                    first_name=rp.person.first_name if rp.person else None,
                    last_name=rp.person.last_name if rp.person else None,
                    date_of_birth=rp.person.date_of_birth if rp.person else None,
                    gender=rp.person.gender if rp.person else None,
                    indigenous_identity=rp.person.indigenous_identity if rp.person else None,
                    band_nation=rp.person.band_nation if rp.person else None,
                    phone=rp.person.phone if rp.person else None,
                )
            )

        # Build reporter response with confidentiality enforcement
        reporter_response = None
        if referral.reporter:
            rep = referral.reporter
            if can_read_reporter or rep.is_anonymous:
                reporter_response = ReferralReporterResponse(
                    id=rep.id,
                    referral_id=rep.referral_id,
                    is_anonymous=rep.is_anonymous,
                    is_mandated_reporter=rep.is_mandated_reporter,
                    wants_notification=rep.wants_notification,
                    reporter_name=rep.reporter_name if not rep.is_anonymous else "[ANONYMOUS]",
                    organization=rep.organization,
                    phone=rep.phone if not rep.is_anonymous else None,
                    email=rep.email if not rep.is_anonymous else None,
                    preferred_contact_method=rep.preferred_contact_method,
                    relationship_to_family=rep.relationship_to_family,
                    reporter_notes=rep.reporter_notes,
                    is_redacted=False,
                )
            else:
                # Redacted container for users without intake.reporter.read
                reporter_response = ReferralReporterResponse(
                    id=rep.id,
                    referral_id=rep.referral_id,
                    is_anonymous=rep.is_anonymous,
                    is_mandated_reporter=rep.is_mandated_reporter,
                    wants_notification=rep.wants_notification,
                    reporter_name="[CONFIDENTIAL / REDACTED]",
                    organization=rep.organization,
                    phone=None,
                    email=None,
                    preferred_contact_method=None,
                    relationship_to_family=None,
                    reporter_notes=None,
                    is_redacted=True,
                )

        # Build incidents, concerns, dispositions
        incidents = [ReferralIncidentResponse.model_validate(inc) for inc in referral.incidents]
        concerns = [ReferralConcernResponse.model_validate(c) for c in referral.concerns]

        primary_concern = next((c.concern_type for c in referral.concerns if c.is_primary), None)
        if not primary_concern and referral.concerns:
            primary_concern = referral.concerns[0].concern_type

        dispositions = []
        for d in referral.dispositions:
            dispositions.append(
                ChildDispositionResponse(
                    id=d.id,
                    referral_id=d.referral_id,
                    person_id=d.person_id,
                    decision=d.decision,
                    reason=d.reason,
                    destination_team_id=d.destination_team_id,
                    destination_program=d.destination_program,
                    external_agency_name=d.external_agency_name,
                    external_referral_contact=d.external_referral_contact,
                    resulting_case_id=d.resulting_case_id,
                    decided_by=d.decided_by,
                    decided_at=d.decided_at,
                    approval_state=d.approval_state,
                    child_first_name=d.person.first_name if d.person else None,
                    child_last_name=d.person.last_name if d.person else None,
                    child_date_of_birth=d.person.date_of_birth if d.person else None,
                )
            )

        decision_resp = IntakeDecisionResponse.model_validate(referral.decision) if referral.decision else None

        links = [
            ReferralLinkResponse(
                id=lk.id,
                source_referral_id=lk.source_referral_id,
                target_referral_id=lk.target_referral_id,
                target_referral_number=lk.target_referral.referral_number if lk.target_referral else None,
                target_referral_status=lk.target_referral.status if lk.target_referral else None,
                link_type=lk.link_type,
                reason=lk.reason,
                created_at=lk.created_at,
            )
            for lk in referral.outgoing_links
        ]

        return ReferralDetailResponse(
            id=referral.id,
            referral_number=referral.referral_number,
            status=referral.status,
            received_date=referral.received_date,
            received_time=referral.received_time,
            received_method=referral.received_method,
            community=referral.community,
            priority=referral.priority,
            risk_level=referral.risk_level,
            summary=referral.summary,
            immediate_safety_concerns=referral.immediate_safety_concerns,
            law_enforcement_involved=referral.law_enforcement_involved,
            law_enforcement_file_number=referral.law_enforcement_file_number,
            law_enforcement_officer_info=referral.law_enforcement_officer_info,
            assigned_worker_id=referral.assigned_worker_id,
            assigned_worker_name=referral.assigned_worker_name,
            assigned_team_id=referral.assigned_team_id,
            origin_agency=referral.origin_agency,
            notes=referral.notes,
            version=referral.version,
            created_at=referral.created_at,
            updated_at=referral.updated_at,
            people_count=len(people_responses),
            children_count=children_count,
            primary_concern=primary_concern,
            people=people_responses,
            reporter=reporter_response,
            incidents=incidents,
            concerns=concerns,
            dispositions=dispositions,
            decision=decision_resp,
            links=links,
        )

    async def update_referral(self, referral_id: uuid.UUID, data: dict, user_id: uuid.UUID | None = None) -> Referral:
        """Update referral metadata."""
        # Status cannot be updated directly via update_referral
        data.pop("status", None)
        data.pop("referral_number", None)
        data["updated_by"] = user_id

        before = await self.repo.get_by_id(referral_id)
        before_data = {"summary": before.summary, "priority": before.priority} if before else None

        updated = await self.repo.update(referral_id, data)
        if not updated:
            raise ValueError(f"Referral {referral_id} not found")

        await self.audit.log_event(
            event_type="REFERRAL_UPDATED",
            user_id=user_id,
            entity_type="referral",
            entity_id=referral_id,
            before_data=before_data,
            after_data=data,
        )
        return updated
