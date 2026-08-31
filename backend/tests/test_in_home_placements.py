"""Tests for In-Home Family Preservation Placements & Safety Monitoring."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_in_home_placement_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client, primary person, and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Jordan", "last_name": "Severight", "date_of_birth": "2020-09-14", "gender": "Male"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Severight Family In-Home Support", "case_type": "Family Support", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create in-home placement
    in_home_payload = {
        "child_id": child_id,
        "caregiver_relationship": "Biological Mother",
        "start_date": "2026-08-01",
        "supervision_level": "INTENSIVE",
        "safety_monitoring_frequency": "BIWEEKLY",
        "support_services_provided": ["Addictions Support", "Elder Mentorship", "Food Security Box"],
        "notes": "Intensive safety monitoring following substantiated neglect referral.",
    }
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/in-home-placements",
        headers=headers,
        json=in_home_payload,
    )
    assert create_res.status_code == 201
    placement = create_res.json()
    placement_id = placement["id"]
    assert placement["status"] == "ACTIVE"
    assert placement["supervision_level"] == "INTENSIVE"

    # 3. Test concurrent active in-home placement prevention (Invariant)
    duplicate_res = await client.post(
        f"/api/v1/cases/{case_id}/in-home-placements",
        headers=headers,
        json=in_home_payload,
    )
    assert duplicate_res.status_code == 409

    # 4. Update in-home placement
    update_res = await client.patch(
        f"/api/v1/in-home-placements/{placement_id}",
        headers=headers,
        json={"supervision_level": "STANDARD", "safety_monitoring_frequency": "MONTHLY"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["supervision_level"] == "STANDARD"

    # 5. Conclude / end in-home placement successfully
    end_payload = {
        "end_date": "2026-08-30",
        "status": "ENDED",
        "closure_reason": "Family achieved protective capacity goals under Case Plan PLN-202608-0001.",
    }
    end_res = await client.post(
        f"/api/v1/in-home-placements/{placement_id}/end",
        headers=headers,
        json=end_payload,
    )
    assert end_res.status_code == 200
    ended = end_res.json()
    assert ended["status"] == "ENDED"
    assert ended["end_date"] == "2026-08-30"
