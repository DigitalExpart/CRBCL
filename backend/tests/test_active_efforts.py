"""Tests for Active Efforts tracking under Indigenous customary care standards."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_active_efforts_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Sarah", "last_name": "Musqua", "date_of_birth": "2018-04-10", "gender": "Female"},
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Musqua Family Wellness Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Record an active effort
    effort_payload = {
        "effort_type": "HOUSING_ASSISTANCE",
        "description": "Assisted family with emergency housing repairs and furnace inspection.",
        "service_category": "Housing & Basic Needs",
        "provider_name": "Cote Housing Authority",
        "service_date": "2026-08-15",
        "outcome": "ONGOING",
        "barriers_encountered": "Supply chain delays for heating components.",
        "remedial_action": "Provided temporary space heaters and daily check-ins.",
    }
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/active-efforts",
        headers=headers,
        json=effort_payload,
    )
    assert create_res.status_code == 201
    effort = create_res.json()
    effort_id = effort["id"]
    assert effort["effort_type"] == "HOUSING_ASSISTANCE"
    assert effort["outcome"] == "ONGOING"
    assert effort["case_id"] == case_id

    # 3. Retrieve single active effort
    get_res = await client.get(f"/api/v1/active-efforts/{effort_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == effort_id

    # 4. Update active effort outcome
    update_res = await client.patch(
        f"/api/v1/active-efforts/{effort_id}",
        headers=headers,
        json={"outcome": "SUCCESSFUL", "remedial_action": "Repairs completed. Inspection passed."},
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["outcome"] == "SUCCESSFUL"
    assert updated["version"] == 2

    # 5. List active efforts for the case
    list_res = await client.get(
        f"/api/v1/cases/{case_id}/active-efforts?outcome=SUCCESSFUL",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(i["id"] == effort_id for i in list_data["items"])
