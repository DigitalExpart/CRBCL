"""Person and Client integration test suite."""

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person


@pytest.mark.asyncio
async def test_create_client_creates_canonical_person(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    payload = {
        "first_name": "Autumn",
        "last_name": "Rain",
        "date_of_birth": "2015-05-12",
        "gender": "Female",
        "status": "Active",
        "risk_level": "Low",
        "indigenous_identity": "First Nations",
        "band_nation": "Muscowpetung Saulteaux Nation",
        "phone": "306-555-0188",
        "address": "456 Sunset Drive",
        "city": "Regina",
    }
    response = await client.post("/api/v1/clients", json=payload, headers=caseworker_user["headers"])
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Autumn"

    # Verify Person record created in persons table
    person_res = await db_session.execute(
        select(Person).where(Person.first_name == "Autumn", Person.last_name == "Rain")
    )
    person = person_res.scalar_one_or_none()
    assert person is not None
    assert person.first_name == "Autumn"
    assert person.phone == "306-555-0188"


@pytest.mark.asyncio
async def test_duplicate_check_endpoint(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    # Seed a person
    p = Person(
        first_name="Jerome",
        last_name="Cardinal",
        date_of_birth=date(1990, 1, 1),
        treaty_number="123456",
    )
    db_session.add(p)
    await db_session.commit()

    # Check duplicate with matching criteria
    check_payload = {
        "first_name": "Jerome",
        "last_name": "Cardinal",
        "treaty_number": "123456",
    }
    response = await client.post(
        "/api/v1/clients/duplicate-check", json=check_payload, headers=caseworker_user["headers"]
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["has_potential_duplicates"] is True
    assert len(res_data["candidates"]) >= 1
    assert res_data["candidates"][0]["similarity_score"] >= 0.8
