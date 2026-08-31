"""Sacred Timeline event service — business history."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeline import TimelineEvent


class TimelineEventType(StrEnum):
    CLIENT_CREATED = "CLIENT_CREATED"
    CLIENT_UPDATED = "CLIENT_UPDATED"
    FAMILY_CREATED = "FAMILY_CREATED"
    FAMILY_UPDATED = "FAMILY_UPDATED"
    CASE_OPENED = "CASE_OPENED"
    CASE_UPDATED = "CASE_UPDATED"
    CASE_NOTE_ADDED = "CASE_NOTE_ADDED"
    CASE_CLOSED = "CASE_CLOSED"
    CASE_REOPENED = "CASE_REOPENED"


class TimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_event(
        self,
        event_type: str,
        title: str,
        description: str = "",
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        client_id: uuid.UUID | None = None,
        family_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        occurred_at: datetime | None = None,
        created_by: uuid.UUID | None = None,
        metadata: dict | None = None,
    ) -> TimelineEvent:
        """Create a new append-oriented Sacred Timeline business history event."""
        if occurred_at is None:
            occurred_at = datetime.now(UTC)

        event = TimelineEvent(
            event_type=event_type,
            title=title,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            client_id=client_id,
            family_id=family_id,
            case_id=case_id,
            occurred_at=occurred_at,
            created_by=created_by,
            metadata_=metadata,
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_timeline_for_entity(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        limit: int = 50,
    ) -> list[TimelineEvent]:
        """Fetch timeline events for a given entity ordered by occurred_at descending."""
        query = (
            select(TimelineEvent)
            .where(
                TimelineEvent.entity_type == entity_type,
                TimelineEvent.entity_id == entity_id,
            )
            .order_by(TimelineEvent.occurred_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_timeline_for_case(
        self,
        case_id: uuid.UUID,
        limit: int = 50,
    ) -> list[TimelineEvent]:
        """Fetch timeline events for a case."""
        query = (
            select(TimelineEvent)
            .where(TimelineEvent.case_id == case_id)
            .order_by(TimelineEvent.occurred_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
