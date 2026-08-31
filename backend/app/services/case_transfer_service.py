"""Case & Child transfer workflow service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.case_management import CaseTransfer
from app.models.team import Team
from app.models.user import User
from app.repositories.case_management_repo import CaseAssignmentRepository, CaseTransferRepository
from app.repositories.case_repo import CaseRepository
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class CaseTransferService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.transfer_repo = CaseTransferRepository(db)
        self.case_repo = CaseRepository(db)
        self.assignment_repo = CaseAssignmentRepository(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def create_transfer_request(
        self,
        case_id: uuid.UUID,
        destination_team_id: uuid.UUID,
        reason: str,
        child_id: uuid.UUID | None = None,
        is_submitted: bool = False,
        current_user: User | None = None,
    ) -> CaseTransfer:
        case = await self.case_repo.get(case_id)
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

        dest_team_res = await self.db.execute(select(Team).where(Team.id == destination_team_id))
        dest_team = dest_team_res.scalar_one_or_none()
        if not dest_team:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Destination team not found")

        if case.assigned_team_id == destination_team_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Destination team cannot be the same as current assigned team.",
            )

        transfer = await self.transfer_repo.create(
            case_id=case.id,
            child_id=child_id,
            source_team_id=case.assigned_team_id or destination_team_id,
            destination_team_id=destination_team_id,
            reason=reason,
            status="PENDING_APPROVAL" if is_submitted else "DRAFT",
            requested_by=current_user.id if current_user else None,
            requested_at=datetime.now(UTC),
        )

        if is_submitted:
            await self.timeline.record_event(
                event_type="TRANSFER_REQUESTED",
                title=f"Transfer to {dest_team.name} Requested",
                description=f"Transfer request submitted for case {case.case_number}. Reason: {reason}",
                entity_type="case",
                entity_id=case.id,
                case_id=case.id,
                created_by=current_user.id if current_user else None,
            )

        await self.db.commit()
        return transfer

    async def submit_transfer_request(
        self,
        transfer_id: uuid.UUID,
        current_user: User | None = None,
    ) -> CaseTransfer:
        transfer = await self.transfer_repo.get(transfer_id)
        if not transfer or transfer.status not in ("DRAFT", "RETURNED"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only DRAFT or RETURNED transfer requests can be submitted.")

        transfer.status = "PENDING_APPROVAL"
        transfer.requested_at = datetime.now(UTC)
        transfer.updated_at = datetime.now(UTC)

        dest_team_res = await self.db.execute(select(Team).where(Team.id == transfer.destination_team_id))
        dest_team = dest_team_res.scalar_one_or_none()

        await self.timeline.record_event(
            event_type="TRANSFER_REQUESTED",
            title=f"Transfer to {dest_team.name if dest_team else 'New Team'} Submitted",
            description=f"Transfer request pending supervisor approval. Reason: {transfer.reason}",
            entity_type="case",
            entity_id=transfer.case_id,
            case_id=transfer.case_id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return transfer

    async def approve_transfer(
        self,
        transfer_id: uuid.UUID,
        review_notes: str | None = None,
        current_user: User | None = None,
    ) -> CaseTransfer:
        """Supervisor approval: updates transfer status, routes case team atomically, and sends outbox event."""
        transfer = await self.transfer_repo.get(transfer_id)
        if not transfer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transfer request not found")

        # Idempotency check
        if transfer.status == "APPROVED":
            return transfer

        if transfer.status not in ("PENDING_APPROVAL", "SUBMITTED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve transfer in '{transfer.status}' status.",
            )

        transfer.status = "APPROVED"
        transfer.reviewed_by = current_user.id if current_user else None
        transfer.reviewed_at = datetime.now(UTC)
        transfer.review_notes = review_notes
        transfer.updated_at = datetime.now(UTC)

        # Atomic case team routing update
        case = await self.case_repo.get(transfer.case_id)
        if case:
            case.assigned_team_id = transfer.destination_team_id
            case.updated_at = datetime.now(UTC)

        # Outbox event
        await self.outbox.enqueue(
            event_type="CASE_TRANSFER_APPROVED",
            aggregate_type="case_transfer",
            aggregate_id=transfer.id,
            payload={
                "transfer_id": str(transfer.id),
                "case_id": str(transfer.case_id),
                "destination_team_id": str(transfer.destination_team_id),
                "approved_by": str(current_user.id) if current_user else None,
            },
        )

        # Sacred Timeline
        await self.timeline.record_event(
            event_type="TRANSFER_APPROVED",
            title="Transfer Request Approved",
            description=f"Approved transfer to destination team. Notes: {review_notes or 'None'}",
            entity_type="case",
            entity_id=transfer.case_id,
            case_id=transfer.case_id,
            created_by=current_user.id if current_user else None,
        )

        await self.audit.log_event(
            event_type="CASE_TRANSFER_APPROVED",
            entity_type="case_transfer",
            entity_id=transfer.id,
            after_data={"status": "APPROVED", "destination_team_id": str(transfer.destination_team_id)},
            user_id=current_user.id if current_user else None,
        )

        await self.db.commit()
        return transfer

    async def return_transfer(
        self,
        transfer_id: uuid.UUID,
        review_notes: str,
        current_user: User | None = None,
    ) -> CaseTransfer:
        transfer = await self.transfer_repo.get(transfer_id)
        if not transfer or transfer.status != "PENDING_APPROVAL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending transfers can be returned.")

        transfer.status = "RETURNED"
        transfer.reviewed_by = current_user.id if current_user else None
        transfer.reviewed_at = datetime.now(UTC)
        transfer.review_notes = review_notes
        transfer.updated_at = datetime.now(UTC)

        await self.timeline.record_event(
            event_type="TRANSFER_RETURNED",
            title="Transfer Request Returned",
            description=f"Returned for clarification. Rationale: {review_notes}",
            entity_type="case",
            entity_id=transfer.case_id,
            case_id=transfer.case_id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return transfer

    async def deny_transfer(
        self,
        transfer_id: uuid.UUID,
        review_notes: str,
        current_user: User | None = None,
    ) -> CaseTransfer:
        transfer = await self.transfer_repo.get(transfer_id)
        if not transfer or transfer.status != "PENDING_APPROVAL":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending transfers can be denied.")

        transfer.status = "DENIED"
        transfer.reviewed_by = current_user.id if current_user else None
        transfer.reviewed_at = datetime.now(UTC)
        transfer.review_notes = review_notes
        transfer.updated_at = datetime.now(UTC)

        await self.timeline.record_event(
            event_type="TRANSFER_DENIED",
            title="Transfer Request Denied",
            description=f"Transfer denied by supervisor. Rationale: {review_notes}",
            entity_type="case",
            entity_id=transfer.case_id,
            case_id=transfer.case_id,
            created_by=current_user.id if current_user else None,
        )

        await self.db.commit()
        return transfer
