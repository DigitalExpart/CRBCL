"""Tests for Phase 6 Plan Versioning and Immutability."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_plan_versioning_and_immutability(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Jordan", "last_name": "Acoose", "date_of_birth": "2017-02-10", "gender": "Male"},
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Acoose Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Plan v1
    plan_payload = {
        "case_id": case_id,
        "primary_person_id": person_id,
        "plan_type": "SAFETY_PLAN",
        "title": "Acoose Safety Plan",
        "meeting_date": "2026-08-31T09:00:00Z",
        "narrative": "Version 1 initial agreement.",
        "goals": [{"goal_text": "Sober supervision during daytime.", "status": "IN_PROGRESS"}],
    }
    create_res = await client.post(f"/api/v1/cases/{case_id}/plans", headers=headers, json=plan_payload)
    assert create_res.status_code == 201
    plan = create_res.json()
    plan_id = plan["id"]
    assert plan["current_version"]["version_number"] == 1

    # 3. Finalize v1
    fin_res = await client.post(f"/api/v1/plans/{plan_id}/finalize", headers=headers, json={})
    assert fin_res.status_code == 200
    v1_hash = fin_res.json()["current_version"]["document_hash"]
    assert v1_hash is not None

    # 4. Create Version 2 on the running plan
    v2_res = await client.post(
        f"/api/v1/plans/{plan_id}/versions",
        headers=headers,
        json={
            "narrative": "Version 2 updated agreement with extended kinship coverage.",
            "meeting_date": "2026-09-15T10:00:00Z",
        },
    )
    assert v2_res.status_code == 201
    v2_plan = v2_res.json()
    assert len(v2_plan["versions"]) == 2
    assert v2_plan["current_version"]["version_number"] == 2
    assert v2_plan["current_version"]["status"] == "DRAFT"
    assert v2_plan["current_version"]["document_hash"] is None

    # 5. Add a new goal to v2
    goal_res = await client.post(
        f"/api/v1/plans/{plan_id}/goals",
        headers=headers,
        json={"goal_text": "Extend supervision to overnight weekend stays."},
    )
    assert goal_res.status_code == 201

    # 6. Verify v1 remains unchanged with its original single goal
    get_v1 = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    v1_data = next(v for v in get_v1.json()["versions"] if v["version_number"] == 1)
    assert v1_data["status"] == "FINALIZED"
    assert v1_data["document_hash"] == v1_hash
