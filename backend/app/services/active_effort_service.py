"""Service for Active Efforts tracking, outcomes, barriers, and remedial action."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import ActiveEffort
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import ActiveEffortCreate, ActiveEffortUpdate
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class ActiveEffortService:
    """Business logic for Active Efforts documentation under Indigenous customary care standards."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlacementRepository(db)
        self.perm = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def _require_case_access(self, user_id: uuid.UUID, case_id: uuid.UUID) -> None:
        if await self.perm.is_user_restricted_from_case(user_id, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    async def create_active_effort(
        self, user: User, case_id: uuid.UUID, data: ActiveEffortCreate
    ) -> ActiveEffort:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.ACTIVE_EFFORTS_WRITE)

        effort = ActiveEffort(
            case_id=case_id,
            effort_type=data.effort_type.upper(),
            description=data.description,
            service_category=data.service_category,
            provider_name=data.provider_name,
            service_date=data.service_date,
            outcome=data.outcome.upper(),
            barriers_encountered=data.barriers_encountered,
            remedial_action=data.remedial_action,
            worker_id=data.worker_id or user.id,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_active_effort(effort)

        await self.audit.log(
            event_type="ACTIVE_EFFORT_LOGGED",
            user_id=user.id,
            entity_type="active_effort",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "effort_type": created.effort_type,
                "outcome": created.outcome,
                "service_date": str(created.service_date),
            },
        )
        await self.timeline.record_event(
            event_type="ACTIVE_EFFORT_RECORDED",
            title=f"Active Effort: {created.effort_type}",
            description=f"Active effort delivered on {created.service_date}. Outcome: {created.outcome}.",
            entity_type="active_effort",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="active_effort.created",
            aggregate_type="active_effort",
            aggregate_id=created.id,
            payload={
                "effort_id": str(created.id),
                "case_id": str(case_id),
                "effort_type": created.effort_type,
                "outcome": created.outcome,
            },
        )
        return created

    async def get_active_effort(self, user: User, effort_id: uuid.UUID) -> ActiveEffort:
        effort = await self.repo.get_active_effort_by_id(effort_id)
        if not effort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active effort record not found.")
        await self._require_case_access(user.id, effort.case_id)
        await self._require_perm(user.id, Permissions.ACTIVE_EFFORTS_READ)
        return effort

    async def list_active_efforts_by_case(
        self,
        user: User,
        case_id: uuid.UUID,
        outcome: str | None = None,
        effort_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ActiveEffort], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.ACTIVE_EFFORTS_READ)
        return await self.repo.list_active_efforts_by_case(
            case_id, outcome=outcome, effort_type=effort_type, page=page, page_size=page_size
        )

    async def update_active_effort(
        self, user: User, effort_id: uuid.UUID, data: ActiveEffortUpdate
    ) -> ActiveEffort:
        effort = await self.repo.get_active_effort_by_id(effort_id)
        if not effort:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active effort record not found.")
        await self._require_case_access(user.id, effort.case_id)
        await self._require_perm(user.id, Permissions.ACTIVE_EFFORTS_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if "effort_type" in update_fields and update_fields["effort_type"]:
            update_fields["effort_type"] = update_fields["effort_type"].upper()
        if "outcome" in update_fields and update_fields["outcome"]:
            update_fields["outcome"] = update_fields["outcome"].upper()

        for k, v in update_fields.items():
            setattr(effort, k, v)
        effort.updated_by = user.id
        effort.version += 1

        await self.audit.log(
            event_type="ACTIVE_EFFORT_UPDATED",
            user_id=user.id,
            entity_type="active_effort",
            entity_id=effort.id,
            after_data=update_fields,
        )
        return effort
