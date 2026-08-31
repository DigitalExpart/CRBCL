"""Service for Polymorphic Background Checks, Screening, and Placement Eligibility Adjudication."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import BackgroundCheck
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import (
    BackgroundCheckAdjudicate,
    BackgroundCheckCreate,
    BackgroundCheckUpdate,
)
from app.workflows.outbox import OutboxService


class BackgroundCheckService:
    """Business logic for Background Checks and Placement Eligibility Screening."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlacementRepository(db)
        self.perm = PermissionService(db)
        self.audit = AuditService(db)
        self.outbox = OutboxService(db)

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    async def create_background_check(
        self, user: User, data: BackgroundCheckCreate
    ) -> BackgroundCheck:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_WRITE)

        check = BackgroundCheck(
            subject_type=data.subject_type.upper(),
            subject_id=data.subject_id,
            subject_name=data.subject_name,
            check_type=data.check_type.upper(),
            status="PENDING",
            request_date=data.request_date,
            conducted_by_agency=data.conducted_by_agency,
            clearance_reference_number=data.clearance_reference_number,
            risk_assessment_notes=data.risk_assessment_notes,
            is_eligible_for_placement=False,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_background_check(check)

        await self.audit.log(
            event_type="BACKGROUND_CHECK_REQUESTED",
            user_id=user.id,
            entity_type="background_check",
            entity_id=created.id,
            after_data={
                "subject_type": created.subject_type,
                "subject_name": created.subject_name,
                "check_type": created.check_type,
            },
        )
        await self.outbox.publish_event(
            event_type="background_check.created",
            aggregate_type="background_check",
            aggregate_id=created.id,
            payload={
                "check_id": str(created.id),
                "subject_type": created.subject_type,
                "subject_name": created.subject_name,
                "check_type": created.check_type,
            },
        )
        return created

    async def get_background_check(self, user: User, check_id: uuid.UUID) -> BackgroundCheck:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_READ)
        check = await self.repo.get_background_check_by_id(check_id)
        if not check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")
        return check

    async def list_background_checks(
        self,
        user: User,
        subject_type: str | None = None,
        subject_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        check_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[BackgroundCheck], int]:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_READ)
        return await self.repo.list_background_checks(
            subject_type=subject_type,
            subject_id=subject_id,
            status=status_filter,
            check_type=check_type,
            page=page,
            page_size=page_size,
        )

    async def update_background_check(
        self, user: User, check_id: uuid.UUID, data: BackgroundCheckUpdate
    ) -> BackgroundCheck:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_WRITE)
        check = await self.repo.get_background_check_by_id(check_id)
        if not check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")

        update_fields = data.model_dump(exclude_unset=True)
        if "subject_type" in update_fields and update_fields["subject_type"]:
            update_fields["subject_type"] = update_fields["subject_type"].upper()
        if "check_type" in update_fields and update_fields["check_type"]:
            update_fields["check_type"] = update_fields["check_type"].upper()

        for k, v in update_fields.items():
            setattr(check, k, v)
        check.updated_by = user.id
        check.version += 1

        await self.audit.log(
            event_type="BACKGROUND_CHECK_UPDATED",
            user_id=user.id,
            entity_type="background_check",
            entity_id=check.id,
            after_data=update_fields,
        )
        return check

    async def adjudicate_background_check(
        self, user: User, check_id: uuid.UUID, data: BackgroundCheckAdjudicate
    ) -> BackgroundCheck:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_ADJUDICATE)
        check = await self.repo.get_background_check_by_id(check_id)
        if not check:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")

        check.status = data.status.upper()
        check.is_eligible_for_placement = data.is_eligible_for_placement
        if data.completion_date:
            check.completion_date = data.completion_date
        if data.expiry_date:
            check.expiry_date = data.expiry_date
        if data.risk_assessment_notes:
            check.risk_assessment_notes = data.risk_assessment_notes

        check.adjudicated_by = user.id
        check.adjudicated_at = datetime.now(UTC)
        check.updated_by = user.id
        check.version += 1

        await self.audit.log(
            event_type="BACKGROUND_CHECK_ADJUDICATED",
            user_id=user.id,
            entity_type="background_check",
            entity_id=check.id,
            after_data={
                "status": check.status,
                "is_eligible_for_placement": check.is_eligible_for_placement,
                "adjudicated_by": str(user.id),
            },
        )
        await self.outbox.publish_event(
            event_type="background_check.adjudicated",
            aggregate_type="background_check",
            aggregate_id=check.id,
            payload={
                "check_id": str(check.id),
                "status": check.status,
                "is_eligible": check.is_eligible_for_placement,
            },
        )
        return check
