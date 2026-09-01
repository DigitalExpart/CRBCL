"""Tests for Child Removal Episodes (Legal authorities, physical custody events)."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_removal_episode_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Liam", "last_name": "Brass", "date_of_birth": "2017-11-22", "gender": "Male"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Brass Child Protection Case", "case_type": "Child Protection", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Record child removal episode
    removal_payload = {
        "child_id": child_id,
        "removal_date": "2026-08-12",
        "removal_time": "14:30:00",
        "removal_type": "EMERGENCY_ORDER",
        "authority_type": "CHILD_WELFARE_WARRANT",
        "legal_authority_reference": "WARRANT-YORKTON-2026-092",
        "reason_for_removal": "Severe acute domestic violence incident with caregiver intoxication.",
        "immediate_safety_threat": "Direct physical risk to child; primary caregiver incapacitated.",
        "removal_location": "104 Cote Reserve Main Road",
        "accompanying_officers": "Cst. Smith & Cst. McKay (RCMP)",
        "child_condition_at_removal": "Upset but physically unharmed. Wearing winter clothing.",
        "belongings_inventoried": True,
    }
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/removals",
        headers=headers,
        json=removal_payload,
    )
    assert create_res.status_code == 201
    removal = create_res.json()
    removal_id = removal["id"]
    assert removal["status"] == "COMPLETED"
    assert removal["authority_type"] == "CHILD_WELFARE_WARRANT"

    # 3. Retrieve removal details
    get_res = await client.get(f"/api/v1/removals/{removal_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["legal_authority_reference"] == "WARRANT-YORKTON-2026-092"

    # 4. Update removal documentation
    update_res = await client.patch(
        f"/api/v1/removals/{removal_id}",
        headers=headers,
        json={"child_condition_at_removal": "Settled after receiving comfort toy and warm meal."},
    )
    assert update_res.status_code == 200
    assert "Settled" in update_res.json()["child_condition_at_removal"]

    # 5. List removals for the case
    list_res = await client.get(f"/api/v1/cases/{case_id}/removals", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert any(r["id"] == removal_id for r in data["items"])
