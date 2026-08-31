"""Medical profiles, allergies, conditions, and medication test suite."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_medical_allergies_and_medications_flow(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    # 1. Create client first
    client_res = await client.post(
        "/api/v1/clients",
        json={"first_name": "Tyler", "last_name": "Starblanket", "status": "Active"},
        headers=caseworker_user["headers"],
    )
    assert client_res.status_code == 201
    client_id = client_res.json()["id"]

    # 2. Add allergy
    allergy_res = await client.post(
        f"/api/v1/clients/{client_id}/allergies",
        json={"allergen": "Amoxicillin", "reaction": "Hives and swelling", "severity": "Severe"},
        headers=caseworker_user["headers"],
    )
    assert allergy_res.status_code == 201
    assert allergy_res.json()["allergen"] == "Amoxicillin"

    # 3. Add medication
    med_res = await client.post(
        f"/api/v1/clients/{client_id}/medications",
        json={
            "medication_name": "Ventolin Inhaler",
            "dosage": "100mcg",
            "frequency": "As needed",
            "route": "Inhalation",
            "prescriber_name": "Dr. Smith",
        },
        headers=caseworker_user["headers"],
    )
    assert med_res.status_code == 201
    assert med_res.json()["medication_name"] == "Ventolin Inhaler"

    # Verify Timeline event created for medication start
    timeline_res = await db_session.execute(
        select(TimelineEvent).where(
            TimelineEvent.client_id == uuid.UUID(client_id),
            TimelineEvent.event_type == "MEDICATION_STARTED",
        )
    )
    assert timeline_res.scalar_one_or_none() is not None

    # 4. Get full medical profile
    med_full = await client.get(f"/api/v1/clients/{client_id}/medical", headers=caseworker_user["headers"])
    assert med_full.status_code == 200
    data = med_full.json()
    assert len(data["allergies"]) == 1
    assert len(data["medications"]) == 1
