"""Service for Court Events, Hearings, Orders, and Band Representation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import CourtEvent
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import CourtEventCreate, CourtEventUpdate
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class CourtEventService:
    """Business logic for Child Protection Court Events & Band Representation."""

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

    async def create_court_event(
        self, user: User, case_id: uuid.UUID, data: CourtEventCreate
    ) -> CourtEvent:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.COURT_WRITE)

        event = CourtEvent(
            case_id=case_id,
            child_id=data.child_id,
            hearing_type=data.hearing_type.upper(),
            court_docket_number=data.court_docket_number,
            court_location=data.court_location,
            judge_name=data.judge_name,
            hearing_date=data.hearing_date,
            hearing_time=data.hearing_time,
            outcome_summary=data.outcome_summary,
            orders_issued=data.orders_issued,
            legal_counsel_info=data.legal_counsel_info,
            band_representative_present=data.band_representative_present,
            next_court_date=data.next_court_date,
            status=data.status.upper(),
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_court_event(event)

        await self.audit.log(
            event_type="COURT_EVENT_CREATED",
            user_id=user.id,
            entity_type="court_event",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "hearing_type": created.hearing_type,
                "hearing_date": str(created.hearing_date),
                "status": created.status,
            },
        )
        await self.timeline.record_event(
            event_type="COURT_HEARING_SCHEDULED",
            title=f"Court Hearing: {created.hearing_type}",
            description=f"Court hearing scheduled for {created.hearing_date} at {created.court_location or 'Court'}. Docket: {created.court_docket_number or 'N/A'}.",
            entity_type="court_event",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="court_event.created",
            aggregate_type="court_event",
            aggregate_id=created.id,
            payload={
                "court_event_id": str(created.id),
                "case_id": str(case_id),
                "hearing_type": created.hearing_type,
                "hearing_date": str(created.hearing_date),
            },
        )
        return created

    async def get_court_event(self, user: User, event_id: uuid.UUID) -> CourtEvent:
        event = await self.repo.get_court_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court event not found.")
        await self._require_case_access(user.id, event.case_id)
        await self._require_perm(user.id, Permissions.COURT_READ)
        return event

    async def list_court_events_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[CourtEvent], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.COURT_READ)
        return await self.repo.list_court_events_by_case(case_id, page=page, page_size=page_size)

    async def update_court_event(
        self, user: User, event_id: uuid.UUID, data: CourtEventUpdate
    ) -> CourtEvent:
        event = await self.repo.get_court_event_by_id(event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Court event not found.")
        await self._require_case_access(user.id, event.case_id)
        await self._require_perm(user.id, Permissions.COURT_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if "hearing_type" in update_fields and update_fields["hearing_type"]:
            update_fields["hearing_type"] = update_fields["hearing_type"].upper()
        if "status" in update_fields and update_fields["status"]:
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(event, k, v)
        event.updated_by = user.id
        event.version += 1

        await self.audit.log(
            event_type="COURT_EVENT_UPDATED",
            user_id=user.id,
            entity_type="court_event",
            entity_id=event.id,
            after_data=update_fields,
        )
        return event
