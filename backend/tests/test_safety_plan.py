"""Tests for Phase 6 Safety Plans: Harm Statements, Strengths, Safety Goals, Activities."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_safety_plan_full_lifecycle(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={
            "first_name": "Autumn",
            "last_name": "Sparvier",
            "date_of_birth": "2019-06-15",
            "gender": "Female",
            "band_nation": "Cowessess First Nation",
        },
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "title": "Sparvier Family Safety Case",
            "case_type": "Child Protection",
            "primary_client_id": person_id,
            "stage": "Investigation",
        },
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Safety Plan
    plan_payload = {
        "case_id": case_id,
        "primary_person_id": person_id,
        "plan_type": "SAFETY_PLAN",
        "title": "Immediate 24-Hour Kinship Safety Plan",
        "meeting_date": "2026-08-31T10:00:00Z",
        "meeting_location": "Family Residence / Lodge Wellness Room",
        "narrative": "Immediate safety plan established with maternal grandmother providing 24/7 protective supervision.",
        "participants": [
            {
                "participant_type": "WORKER",
                "name": "Sarah Caseworker",
                "role": "Primary Protection Worker",
                "attendance_status": "ATTENDED",
                "signature_required": True,
            },
            {
                "participant_type": "FAMILY_MEMBER",
                "name": "Evelyn Sparvier",
                "relationship": "Maternal Grandmother",
                "role": "Kinship Safety Supervisor",
                "attendance_status": "ATTENDED",
                "signature_required": True,
            },
        ],
        "concerns": [
            {
                "concern_type": "HARM_STATEMENT",
                "statement": "Caregiver substance use without alternative supervision left child unattended on Aug 30.",
                "severity": "Critical",
                "sort_order": 1,
            },
            {
                "concern_type": "DANGER_STATEMENT",
                "statement": "If caregiver uses substances while sole supervisor, child is at immediate risk of harm.",
                "severity": "Critical",
                "sort_order": 2,
            },
        ],
        "strengths": [
            {
                "category": "Kinship Support",
                "statement": "Grandmother Evelyn lives next door and is willing and able to provide continuous supervision.",
                "sort_order": 1,
            },
            {
                "category": "Cultural Connections",
                "statement": "Family has strong connection to Elder support circle in Cowessess.",
                "sort_order": 2,
            },
        ],
        "goals": [
            {
                "goal_text": "Ensure 24/7 sober protective adult presence at all times around child.",
                "category": "Immediate Safety",
                "target_date": "2026-09-07",
                "status": "IN_PROGRESS",
                "sort_order": 1,
                "activities": [
                    {
                        "activity_text": "Grandmother Evelyn resides in home to provide full-time supervision.",
                        "responsible_type": "FAMILY_MEMBER",
                        "responsible_name": "Evelyn Sparvier",
                        "due_date": "2026-09-07",
                        "status": "IN_PROGRESS",
                    },
                    {
                        "activity_text": "Worker conducts daily unannounced wellness drop-in.",
                        "responsible_type": "WORKER",
                        "responsible_name": "Sarah Caseworker",
                        "due_date": "2026-09-03",
                        "status": "NOT_STARTED",
                    },
                ],
            }
        ],
    }

    create_res = await client.post(f"/api/v1/cases/{case_id}/plans", headers=headers, json=plan_payload)
    assert create_res.status_code == 201, create_res.text
    plan_data = create_res.json()

    assert plan_data["plan_number"].startswith("PLN-")
    assert plan_data["plan_type"] == "SAFETY_PLAN"
    assert plan_data["status"] == "DRAFT"
    assert len(plan_data["current_version"]["concerns"]) == 2
    assert len(plan_data["current_version"]["strengths"]) == 2
    assert len(plan_data["current_version"]["goals"]) == 1
    assert len(plan_data["current_version"]["goals"][0]["activities"]) == 2

    plan_id = plan_data["id"]

    # 3. Finalize Safety Plan (Generates SHA-256 Document Hash)
    finalize_res = await client.post(
        f"/api/v1/plans/{plan_id}/finalize", headers=headers, json={"notes": "All parties agreed."}
    )
    assert finalize_res.status_code == 200, finalize_res.text
    finalized_data = finalize_res.json()
    assert finalized_data["status"] == "FINALIZED"
    assert finalized_data["current_version"]["document_hash"] is not None
    assert len(finalized_data["current_version"]["document_hash"]) == 64

    # 4. Attempt mutation on finalized plan -> should fail
    fail_update = await client.put(f"/api/v1/plans/{plan_id}", headers=headers, json={"title": "Altered Title"})
    assert fail_update.status_code == 400

    # 5. Verify print view
    print_res = await client.get(f"/api/v1/plans/{plan_id}/print", headers=headers)
    assert print_res.status_code == 200
    print_data = print_res.json()
    assert print_data["plan_number"] == plan_data["plan_number"]
    assert print_data["document_hash"] == finalized_data["current_version"]["document_hash"]
