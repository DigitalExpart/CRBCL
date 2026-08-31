"""Tests for Phase 6 Case Plans: Goals, Multi-Party Activities, Responsibilities, Metrics."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_plan_and_activities_flow(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create client and case
    client_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={
            "first_name": "Marcus",
            "last_name": "Kakakaway",
            "date_of_birth": "2015-08-20",
            "gender": "Male",
        },
    )
    assert client_res.status_code == 201
    person_id = client_res.json()["id"]

    case_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={
            "title": "Kakakaway Family Wellness Roadmap",
            "case_type": "Family Support",
            "primary_client_id": person_id,
        },
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Create Case Plan
    plan_payload = {
        "case_id": case_id,
        "primary_person_id": person_id,
        "plan_type": "CASE_PLAN",
        "title": "Comprehensive 6-Month Family Wellness Plan",
        "meeting_date": "2026-08-31T14:00:00Z",
        "narrative": "Family agreed to holistic wellness goals covering housing stability and cultural mentorship.",
        "goals": [
            {
                "goal_text": "Establish stable permanent family housing in community.",
                "category": "Housing & Basic Needs",
                "target_date": "2026-11-30",
                "status": "IN_PROGRESS",
                "sort_order": 1,
                "activities": [
                    {
                        "activity_text": "Submit housing application to Band Housing Authority.",
                        "responsible_type": "WORKER",
                        "responsible_name": "Caseworker Dan",
                        "due_date": "2026-09-15",
                        "status": "IN_PROGRESS",
                    },
                    {
                        "activity_text": "Gather income confirmation documents.",
                        "responsible_type": "FAMILY_MEMBER",
                        "responsible_name": "Marcus Father",
                        "due_date": "2026-09-10",
                        "status": "NOT_STARTED",
                    },
                ],
            },
            {
                "goal_text": "Connect youth with cultural Elder mentorship program.",
                "category": "Cultural & Traditional Healing",
                "target_date": "2026-10-15",
                "status": "NOT_STARTED",
                "sort_order": 2,
                "activities": [
                    {
                        "activity_text": "Attend weekly youth drum & round dance circle.",
                        "responsible_type": "COMMUNITY",
                        "responsible_name": "Elder Circle",
                        "due_date": "2026-10-01",
                        "status": "NOT_STARTED",
                    }
                ],
            },
        ],
    }

    create_res = await client.post(f"/api/v1/cases/{case_id}/plans", headers=headers, json=plan_payload)
    assert create_res.status_code == 201
    plan = create_res.json()
    plan_id = plan["id"]
    goals = plan["current_version"]["goals"]
    assert len(goals) == 2
    goal1_id = goals[0]["id"]
    act1_id = goals[0]["activities"][0]["id"]

    # 3. Complete Activity 1
    comp_act = await client.post(
        f"/api/v1/plans/activities/{act1_id}/complete",
        headers=headers,
        json={"completion_notes": "Application submitted and received by housing officer."},
    )
    assert comp_act.status_code == 200
    act_data = comp_act.json()
    assert act_data["status"] == "COMPLETED"
    assert act_data["completed_at"] is not None

    # 4. Complete Goal 1
    comp_goal = await client.post(
        f"/api/v1/plans/goals/{goal1_id}/complete",
        headers=headers,
        json={"notes": "Housing secured and keys handed over."},
    )
    assert comp_goal.status_code == 200
    goal_data = comp_goal.json()
    assert goal_data["status"] == "COMPLETED"
    assert goal_data["completed_at"] is not None

    # 5. Fetch updated plan and verify metrics
    get_plan = await client.get(f"/api/v1/plans/{plan_id}", headers=headers)
    assert get_plan.status_code == 200
    detail = get_plan.json()
    metrics = detail["metrics"]
    assert metrics["total_goals"] == 2
    assert metrics["completed_goals"] == 1
    assert metrics["completion_percentage"] == 50.0
    assert metrics["total_activities"] == 3
    assert metrics["completed_activities"] == 1
