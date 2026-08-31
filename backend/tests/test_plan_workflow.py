"""Tests for Phase 6 Plan Workflow: Review, Approve, Return, and Director Lock/Unlock."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_plan_workflow_and_director_governance(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Rory", "last_name": "Bellegarde", "date_of_birth": "2018-09-19", "gender": "Male"},
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Bellegarde Case", "case_type": "Child Protection", "primary_client_id": person_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Plan
    create_res = await client.post(
        f"/api/v1/cases/{case_id}/plans",
        headers=headers,
        json={"case_id": case_id, "plan_type": "CASE_PLAN", "title": "Bellegarde Wellness Agreement"},
    )
    assert create_res.status_code == 201
    plan_id = create_res.json()["id"]

    # 3. Submit Plan for review -> IN_REVIEW
    sub_res = await client.post(
        f"/api/v1/plans/{plan_id}/submit",
        headers=headers,
        json={"comments": "Ready for supervisor sign-off."},
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["status"] == "IN_REVIEW"

    # 4. Supervisor returns plan with revision notes -> DRAFT
    ret_res = await client.post(
        f"/api/v1/plans/{plan_id}/return",
        headers=headers,
        json={"reasons": "Please add cultural mentorship activity under Goal 1."},
    )
    assert ret_res.status_code == 200
    assert ret_res.json()["status"] == "DRAFT"

    # 5. Resubmit plan -> IN_REVIEW
    await client.post(f"/api/v1/plans/{plan_id}/submit", headers=headers, json={})

    # 6. Supervisor approves plan -> FINALIZED + hash computed
    app_res = await client.post(
        f"/api/v1/plans/{plan_id}/approve",
        headers=headers,
        json={"comments": "Clinical safety goals verified."},
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == "FINALIZED"
    assert app_res.json()["current_version"]["document_hash"] is not None

    # 7. Lock plan -> LOCKED
    lock_res = await client.post(
        f"/api/v1/plans/{plan_id}/lock",
        headers=headers,
        json={"reason": "All community and worker signatures gathered."},
    )
    assert lock_res.status_code == 200
    assert lock_res.json()["status"] == "LOCKED"

    # 8. Director unlock with mandatory justification
    unlock_res = await client.post(
        f"/api/v1/plans/{plan_id}/unlock",
        headers=headers,
        json={"justification": "Director override authorized to update provider schedule."},
    )
    assert unlock_res.status_code == 200
    assert unlock_res.json()["status"] == "FINALIZED"
