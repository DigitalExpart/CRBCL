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

    async def create_background_check(self, user: User, data: BackgroundCheckCreate) -> BackgroundCheck:
        await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_WRITE)

        check = BackgroundCheck(
            subject_type=data.subject_type.upper(),
            subject_id=data.subject_id,
            subject_name=data.subject_name,
            check_type=data.check_type.upper(),
            placement_home_id=data.placement_home_id,
            document_id=data.document_id,
            renewal_status=data.renewal_status or "CURRENT",
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
                "placement_home_id": str(created.placement_home_id) if created.placement_home_id else None,
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
                "placement_home_id": str(created.placement_home_id) if created.placement_home_id else None,
            },
        )
        return created

    async def get_background_check(self, user: User, check_id: uuid.UUID) -> BackgroundCheck:
        check = await self.repo.get_background_check_by_id(check_id)
        if not check or check.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")

        # Object-aware read privacy:
        if check.placement_home_id is not None:
            has_perm = (
                await self.perm.user_has_permission(user.id, Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_HOME_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_CLEARANCE_ADJUDICATE)
            )
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to access protected Resource caregiver clearance records.",
                )
        else:
            await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_READ)

        return check

    async def list_background_checks(
        self,
        user: User,
        subject_type: str | None = None,
        subject_id: uuid.UUID | None = None,
        status_filter: str | None = None,
        check_type: str | None = None,
        placement_home_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[BackgroundCheck], int]:
        if placement_home_id is not None:
            has_perm = (
                await self.perm.user_has_permission(user.id, Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_HOME_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_CLEARANCE_ADJUDICATE)
            )
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to access protected Resource caregiver clearances.",
                )
        else:
            await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_READ)

        items, total = await self.repo.list_background_checks(
            subject_type=subject_type,
            subject_id=subject_id,
            status=status_filter,
            check_type=check_type,
            placement_home_id=placement_home_id,
            page=page,
            page_size=page_size,
        )
        # Redact/filter out Resource checks if user lacks Resource clearance read authority
        if placement_home_id is None:
            has_resource_read = (
                await self.perm.user_has_permission(user.id, Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_HOME_READ)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_CLEARANCE_ADJUDICATE)
            )
            if not has_resource_read:
                items = [chk for chk in items if chk.placement_home_id is None]
        return items, total

    async def update_background_check(
        self, user: User, check_id: uuid.UUID, data: BackgroundCheckUpdate
    ) -> BackgroundCheck:
        check = await self.repo.get_background_check_by_id(check_id)
        if not check or check.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")

        if check.placement_home_id is not None:
            has_perm = (
                await self.perm.user_has_permission(user.id, Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_MANAGE)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_HOME_WRITE)
                or await self.perm.user_has_permission(user.id, Permissions.RESOURCE_CLEARANCE_ADJUDICATE)
            )
            if not has_perm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User does not have permission to manage protected Resource caregiver clearances.",
                )
        else:
            await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("subject_type"):
            update_fields["subject_type"] = update_fields["subject_type"].upper()
        if update_fields.get("check_type"):
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
        check = await self.repo.get_background_check_by_id(check_id)
        if not check or check.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Background check record not found.")

        # Object-aware authorization:
        # If the BackgroundCheck is Resource-related, require Resource clearance adjudication capability.
        # Otherwise preserve existing background_check.adjudicate behavior for established child-welfare checks.
        if check.placement_home_id is not None:
            await self._require_perm(user.id, Permissions.RESOURCE_CLEARANCE_ADJUDICATE)
        else:
            await self._require_perm(user.id, Permissions.BACKGROUND_CHECK_ADJUDICATE)

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
