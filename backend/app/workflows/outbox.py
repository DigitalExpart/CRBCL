"""Transactional outbox service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent


class OutboxService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def enqueue(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        payload: dict,
        max_attempts: int = 5,
    ) -> OutboxEvent:
        """Enqueue an outbox event within the caller's active database transaction."""
        event = OutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            payload=payload,
            status="pending",
            attempt_count=0,
            max_attempts=max_attempts,
            available_at=datetime.now(UTC),
        )
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_pending_events(self, limit: int = 10) -> list[OutboxEvent]:
        """Fetch pending outbox events that are available for processing."""
        now = datetime.now(UTC)
        query = (
            select(OutboxEvent)
            .where(
                OutboxEvent.status == "pending",
                OutboxEvent.available_at <= now,
            )
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_processed(self, event_id: uuid.UUID) -> None:
        """Mark an outbox event as successfully processed."""
        result = await self.db.execute(select(OutboxEvent).where(OutboxEvent.id == event_id))
        event = result.scalar_one_or_none()
        if event:
            event.status = "processed"
            event.processed_at = datetime.now(UTC)
            await self.db.flush()

    async def record_failure(self, event_id: uuid.UUID, error_message: str) -> None:
        """Record failure on an outbox event, scheduling retry or marking dead-letter."""
        result = await self.db.execute(select(OutboxEvent).where(OutboxEvent.id == event_id))
        event = result.scalar_one_or_none()
        if not event:
            return

        event.attempt_count += 1
        event.last_error = error_message

        if event.attempt_count >= event.max_attempts:
            event.status = "failed"
        else:
            # Exponential backoff (2^attempt seconds)
            backoff_sec = 2 ** event.attempt_count
            event.available_at = datetime.now(UTC) + timedelta(seconds=backoff_sec)
        await self.db.flush()
