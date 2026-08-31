"""Tests for Case Note to Plan Goal Linkage and Boundary Enforcement."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_note_goal_linkage_and_cross_case_rejection(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create two separate cases
    c1_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "ChildA", "last_name": "FamilyOne", "date_of_birth": "2018-01-01", "gender": "Female"},
    )
    p1_id = c1_res.json()["id"]

    case1_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Case One", "case_type": "Child Protection", "primary_client_id": p1_id},
    )
    case1_id = case1_res.json()["id"]

    c2_res = await client.post(
        "/api/v1/clients",
        headers=headers,
        json={"first_name": "ChildB", "last_name": "FamilyTwo", "date_of_birth": "2017-02-02", "gender": "Male"},
    )
    p2_id = c2_res.json()["id"]

    case2_res = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Case Two", "case_type": "Child Protection", "primary_client_id": p2_id},
    )
    case2_id = case2_res.json()["id"]

    # 2. Create Plan on Case One with a Goal
    plan1_res = await client.post(
        f"/api/v1/cases/{case1_id}/plans",
        headers=headers,
        json={
            "case_id": case1_id,
            "plan_type": "CASE_PLAN",
            "title": "Case One Wellness Plan",
            "goals": [{"goal_text": "Case One Primary Wellness Goal", "target_date": "2026-10-31"}],
        },
    )
    assert plan1_res.status_code == 201
    goal1_id = plan1_res.json()["current_version"]["goals"][0]["id"]

    # 3. Fetch active goals for Case One
    active_goals_res = await client.get(f"/api/v1/cases/{case1_id}/active-goals", headers=headers)
    assert active_goals_res.status_code == 200
    active_goals = active_goals_res.json()
    assert len(active_goals) == 1
    assert active_goals[0]["id"] == goal1_id

    # 4. Create Case Note on Case One linked to Goal One -> MUST succeed
    note_res = await client.post(
        f"/api/v1/cases/{case1_id}/notes",
        headers=headers,
        json={
            "subject": "Home visit regarding wellness goal",
            "content": "Met with family and reviewed progress on primary goal.",
            "note_type": "Home Visit",
            "goal_id": goal1_id,
        },
    )
    assert note_res.status_code == 201
    note_data = note_res.json()
    assert note_data["goal_id"] == goal1_id

    # 5. Attempt to create Case Note on Case Two linked to Goal One (Cross-Case!) -> MUST FAIL (400 Bad Request)
    cross_case_fail = await client.post(
        f"/api/v1/cases/{case2_id}/notes",
        headers=headers,
        json={
            "subject": "Cross-case invalid note",
            "content": "Attempting to link goal from Case One to Case Two.",
            "note_type": "Progress Note",
            "goal_id": goal1_id,
        },
    )
    assert cross_case_fail.status_code == 400
    assert "Goal does not belong to this case" in cross_case_fail.text

    # 6. Attempt to link random non-existent goal UUID -> MUST FAIL (400 Bad Request)
    random_goal_id = str(uuid.uuid4())
    random_fail = await client.post(
        f"/api/v1/cases/{case1_id}/notes",
        headers=headers,
        json={
            "subject": "Invalid goal note",
            "content": "Non-existent goal.",
            "note_type": "Progress Note",
            "goal_id": random_goal_id,
        },
    )
    assert random_fail.status_code == 400
