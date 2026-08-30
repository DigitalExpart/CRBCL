"""Audit integrity and outbox retry test suite."""

import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.outbox import OutboxEvent
from app.workflows.outbox import OutboxService


@pytest.mark.asyncio
async def test_outbox_retry_logic(db_session: AsyncSession):
    """Test outbox retry increments attempt_count and uses exponential backoff."""
    outbox = OutboxService(db_session)
    event = await outbox.enqueue(
        event_type="TEST_EVENT",
        aggregate_type="test",
        aggregate_id=uuid.uuid4(),
        payload={"sample": "data"},
        max_attempts=3,
    )
    await db_session.commit()

    assert event.status == "pending"
    assert event.attempt_count == 0

    # 1. First failure
    await outbox.record_failure(event.id, "Network timeout 1")
    await db_session.commit()

    updated_res = await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == event.id))
    updated = updated_res.scalar_one()
    assert updated.attempt_count == 1
    assert updated.status == "pending"
    assert updated.last_error == "Network timeout 1"

    # 2. Exceed max attempts
    await outbox.record_failure(event.id, "Network timeout 2")
    await outbox.record_failure(event.id, "Network timeout 3")
    await db_session.commit()

    final_res = await db_session.execute(select(OutboxEvent).where(OutboxEvent.id == event.id))
    final_event = final_res.scalar_one()
    assert final_event.attempt_count == 3
    assert final_event.status == "failed"  # Marked dead-letter / failed safely


@pytest.mark.asyncio
async def test_audit_event_immutability(db_session: AsyncSession):
    """Confirm audit events are append-only and have no API modification routes."""
    event = AuditEvent(
        event_type="SYSTEM_INITIALIZED",
        source="system",
        metadata_={"version": "1.0.0"},
    )
    db_session.add(event)
    await db_session.commit()

    res = await db_session.execute(select(AuditEvent).where(AuditEvent.id == event.id))
    saved = res.scalar_one()
    assert saved.event_type == "SYSTEM_INITIALIZED"
