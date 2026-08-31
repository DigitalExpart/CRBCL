"""Tests for Permanency Plans and Family Visitation Plans."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_permanency_and_visitation_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Kaya", "last_name": "Kitchemonia", "date_of_birth": "2019-10-18", "gender": "Female"},
    )
    assert client_res.status_code == 201
    child_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Kitchemonia Child Case", "case_type": "Child Protection", "primary_client_id": child_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Permanency Plan
    perm_payload = {
        "child_id": child_id,
        "primary_goal": "REUNIFICATION",
        "concurrent_goal": "CUSTOMARY_CARE",
        "target_date": "2027-02-01",
        "cultural_heritage_strategy": "Regular attendance at Cote First Nation language & drumming circles.",
        "sibling_co_placement_strategy": "Maintain joint placement with older brother Marcus.",
        "review_frequency_months": 6,
        "next_review_date": "2026-11-01",
        "notes": "Concurrent planning active in compliance with customary care policy.",
    }
    perm_res = await client.post(
        f"/api/v1/cases/{case_id}/permanency-plans",
        headers=headers,
        json=perm_payload,
    )
    assert perm_res.status_code == 201
    perm_plan = perm_res.json()
    perm_plan_id = perm_plan["id"]
    assert perm_plan["primary_goal"] == "REUNIFICATION"
    assert perm_plan["status"] == "DRAFT"

    # 3. Update Permanency Plan to ACTIVE
    perm_update_res = await client.patch(
        f"/api/v1/permanency-plans/{perm_plan_id}",
        headers=headers,
        json={"status": "ACTIVE"},
    )
    assert perm_update_res.status_code == 200
    assert perm_update_res.json()["status"] == "ACTIVE"

    # 4. Create Visitation Plan
    visit_payload = {
        "child_id": child_id,
        "participant_names": ["Mother (Rachel)", "Grandmother (Agnes)"],
        "frequency": "WEEKLY",
        "duration_hours": 2.0,
        "supervision_required": True,
        "supervisor_type": "FAMILY_SUPPORT_WORKER",
        "location": "CRBCL Family Wellness Healing Center",
        "conditions": "Sober presentation required; drug screening protocol active.",
        "effective_from": "2026-08-01",
        "effective_to": "2026-12-31",
        "notes": "Supervised bonding and traditional craft making.",
    }
    visit_res = await client.post(
        f"/api/v1/cases/{case_id}/visitation-plans",
        headers=headers,
        json=visit_payload,
    )
    assert visit_res.status_code == 201
    visit_plan = visit_res.json()
    visit_plan_id = visit_plan["id"]
    assert visit_plan["frequency"] == "WEEKLY"
    assert visit_plan["status"] == "ACTIVE"
    assert float(visit_plan["duration_hours"]) == 2.0

    # 5. List plans
    perm_list = await client.get(f"/api/v1/cases/{case_id}/permanency-plans", headers=headers)
    assert perm_list.status_code == 200
    assert perm_list.json()["total"] >= 1

    visit_list = await client.get(f"/api/v1/cases/{case_id}/visitation-plans", headers=headers)
    assert visit_list.status_code == 200
    assert visit_list.json()["total"] >= 1
