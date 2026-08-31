"""Intake approval workflow service handling worker submission, supervisor approval, and return."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.referral import Referral
from app.repositories.referral_repo import ReferralRepository
from app.services.intake_decision_service import IntakeDecisionService
from app.services.referral_routing_service import ReferralRoutingService
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class IntakeApprovalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReferralRepository(db)
        self.decision_service = IntakeDecisionService(db)
        self.routing_service = ReferralRoutingService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def submit_for_approval(
        self,
        referral_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Referral:
        """Worker submits referral for supervisor review."""
        referral = await self.repo.get_by_id(referral_id)
        if not referral:
            raise ValueError("Referral not found")

        if referral.status not in ("DRAFT", "IN_PROGRESS", "RETURNED", "RECEIVED"):
            raise ValueError(f"Cannot submit referral in status '{referral.status}' for supervisor approval.")

        # Validate readiness
        is_ready, errors = await self.decision_service.validate_readiness_for_submission(referral_id)
        if not is_ready:
            raise ValueError(f"Referral validation failed: {'; '.join(errors)}")

        before_status = referral.status
        referral.status = "PENDING_SUPERVISOR"
        referral.updated_by = user_id
        referral.updated_at = datetime.now(UTC)
        referral.version += 1

        if referral.decision:
            referral.decision.submitted_by = user_id
            referral.decision.submitted_at = datetime.now(UTC)

        await self.db.flush()

        # Audit, Timeline, Outbox
        await self.audit.log_event(
            event_type="INTAKE_SUBMITTED",
            user_id=user_id,
            entity_type="referral",
            entity_id=referral.id,
            before_data={"status": before_status},
            after_data={"status": "PENDING_SUPERVISOR"},
        )

        await self.timeline.record_event(
            event_type="INTAKE_SUBMITTED",
            title=f"Intake {referral.referral_number} Submitted for Approval",
            description=f"Submitted by worker for supervisor review. Dispositions recorded for {len(referral.dispositions)} children.",
            entity_type="referral",
            entity_id=referral.id,
            created_by=user_id,
        )

        await self.outbox.enqueue(
            event_type="INTAKE_SUBMITTED",
            aggregate_type="referral",
            aggregate_id=referral.id,
            payload={
                "referral_id": str(referral.id),
                "referral_number": referral.referral_number,
                "team_id": str(referral.assigned_team_id) if referral.assigned_team_id else None,
                "message": f"Referral {referral.referral_number} is pending supervisor approval.",
            },
        )

        return referral

    async def return_to_worker(
        self,
        referral_id: uuid.UUID,
        supervisor_id: uuid.UUID,
        return_reason: str,
    ) -> Referral:
        """Supervisor returns referral to worker with revision comments."""
        if not return_reason or not return_reason.strip():
            raise ValueError("Return comments are required when returning an intake referral.")

        referral = await self.repo.get_by_id(referral_id)
        if not referral:
            raise ValueError("Referral not found")

        if referral.status != "PENDING_SUPERVISOR":
            raise ValueError(
                f"Cannot return referral in status '{referral.status}'. It must be in PENDING_SUPERVISOR state."
            )

        before_status = referral.status
        referral.status = "RETURNED"
        referral.updated_by = supervisor_id
        referral.updated_at = datetime.now(UTC)
        referral.version += 1

        if referral.decision:
            referral.decision.returned_by = supervisor_id
            referral.decision.returned_at = datetime.now(UTC)
            referral.decision.return_reason = return_reason.strip()

        await self.db.flush()

        # Audit, Timeline, Outbox
        await self.audit.log_event(
            event_type="INTAKE_RETURNED",
            user_id=supervisor_id,
            entity_type="referral",
            entity_id=referral.id,
            before_data={"status": before_status},
            after_data={"status": "RETURNED", "return_reason": return_reason.strip()},
        )

        await self.timeline.record_event(
            event_type="INTAKE_RETURNED",
            title=f"Intake {referral.referral_number} Returned by Supervisor",
            description=f"Returned with comments: {return_reason.strip()}",
            entity_type="referral",
            entity_id=referral.id,
            created_by=supervisor_id,
        )

        await self.outbox.enqueue(
            event_type="INTAKE_RETURNED",
            aggregate_type="referral",
            aggregate_id=referral.id,
            payload={
                "referral_id": str(referral.id),
                "referral_number": referral.referral_number,
                "assigned_worker_id": str(referral.assigned_worker_id) if referral.assigned_worker_id else None,
                "return_reason": return_reason.strip(),
                "message": f"Referral {referral.referral_number} returned with comments: {return_reason.strip()}",
            },
        )

        return referral

    async def approve_referral(
        self,
        referral_id: uuid.UUID,
        supervisor_id: uuid.UUID,
        supervisor_notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> Referral:
        """Supervisor approves referral and triggers atomic child disposition routing."""
        referral = await self.repo.get_by_id(referral_id)
        if not referral:
            raise ValueError("Referral not found")

        # Idempotency check
        if referral.status == "APPROVED":
            return referral

        if referral.status != "PENDING_SUPERVISOR":
            raise ValueError(
                f"Cannot approve referral in status '{referral.status}'. Must be in PENDING_SUPERVISOR state."
            )

        before_status = referral.status
        referral.status = "APPROVED"
        referral.updated_by = supervisor_id
        referral.updated_at = datetime.now(UTC)
        referral.version += 1

        if referral.decision:
            referral.decision.approved_by = supervisor_id
            referral.decision.approved_at = datetime.now(UTC)
            referral.decision.supervisor_notes = supervisor_notes

        await self.db.flush()

        # Execute automated child routing
        created_cases = await self.routing_service.route_approved_referral(referral, supervisor_id)

        # Audit, Timeline, Outbox
        await self.audit.log_event(
            event_type="INTAKE_APPROVED",
            user_id=supervisor_id,
            entity_type="referral",
            entity_id=referral.id,
            before_data={"status": before_status},
            after_data={"status": "APPROVED", "cases_created": len(created_cases)},
        )

        await self.timeline.record_event(
            event_type="INTAKE_APPROVED",
            title=f"Intake {referral.referral_number} Approved by Supervisor",
            description=f"Approved with {len(referral.dispositions)} child disposition(s). {len(created_cases)} resulting case(s) opened.",
            entity_type="referral",
            entity_id=referral.id,
            created_by=supervisor_id,
        )

        await self.outbox.enqueue(
            event_type="INTAKE_APPROVED",
            aggregate_type="referral",
            aggregate_id=referral.id,
            payload={
                "referral_id": str(referral.id),
                "referral_number": referral.referral_number,
                "assigned_worker_id": str(referral.assigned_worker_id) if referral.assigned_worker_id else None,
                "cases_count": len(created_cases),
                "message": f"Referral {referral.referral_number} has been approved.",
            },
        )

        return referral
