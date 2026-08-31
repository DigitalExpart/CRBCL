"""Tests for Primary Placement Episodes, Linking to Removals, and Concurrency Invariants."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_placement_episode_lifecycle_and_invariants(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client, case, and removal episode
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Marcus", "last_name": "Pelly", "date_of_birth": "2016-07-03", "gender": "Male"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Pelly Child Protection Case", "case_type": "Child Protection", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    removal_res = await client.post(
        f"/api/v1/cases/{case_id}/removals",
        headers=headers,
        json={
            "child_id": child_id,
            "removal_date": "2026-08-05",
            "removal_type": "TEMPORARY_CUSTODY",
            "authority_type": "COURT_ORDER",
            "reason_for_removal": "Parental substance emergency.",
        },
    )
    assert removal_res.status_code == 201
    removal_id = removal_res.json()["id"]

    # 2. Create primary placement episode linked to the removal
    placement_payload = {
        "child_id": child_id,
        "removal_episode_id": removal_id,
        "placement_type": "KINSHIP",
        "provider_name": "Auntie Mary Pelly Kinship Home",
        "provider_contact": "306-555-0199",
        "provider_address": "Treaty 4 Reserve Land",
        "start_date": "2026-08-05",
        "primary_caregiver_name": "Mary Pelly",
        "per_diem_rate": 45.50,
        "cultural_plan_in_place": True,
        "placement_notes": "Kinship care placement under customary agreement.",
    }
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/placements",
        headers=headers,
        json=placement_payload,
    )
    assert create_res.status_code == 201
    placement = create_res.json()
    placement_id = placement["id"]
    assert placement["status"] == "ACTIVE"
    assert placement["removal_episode_id"] == removal_id
    assert float(placement["per_diem_rate"]) == 45.50

    # 3. Test concurrent active placement prevention invariant (ADR-016)
    concurrent_res = await client.post(
        f"/api/v1/cases/{case_id}/placements",
        headers=headers,
        json={
            "child_id": child_id,
            "placement_type": "FOSTER_HOME",
            "provider_name": "Yorkton Emergency Shelter",
            "start_date": "2026-08-06",
        },
    )
    assert concurrent_res.status_code == 409
    assert "already has an active primary placement" in concurrent_res.text

    # 4. Update placement details
    update_res = await client.patch(
        f"/api/v1/placements/{placement_id}",
        headers=headers,
        json={"per_diem_rate": 50.00, "cultural_plan_in_place": True},
    )
    assert update_res.status_code == 200
    assert float(update_res.json()["per_diem_rate"]) == 50.00

    # 5. Test placement disruption workflow
    disrupt_res = await client.post(
        f"/api/v1/placements/{placement_id}/disrupt?reason=Caregiver+hospitalized",
        headers=headers,
    )
    assert disrupt_res.status_code == 200
    assert disrupt_res.json()["status"] == "DISRUPTED"
