"""Tests for Phase 6 Plan Cloning: Stripping Signatures, Locks, and Creating New Draft."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_plan_cloning_behavior(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "Tessa", "last_name": "Lavallee", "date_of_birth": "2018-11-04", "gender": "Female"},
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Lavallee Family Support", "case_type": "Family Support", "primary_client_id": person_id},
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Plan with goals, finalize, sign, and lock
    plan_payload = {
        "case_id": case_id,
        "primary_person_id": person_id,
        "plan_type": "CASE_PLAN",
        "title": "Lavallee Initial Case Plan",
        "narrative": "Original session narrative.",
        "participants": [{"participant_type": "WORKER", "name": "Worker Jane", "signature_required": True}],
        "concerns": [{"concern_type": "SAFETY_CONCERN", "statement": "Concern 1", "severity": "Medium"}],
        "strengths": [{"category": "Kinship", "statement": "Extended family support"}],
        "goals": [{"goal_text": "Complete parenting classes", "status": "IN_PROGRESS"}],
    }
    create_res = await client.post(f"/api/v1/cases/{case_id}/plans", headers=headers, json=plan_payload)
    assert create_res.status_code == 201
    orig_plan = create_res.json()
    orig_plan_id = orig_plan["id"]

    # Finalize and sign
    await client.post(f"/api/v1/plans/{orig_plan_id}/finalize", headers=headers, json={})
    await client.post(
        f"/api/v1/plans/{orig_plan_id}/signatures",
        headers=headers,
        json={
            "signer_type": "WORKER",
            "signer_name": "Worker Jane",
            "signer_role": "Caseworker",
            "signature_data": "data:image/svg+xml;base64,mock",
            "method": "ELECTRONIC_DRAW",
        },
    )
    # Lock
    await client.post(f"/api/v1/plans/{orig_plan_id}/lock", headers=headers, json={"reason": "Signed and locked."})

    # 3. Clone Plan
    clone_res = await client.post(
        f"/api/v1/plans/{orig_plan_id}/clone",
        headers=headers,
        json={"new_title": "Lavallee 2027 Annual Case Plan Review", "include_completed_goals": False},
    )
    assert clone_res.status_code == 201
    cloned_plan = clone_res.json()

    # 4. Verify Cloned Plan Invariants
    assert cloned_plan["id"] != orig_plan_id
    assert cloned_plan["plan_number"] != orig_plan["plan_number"]
    assert cloned_plan["title"] == "Lavallee 2027 Annual Case Plan Review"
    assert cloned_plan["status"] == "DRAFT"

    cloned_curr_v = cloned_plan["current_version"]
    assert cloned_curr_v["status"] == "DRAFT"
    assert cloned_curr_v["version_number"] == 1
    assert cloned_curr_v["document_hash"] is None
    assert cloned_curr_v["finalized_at"] is None
    assert cloned_curr_v["locked_at"] is None

    # Signatures must be stripped
    assert len(cloned_curr_v["signatures"]) == 0

    # Concerns, strengths, and goals must be copied
    assert len(cloned_curr_v["concerns"]) == 1
    assert len(cloned_curr_v["strengths"]) == 1
    assert len(cloned_curr_v["goals"]) == 1
    assert cloned_curr_v["goals"][0]["goal_text"] == "Complete parenting classes"
