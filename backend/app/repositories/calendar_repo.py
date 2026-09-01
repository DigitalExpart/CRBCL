"""Calendar and scheduling repository."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.calendar import CalendarEvent, CalendarRecurrenceRule


class CalendarRepo:
    """Data access layer for calendar events and recurrence rules."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        event_type: str,
        title: str,
        start_at: datetime,
        end_at: datetime,
        all_day: bool = False,
        timezone: str = "America/Regina",
        location: str | None = None,
        description: str | None = None,
        source_entity_type: str | None = None,
        source_entity_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        person_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        assigned_user_id: uuid.UUID | None = None,
        status: str = "SCHEDULED",
        created_by: uuid.UUID | None = None,
        recurrence_data: dict[str, Any] | None = None,
    ) -> CalendarEvent:
        event = CalendarEvent(
            event_type=event_type,
            title=title,
            start_at=start_at,
            end_at=end_at,
            all_day=all_day,
            timezone=timezone,
            location=location,
            description=description,
            source_entity_type=source_entity_type,
            source_entity_id=source_entity_id,
            case_id=case_id,
            person_id=person_id,
            team_id=team_id,
            assigned_user_id=assigned_user_id,
            status=status,
            created_by=created_by,
            updated_by=created_by,
        )
        self.db.add(event)
        await self.db.flush()

        if recurrence_data:
            rule = CalendarRecurrenceRule(
                calendar_event_id=event.id,
                frequency=recurrence_data.get("frequency", "WEEKLY"),
                interval=recurrence_data.get("interval", 1),
                by_weekday=recurrence_data.get("by_weekday"),
                until_date=recurrence_data.get("until_date"),
                max_occurrences=recurrence_data.get("max_occurrences"),
            )
            self.db.add(rule)
            await self.db.flush()

        return event

    async def get_by_id(self, event_id: uuid.UUID) -> CalendarEvent | None:
        stmt = (
            select(CalendarEvent)
            .options(
                selectinload(CalendarEvent.case),
                selectinload(CalendarEvent.person),
                selectinload(CalendarEvent.assigned_user),
                selectinload(CalendarEvent.recurrence_rule),
            )
            .where(CalendarEvent.id == event_id, CalendarEvent.deleted_at.is_(None))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_source(self, source_type: str, source_id: uuid.UUID) -> CalendarEvent | None:
        stmt = (
            select(CalendarEvent)
            .where(
                CalendarEvent.source_entity_type == source_type,
                CalendarEvent.source_entity_id == source_id,
                CalendarEvent.deleted_at.is_(None),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def update(self, event_id: uuid.UUID, update_data: dict[str, Any], updated_by: uuid.UUID | None = None) -> CalendarEvent | None:
        event = await self.get_by_id(event_id)
        if not event:
            return None

        for key, val in update_data.items():
            if hasattr(event, key) and val is not None and key not in ("id", "created_at", "created_by"):
                setattr(event, key, val)

        event.updated_at = datetime.now(UTC)
        if updated_by:
            event.updated_by = updated_by

        await self.db.flush()
        return event

    async def delete(self, event_id: uuid.UUID, deleted_by: uuid.UUID | None = None) -> bool:
        event = await self.get_by_id(event_id)
        if not event:
            return False

        event.deleted_at = datetime.now(UTC)
        event.deleted_by = deleted_by
        await self.db.flush()
        return True

    async def query_schedule(
        self,
        start_at: datetime,
        end_at: datetime,
        user_id: uuid.UUID | None = None,
        team_id: uuid.UUID | None = None,
        worker_ids: list[uuid.UUID] | None = None,
        case_id: uuid.UUID | None = None,
        event_types: list[str] | None = None,
    ) -> list[CalendarEvent]:
        """Query calendar events overlapping [start_at, end_at] with optional actor/team/type filters."""
        conditions = [
            CalendarEvent.deleted_at.is_(None),
            # Overlapping window: start_at < window_end AND end_at > window_start
            CalendarEvent.start_at <= end_at,
            CalendarEvent.end_at >= start_at,
        ]

        if user_id:
            conditions.append(
                or_(
                    CalendarEvent.assigned_user_id == user_id,
                    CalendarEvent.created_by == user_id,
                )
            )

        if team_id:
            conditions.append(CalendarEvent.team_id == team_id)

        if worker_ids:
            conditions.append(CalendarEvent.assigned_user_id.in_(worker_ids))

        if case_id:
            conditions.append(CalendarEvent.case_id == case_id)

        if event_types:
            conditions.append(CalendarEvent.event_type.in_(event_types))

        stmt = (
            select(CalendarEvent)
            .options(
                selectinload(CalendarEvent.case),
                selectinload(CalendarEvent.person),
                selectinload(CalendarEvent.assigned_user),
                selectinload(CalendarEvent.recurrence_rule),
            )
            .where(and_(*conditions))
            .order_by(CalendarEvent.start_at.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
