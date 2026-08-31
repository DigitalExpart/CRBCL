"""Case note 4-way transactional integrity test suite."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.outbox import OutboxEvent
from app.models.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_case_note_atomic_creation(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    """
    Test 4-way single-transaction commit:
    1. Case note created
    2. Audit event generated
    3. Timeline event generated
    4. Outbox event generated
    """
    # 1. Create a parent case first
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Test Case for Note", "case_type": "Child Safety", "status": "Open"},
        headers=caseworker_user["headers"],
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Post a case note
    note_payload = {
        "subject": "Home Visit & Cultural Teaching",
        "content": "Met with family and Elder. Discussed seasonal harvesting teachings and reviewed wellness plan.",
        "note_type": "Progress Note",
        "is_confidential": False,
    }
    note_res = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json=note_payload,
        headers=caseworker_user["headers"],
    )
    assert note_res.status_code == 201
    note_data = note_res.json()
    note_id = uuid.UUID(note_data["id"])

    # 3. Verify Note, Audit, Timeline, and Outbox were all committed
    audit_res = await db_session.execute(
        select(AuditEvent).where(AuditEvent.entity_id == note_id, AuditEvent.event_type == "CASE_NOTE_CREATED")
    )
    assert audit_res.scalar_one_or_none() is not None

    timeline_res = await db_session.execute(
        select(TimelineEvent).where(TimelineEvent.entity_id == note_id, TimelineEvent.event_type == "CASE_NOTE_ADDED")
    )
    assert timeline_res.scalar_one_or_none() is not None

    outbox_res = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == note_id)
    )
    assert outbox_res.scalar_one_or_none() is not None

    # 4. List notes for case
    list_res = await client.get(f"/api/v1/cases/{case_id}/notes", headers=caseworker_user["headers"])
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) == 1
    assert list_res.json()["items"][0]["subject"] == "Home Visit & Cultural Teaching"
