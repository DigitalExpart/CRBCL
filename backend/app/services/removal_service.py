"""Service for Removal Episodes (Legal authorities, physical removal events, inventory)."""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import RemovalEpisode
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import RemovalEpisodeCreate, RemovalEpisodeUpdate
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class RemovalService:
    """Business logic for Child Removal Episodes."""

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

    async def create_removal_episode(
        self, user: User, case_id: uuid.UUID, data: RemovalEpisodeCreate
    ) -> RemovalEpisode:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.REMOVAL_WRITE)

        removal = RemovalEpisode(
            case_id=case_id,
            child_id=data.child_id,
            removal_date=data.removal_date,
            removal_time=data.removal_time,
            removal_type=data.removal_type.upper(),
            authority_type=data.authority_type.upper(),
            legal_authority_reference=data.legal_authority_reference,
            reason_for_removal=data.reason_for_removal,
            immediate_safety_threat=data.immediate_safety_threat,
            removal_location=data.removal_location,
            accompanying_officers=data.accompanying_officers,
            child_condition_at_removal=data.child_condition_at_removal,
            belongings_inventoried=data.belongings_inventoried,
            status="COMPLETED",
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_removal_episode(removal)

        await self.audit.log(
            event_type="REMOVAL_EPISODE_CREATED",
            user_id=user.id,
            entity_type="removal_episode",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "removal_type": created.removal_type,
                "authority_type": created.authority_type,
                "removal_date": str(created.removal_date),
            },
        )
        await self.timeline.record_event(
            event_type="REMOVAL_EXECUTED",
            title=f"Child Removal Executed ({created.removal_type})",
            description=f"Child placed into care under {created.authority_type} ({created.legal_authority_reference or 'N/A'}). Reason: {created.reason_for_removal}",
            entity_type="removal_episode",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="removal.created",
            aggregate_type="removal_episode",
            aggregate_id=created.id,
            payload={
                "removal_id": str(created.id),
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "removal_type": created.removal_type,
            },
        )
        return created

    async def get_removal_episode(self, user: User, removal_id: uuid.UUID) -> RemovalEpisode:
        removal = await self.repo.get_removal_episode_by_id(removal_id)
        if not removal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Removal episode not found.")
        await self._require_case_access(user.id, removal.case_id)
        await self._require_perm(user.id, Permissions.REMOVAL_READ)
        return removal

    async def list_removal_episodes_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[RemovalEpisode], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.REMOVAL_READ)
        return await self.repo.list_removal_episodes_by_case(case_id, page=page, page_size=page_size)

    async def update_removal_episode(
        self, user: User, removal_id: uuid.UUID, data: RemovalEpisodeUpdate
    ) -> RemovalEpisode:
        removal = await self.repo.get_removal_episode_by_id(removal_id)
        if not removal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Removal episode not found.")
        await self._require_case_access(user.id, removal.case_id)
        await self._require_perm(user.id, Permissions.REMOVAL_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("removal_type"):
            update_fields["removal_type"] = update_fields["removal_type"].upper()
        if update_fields.get("authority_type"):
            update_fields["authority_type"] = update_fields["authority_type"].upper()
        if update_fields.get("status"):
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(removal, k, v)
        removal.updated_by = user.id
        removal.version += 1

        await self.audit.log(
            event_type="REMOVAL_EPISODE_UPDATED",
            user_id=user.id,
            entity_type="removal_episode",
            entity_id=removal.id,
            after_data=update_fields,
        )
        return removal
