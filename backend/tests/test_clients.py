"""Client CRUD and audit integration test suite."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AccessEvent, AuditEvent
from app.models.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_create_and_get_client(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    # 1. Create client
    create_payload = {
        "first_name": "Jordan",
        "last_name": "Bear",
        "status": "Active",
        "risk_level": "Low",
        "email": "jordan.bear@example.ca",
        "phone": "306-555-0199",
        "province": "Saskatchewan",
        "indigenous_identity": "First Nations",
        "band_nation": "Muscowpetung Saulteaux Nation",
    }
    create_res = await client.post("/api/v1/clients", json=create_payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    created_data = create_res.json()
    client_id = uuid.UUID(created_data["id"])
    assert created_data["first_name"] == "Jordan"
    assert created_data["last_name"] == "Bear"

    # Verify Audit Event generated
    audit_res = await db_session.execute(
        select(AuditEvent).where(AuditEvent.entity_id == client_id, AuditEvent.event_type == "CLIENT_CREATED")
    )
    assert audit_res.scalar_one_or_none() is not None

    # Verify Sacred Timeline Event generated
    timeline_res = await db_session.execute(select(TimelineEvent).where(TimelineEvent.client_id == client_id))
    assert timeline_res.scalar_one_or_none() is not None

    # 2. Get client (profile view)
    get_res = await client.get(f"/api/v1/clients/{client_id}", headers=caseworker_user["headers"])
    assert get_res.status_code == 200
    assert get_res.json()["email"] == "jordan.bear@example.ca"

    # Verify Access Event logged on sensitive profile read
    access_res = await db_session.execute(
        select(AccessEvent).where(AccessEvent.entity_id == client_id, AccessEvent.event_type == "CLIENT_PROFILE_VIEWED")
    )
    assert access_res.scalar_one_or_none() is not None

    # 3. Update client
    update_payload = {"risk_level": "Medium", "city": "Regina"}
    patch_res = await client.patch(
        f"/api/v1/clients/{client_id}", json=update_payload, headers=caseworker_user["headers"]
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["risk_level"] == "Medium"
    assert patch_res.json()["city"] == "Regina"
