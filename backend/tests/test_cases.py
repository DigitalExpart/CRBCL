"""Case management test suite."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import OutboxEvent
from app.models.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_create_and_list_cases(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    create_payload = {
        "title": "Family Support & Reconnection Plan",
        "case_type": "Family Support",
        "status": "Open",
        "priority": "High",
        "risk_level": "Medium",
        "description": "Culturally grounded wellness plan with kinship connection.",
    }
    create_res = await client.post("/api/v1/cases", json=create_payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    case_data = create_res.json()
    assert "CRB-" in case_data["case_number"]
    case_id = uuid.UUID(case_data["id"])

    # Verify Timeline event
    timeline_res = await db_session.execute(
        select(TimelineEvent).where(TimelineEvent.case_id == case_id, TimelineEvent.event_type == "CASE_OPENED")
    )
    assert timeline_res.scalar_one_or_none() is not None

    # Verify Outbox event created
    outbox_res = await db_session.execute(
        select(OutboxEvent).where(OutboxEvent.aggregate_id == case_id)
    )
    assert outbox_res.scalar_one_or_none() is not None

    # List cases
    list_res = await client.get("/api/v1/cases", headers=caseworker_user["headers"])
    assert list_res.status_code == 200
    assert len(list_res.json()["items"]) >= 1
