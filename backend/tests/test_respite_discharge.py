"""Tests for Respite Stays, Discharge Episodes, and Child History Aggregation."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_respite_and_discharge_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client, case, and placement
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Autumn", "last_name": "Whitehawk", "date_of_birth": "2015-03-25", "gender": "Female"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Whitehawk Case", "case_type": "Child Protection", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    placement_res = await client.post(
        f"/api/v1/cases/{case_id}/placements",
        headers=headers,
        json={
            "child_id": child_id,
            "placement_type": "CUSTOMARY_CARE",
            "provider_name": "Whitehawk Customary Lodge",
            "start_date": "2026-08-01",
        },
    )
    assert placement_res.status_code == 201
    placement_id = placement_res.json()["id"]

    # 2. Schedule Respite Stay within the placement
    respite_payload = {
        "respite_provider_name": "Camp Sundance Cultural Retreat",
        "respite_type": "PLANNED",
        "start_date": "2026-08-15",
        "end_date": "2026-08-18",
        "reason": "Weekend cultural land-based camp and caregiver relief.",
        "status": "SCHEDULED",
        "notes": "Cultural coordinator escorting child.",
    }
    respite_res = await client.post(
        f"/api/v1/placements/{placement_id}/respite",
        headers=headers,
        json=respite_payload,
    )
    assert respite_res.status_code == 201
    respite = respite_res.json()
    respite_id = respite["id"]
    assert respite["respite_provider_name"] == "Camp Sundance Cultural Retreat"

    # 3. Verify placement is still ACTIVE (Respite does NOT terminate placement)
    placement_check = await client.get(f"/api/v1/placements/{placement_id}", headers=headers)
    assert placement_check.json()["status"] == "ACTIVE"

    # 4. List respite episodes for the placement
    respite_list = await client.get(f"/api/v1/placements/{placement_id}/respite", headers=headers)
    assert respite_list.status_code == 200
    assert respite_list.json()["total"] >= 1

    # 5. Discharge the Placement (Atomically transitions placement to COMPLETED)
    discharge_payload = {
        "discharge_date": "2026-08-31",
        "discharge_type": "REUNIFICATION",
        "destination_name": "Biological Parents (Home)",
        "destination_relationship": "Parents",
        "post_discharge_supervision_plan": "Biweekly home visits by family support worker for 6 months.",
        "discharge_readiness_assessed": True,
        "notes": "Reunification plan successfully completed.",
    }
    discharge_res = await client.post(
        f"/api/v1/placements/{placement_id}/discharge",
        headers=headers,
        json=discharge_payload,
    )
    assert discharge_res.status_code == 201
    discharge = discharge_res.json()
    assert discharge["discharge_type"] == "REUNIFICATION"
    assert discharge["approved_by"] is not None
    assert discharge["approved_at"] is not None

    # 6. Verify placement status transitioned to COMPLETED and end_date is populated
    placement_final = await client.get(f"/api/v1/placements/{placement_id}", headers=headers)
    assert placement_final.json()["status"] == "COMPLETED"
    assert placement_final.json()["end_date"] == "2026-08-31"

    # 7. Test Child Longitudinal Episodes API
    child_episodes_res = await client.get(f"/api/v1/children/{child_id}/episodes", headers=headers)
    assert child_episodes_res.status_code == 200
    episodes_data = child_episodes_res.json()
    assert episodes_data["child_id"] == child_id
    assert len(episodes_data["placement_episodes"]) >= 1
