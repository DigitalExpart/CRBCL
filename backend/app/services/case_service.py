"""Case management service orchestrating lifecycle transitions, snapshots, people, assignments, sources, links, and restrictions."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.case import Case
from app.models.case_management import (
    CaseAssignment,
    CaseLink,
    CasePerson,
    CaseRestriction,
)
from app.models.case_note import CaseNote
from app.models.client import Client
from app.models.family import Family
from app.models.person import Person
from app.models.referral import Referral
from app.models.user import User
from app.permissions.service import PermissionService
from app.repositories.case_management_repo import (
    CaseAssignmentRepository,
    CaseExternalWorkerRepository,
    CaseLinkRepository,
    CasePersonRepository,
    CaseRestrictionRepository,
    CaseSourceRepository,
    CaseStatusHistoryRepository,
)
from app.repositories.case_repo import CaseRepository
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.people_repo = CasePersonRepository(db)
        self.assignment_repo = CaseAssignmentRepository(db)
        self.external_repo = CaseExternalWorkerRepository(db)
        self.source_repo = CaseSourceRepository(db)
        self.link_repo = CaseLinkRepository(db)
        self.restriction_repo = CaseRestrictionRepository(db)
        self.status_history_repo = CaseStatusHistoryRepository(db)
        self.perm_service = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def get_case_or_404(self, case_id: uuid.UUID, current_user: User | None = None) -> Case:
        """Fetch case with authorization and restriction check."""
        case = await self.case_repo.get(case_id)
        if not case or case.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        if current_user:
            # Check Case Restrictions (ADR-010)
            if await self.perm_service.is_user_restricted_from_case(current_user.id, case_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Active conflict-of-interest restriction on this case.",
                )

            # Check Team Scope
            if not await self.perm_service.user_can_access_team(current_user.id, case.assigned_team_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Case is assigned to a team outside your scope.",
                )

        return case

    async def create_case(
        self,
        title: str,
        case_type: str,
        priority: str = "Medium",
        risk_level: str = "Medium",
        stage: str = "INVESTIGATION",
        description: str | None = None,
        client_id: uuid.UUID | None = None,
        family_id: uuid.UUID | None = None,
        assigned_worker_id: uuid.UUID | None = None,
        assigned_team_id: uuid.UUID | None = None,
        intake_date: date | None = None,
        current_user: User | None = None,
    ) -> Case:
        """Create a new Case with atomic sequence number and baseline assignment."""
        case_number = await self.case_repo.generate_case_number()

        assigned_worker_name = None
        if assigned_worker_id:
            user_stmt = select(User).where(User.id == assigned_worker_id)
            user_res = await self.db.execute(user_stmt)
            worker_user = user_res.scalar_one_or_none()
            if worker_user:
                assigned_worker_name = worker_user.full_name or worker_user.email

        case = await self.case_repo.create(
            case_number=case_number,
            title=title,
            case_type=case_type,
            status="Open",
            stage=stage,
            priority=priority,
            risk_level=risk_level,
            description=description,
            client_id=client_id,
            family_id=family_id,
            assigned_worker_id=assigned_worker_id,
            assigned_worker_name=assigned_worker_name,
            assigned_team_id=assigned_team_id,
            intake_date=intake_date or date.today(),
            created_by=current_user.id if current_user else None,
        )

        # Baseline assignment record
        if assigned_worker_id:
            await self.assignment_repo.create(
                case_id=case.id,
                user_id=assigned_worker_id,
                role="primary_investigator" if case_type == "PROTECTION" else "caseworker",
                is_active=True,
                assigned_by=current_user.id if current_user else None,
            )

        # Log status history
        await self.status_history_repo.create(
            case_id=case.id,
            previous_status=None,
            new_status="Open",
            reason="Initial Case File Opened",
            changed_by=current_user.id if current_user else None,
        )

        # Sacred Timeline
        await self.timeline.record_event(
            event_type="CASE_OPENED",
            title=f"Case {case.case_number} Created",
            description=f"{case_type} case opened: {title}",
            entity_type="case",
            entity_id=case.id,
            case_id=case.id,
            client_id=client_id,
            created_by=current_user.id if current_user else None,
        )

        # Transactional Outbox
        await self.outbox.enqueue(
            event_type="CASE_OPENED_NOTIFICATION",
            aggregate_type="case",
            aggregate_id=case.id,
            payload={
                "case_id": str(case.id),
                "case_number": case.case_number,
                "case_type": case.case_type,
                "title": case.title,
                "assigned_team_id": str(case.assigned_team_id) if case.assigned_team_id else None,
            },
        )

        # Audit Event
        await self.audit.log_event(
            event_type="CASE_CREATED",
            entity_type="case",
            entity_id=case.id,
            after_data={
                "case_number": case.case_number,
                "title": case.title,
                "case_type": case.case_type,
                "priority": case.priority,
            },
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def update_case(
        self,
        case_id: uuid.UUID,
        update_data: dict,
        current_user: User,
    ) -> Case:
        """Update case properties (excluding direct status manipulation)."""
        case = await self.get_case_or_404(case_id, current_user)

        # Status must NOT be changed via generic PATCH (ADR-009)
        if "status" in update_data and update_data["status"] != case.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case status cannot be changed directly. Use formal lifecycle command endpoints (/close, /reopen).",
            )

        for key, val in update_data.items():
            if hasattr(case, key) and key not in ("id", "case_number", "created_at", "created_by"):
                setattr(case, key, val)

        case.updated_at = datetime.now(UTC)
        case.updated_by = current_user.id

        await self.audit.log_event(
            event_type="CASE_UPDATED",
            entity_type="case",
            entity_id=case.id,
            after_data=update_data,
            user_id=current_user.id,
        )

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def close_case(
        self,
        case_id: uuid.UUID,
        closed_reason: str,
        closed_date: date | None = None,
        current_user: User | None = None,
    ) -> Case:
        """Controlled case closure with status history and audit."""
        case = await self.get_case_or_404(case_id, current_user)
        if case.status == "Closed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Case is already closed.")

        prev_status = case.status
        case.status = "Closed"
        case.stage = "CLOSURE"
        case.closed_date = closed_date or date.today()
        case.closed_reason = closed_reason
        case.updated_at = datetime.now(UTC)
        case.updated_by = current_user.id if current_user else None

        await self.status_history_repo.create(
            case_id=case.id,
            previous_status=prev_status,
            new_status="Closed",
            reason=closed_reason,
            changed_by=current_user.id if current_user else None,
        )

        await self.timeline.record_event(
            event_type="CASE_CLOSED",
            title=f"Case {case.case_number} Closed",
            description=f"Case closed. Rationale: {closed_reason}",
            entity_type="case",
            entity_id=case.id,
            case_id=case.id,
            created_by=current_user.id if current_user else None,
        )

        await self.audit.log_event(
            event_type="CASE_CLOSED",
            entity_type="case",
            entity_id=case.id,
            after_data={"previous_status": prev_status, "new_status": "Closed", "reason": closed_reason},
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def reopen_case(
        self,
        case_id: uuid.UUID,
        reopen_reason: str,
        current_user: User | None = None,
    ) -> Case:
        """Controlled case reopening preserving past closure history."""
        case = await self.get_case_or_404(case_id, current_user)
        if case.status != "Closed":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only closed cases can be reopened.")

        prev_status = case.status
        case.status = "Reopened"
        case.stage = "INVESTIGATION"
        case.reopened_at = datetime.now(UTC)
        case.reopened_by = current_user.id if current_user else None
        case.reopened_reason = reopen_reason
        case.updated_at = datetime.now(UTC)
        case.updated_by = current_user.id if current_user else None

        await self.status_history_repo.create(
            case_id=case.id,
            previous_status=prev_status,
            new_status="Reopened",
            reason=reopen_reason,
            changed_by=current_user.id if current_user else None,
        )

        await self.timeline.record_event(
            event_type="CASE_REOPENED",
            title=f"Case {case.case_number} Reopened",
            description=f"Case reopened. Rationale: {reopen_reason}",
            entity_type="case",
            entity_id=case.id,
            case_id=case.id,
            created_by=current_user.id if current_user else None,
        )

        await self.audit.log_event(
            event_type="CASE_REOPENED",
            entity_type="case",
            entity_id=case.id,
            after_data={"previous_status": prev_status, "new_status": "Reopened", "reason": reopen_reason},
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def get_case_snapshot(self, case_id: uuid.UUID, current_user: User) -> dict:
        """Efficient at-a-glance snapshot aggregation without N+1 queries."""
        case = await self.get_case_or_404(case_id, current_user)

        # Primary Client / Person
        client_data = None
        if case.client_id:
            cl_stmt = select(Client).where(Client.id == case.client_id)
            cl_res = await self.db.execute(cl_stmt)
            cl = cl_res.scalar_one_or_none()
            if cl:
                client_data = {
                    "id": str(cl.id),
                    "full_name": f"{cl.first_name} {cl.last_name}",
                    "gender": cl.gender,
                    "date_of_birth": cl.date_of_birth.isoformat() if cl.date_of_birth else None,
                }

        # Family
        family_data = None
        if case.family_id:
            fam_stmt = select(Family).where(Family.id == case.family_id)
            fam_res = await self.db.execute(fam_stmt)
            fam = fam_res.scalar_one_or_none()
            if fam:
                family_data = {
                    "id": str(fam.id),
                    "family_name": fam.family_name,
                    "first_nation": fam.first_nation_community,
                }

        # Originating Referral Provenance
        origin_referral_data = None
        if case.origin_referral_id:
            ref_stmt = select(Referral).where(Referral.id == case.origin_referral_id)
            ref_res = await self.db.execute(ref_stmt)
            ref = ref_res.scalar_one_or_none()
            if ref:
                origin_referral_data = {
                    "id": str(ref.id),
                    "referral_number": ref.referral_number,
                    "received_date": ref.received_date.isoformat() if ref.received_date else None,
                    "received_method": ref.received_method,
                    "priority": ref.priority,
                }

        # Assigned Workers
        assignments = await self.assignment_repo.get_by_case(case.id)
        active_workers = [
            {
                "id": str(a.id),
                "user_id": str(a.user_id),
                "name": a.user.full_name or a.user.email if a.user else "Assigned Worker",
                "email": a.user.email if a.user else None,
                "role": a.role,
                "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None,
            }
            for a in assignments
            if a.is_active
        ]

        # People Count
        people = await self.people_repo.get_by_case(case.id)

        # Last Note Date & Next Appointment
        last_note_stmt = (
            select(CaseNote.created_at, CaseNote.next_appointment_at)
            .where(CaseNote.case_id == case.id, CaseNote.deleted_at.is_(None))
            .order_by(CaseNote.created_at.desc())
            .limit(1)
        )
        note_res = await self.db.execute(last_note_stmt)
        latest_note = note_res.first()
        last_note_date = latest_note[0].isoformat() if latest_note and latest_note[0] else None
        next_appointment = latest_note[1].isoformat() if latest_note and latest_note[1] else None

        # Days Open
        days_open = 0
        if case.intake_date:
            end = case.closed_date or date.today()
            days_open = (end - case.intake_date).days

        # Critical Alerts
        alerts = []
        if case.risk_level in ("High", "Critical"):
            alerts.append({"severity": "high", "message": f"Elevated Risk: Case is designated {case.risk_level} risk."})
        if days_open > 365:
            alerts.append({"severity": "warning", "message": f"Extended Case: Open for {days_open} days (>12 months)."})
        if not last_note_date and days_open > 14:
            alerts.append(
                {"severity": "warning", "message": "Documentation Alert: No recorded case notes in >14 days."}
            )

        return {
            "case_id": str(case.id),
            "case_number": case.case_number,
            "title": case.title,
            "case_type": case.case_type,
            "status": case.status,
            "stage": case.stage,
            "priority": case.priority,
            "risk_level": case.risk_level,
            "description": case.description,
            "intake_date": case.intake_date.isoformat() if case.intake_date else None,
            "closed_date": case.closed_date.isoformat() if case.closed_date else None,
            "days_open": days_open,
            "primary_client": client_data,
            "family": family_data,
            "origin_referral": origin_referral_data,
            "active_workers": active_workers,
            "total_people_count": len(people),
            "last_note_date": last_note_date,
            "next_appointment": next_appointment,
            "alerts": alerts,
        }

    # ── People Operations ──────────────────────────────────────
    async def add_person_to_case(
        self,
        case_id: uuid.UUID,
        person_id: uuid.UUID,
        role: str = "other",
        relationship_to_subject: str | None = None,
        is_primary: bool = False,
        notes: str | None = None,
        current_user: User | None = None,
    ) -> CasePerson:
        case = await self.get_case_or_404(case_id, current_user)
        person_stmt = select(Person).where(Person.id == person_id)
        person_res = await self.db.execute(person_stmt)
        person = person_res.scalar_one_or_none()
        if not person:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person not found")

        case_person = await self.people_repo.create(
            case_id=case.id,
            person_id=person.id,
            role=role,
            relationship_to_subject=relationship_to_subject,
            is_primary=is_primary,
            start_date=date.today(),
            notes=notes,
            created_by=current_user.id if current_user else None,
        )

        await self.timeline.record_event(
            event_type="PERSON_ADDED_TO_CASE",
            title=f"{person.first_name} {person.last_name} Added",
            description=f"Added to case {case.case_number} as {role}.",
            entity_type="case",
            entity_id=case.id,
            case_id=case.id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return case_person

    # ── Worker Assignments ─────────────────────────────────────
    async def assign_worker(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str = "caseworker",
        notes: str | None = None,
        current_user: User | None = None,
    ) -> CaseAssignment:
        case = await self.get_case_or_404(case_id, current_user)
        user_stmt = select(User).where(User.id == user_id)
        user_res = await self.db.execute(user_stmt)
        worker = user_res.scalar_one_or_none()
        if not worker:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Check if worker is restricted from this case (ADR-010)
        if await self.perm_service.is_user_restricted_from_case(worker.id, case.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign {worker.full_name or worker.email}: Active conflict restriction exists.",
            )

        if role == "primary_investigator":
            await self.assignment_repo.deactivate_previous_role_assignment(case.id, "primary_investigator")
            case.assigned_worker_id = worker.id
            case.assigned_worker_name = worker.full_name or worker.email

        assignment = await self.assignment_repo.create(
            case_id=case.id,
            user_id=worker.id,
            role=role,
            is_active=True,
            assigned_by=current_user.id if current_user else None,
            notes=notes,
        )

        await self.timeline.record_event(
            event_type="WORKER_ASSIGNED",
            title=f"Worker Assigned: {worker.full_name or worker.email}",
            description=f"Assigned as {role} on case {case.case_number}.",
            entity_type="case",
            entity_id=case.id,
            case_id=case.id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return assignment

    async def unassign_worker(
        self,
        assignment_id: uuid.UUID,
        current_user: User | None = None,
    ) -> None:
        assignment = await self.assignment_repo.get(assignment_id)
        if not assignment or not assignment.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active assignment not found")

        assignment.is_active = False
        assignment.unassigned_at = datetime.now(UTC)

        await self.timeline.record_event(
            event_type="WORKER_UNASSIGNED",
            title="Worker Assignment Ended",
            description=f"Ended assignment for {assignment.role}.",
            entity_type="case",
            entity_id=assignment.case_id,
            case_id=assignment.case_id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()

    # ── Case Links ─────────────────────────────────────────────
    async def create_case_link(
        self,
        source_case_id: uuid.UUID,
        target_case_id: uuid.UUID,
        link_type: str = "related_family",
        reason: str | None = None,
        current_user: User | None = None,
    ) -> CaseLink:
        if source_case_id == target_case_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot link a case to itself.")

        source_case = await self.get_case_or_404(source_case_id, current_user)
        target_case = await self.get_case_or_404(target_case_id, current_user)

        if await self.link_repo.link_exists(source_case_id, target_case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cases are already linked.")

        link = await self.link_repo.create(
            source_case_id=source_case.id,
            target_case_id=target_case.id,
            link_type=link_type,
            reason=reason,
            linked_by=current_user.id if current_user else None,
        )

        await self.timeline.record_event(
            event_type="CASE_LINKED",
            title=f"Linked to Case {target_case.case_number}",
            description=f"Link type: {link_type}. Reason: {reason or 'None'}",
            entity_type="case",
            entity_id=source_case.id,
            case_id=source_case.id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return link

    # ── Case Restrictions (Conflict of Interest) ───────────────
    async def add_case_restriction(
        self,
        case_id: uuid.UUID,
        user_id: uuid.UUID,
        restriction_type: str,
        reason: str,
        current_user: User | None = None,
    ) -> CaseRestriction:
        case = await self.get_case_or_404(case_id, current_user)
        user_stmt = select(User).where(User.id == user_id)
        user_res = await self.db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Deactivate any active assignments this user currently holds on the case
        stmt = select(CaseAssignment).where(
            CaseAssignment.case_id == case.id,
            CaseAssignment.user_id == user.id,
            CaseAssignment.is_active == True,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        for a in res.scalars().all():
            a.is_active = False
            a.unassigned_at = datetime.now(UTC)

        restriction = await self.restriction_repo.create(
            case_id=case.id,
            user_id=user.id,
            restriction_type=restriction_type,
            reason=reason,
            is_active=True,
            created_by=current_user.id if current_user else None,
        )

        await self.audit.log_event(
            event_type="CASE_RESTRICTION_CREATED",
            entity_type="case_restriction",
            entity_id=restriction.id,
            after_data={
                "case_id": str(case.id),
                "user_id": str(user.id),
                "restriction_type": restriction_type,
                "reason": reason,
            },
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        return restriction

    async def remove_case_restriction(
        self,
        restriction_id: uuid.UUID,
        removal_reason: str,
        current_user: User | None = None,
    ) -> CaseRestriction:
        restriction = await self.restriction_repo.get(restriction_id)
        if not restriction or not restriction.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active restriction not found")

        restriction.is_active = False
        restriction.removed_at = datetime.now(UTC)
        restriction.removed_by = current_user.id if current_user else None
        restriction.removal_reason = removal_reason

        await self.audit.log_event(
            event_type="CASE_RESTRICTION_REMOVED",
            entity_type="case_restriction",
            entity_id=restriction.id,
            after_data={"is_active": False, "removal_reason": removal_reason},
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        return restriction
