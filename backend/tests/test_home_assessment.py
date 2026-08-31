"""Test suite for Home Assessment workflow, indicators, and persistence."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_home_assessment_full_flow(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    # 1. Create a test case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Test Family Case for Home Assessment", "case_type": "Child Safety", "status": "Open", "priority": "High"},
        headers=caseworker_user["headers"],
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Start a HOME_ASSESSMENT
    start_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "HOME_ASSESSMENT", "title": "Initial Residence Safety Visit"},
        headers=caseworker_user["headers"],
    )
    assert start_res.status_code == 201
    asm_data = start_res.json()
    assert asm_data["status"] == "DRAFT"
    assert "ASM-" in asm_data["assessment_number"]
    asm_id = asm_data["id"]
    version_data = asm_data["template_version"]
    assert version_data is not None

    # Map question keys to UUIDs and options
    q_map = {}
    opt_map = {}
    for sec in version_data["sections"]:
        for q in sec["questions"]:
            q_map[q["key"]] = q["id"]
            for opt in q["options"]:
                opt_map[f"{q['key']}:{opt['key']}"] = opt["id"]

    # 3. Enter and save answers
    answers_payload = {
        "answers": [
            {"question_id": q_map["substance_use_detected"], "boolean_value": True},
            {"question_id": q_map["substance_use_details"], "text_value": "Alcohol containers in living area."},
            {"question_id": q_map["hazardous_chemicals"], "boolean_value": False},
            {"question_id": q_map["sanitation_concerns"], "boolean_value": False},
            {"question_id": q_map["broken_windows"], "boolean_value": False},
            {"question_id": q_map["running_water"], "boolean_value": True},
            {"question_id": q_map["adequate_heat"], "boolean_value": True},
            {"question_id": q_map["overcrowding"], "boolean_value": False},
            {"question_id": q_map["structural_concerns"], "boolean_value": False},
            {"question_id": q_map["recognizes_hazards"], "boolean_value": True},
            {"question_id": q_map["willing_to_remedy"], "boolean_value": True},
            {"question_id": q_map["support_network_present"], "boolean_value": True},
            {
                "question_id": q_map["home_safety_outcome"],
                "selected_option_ids": [opt_map["home_safety_outcome:SAFETY_PLAN_CREATED"]],
            },
            {"question_id": q_map["action_plan_summary"], "text_value": "Family agreed to remove all substances and attend family support."},
        ],
        "determination": "SAFETY_PLAN_CREATED",
        "determination_notes": "Child safe in home with active safety plan in place.",
        "summary": "Completed home visit; living conditions stable with remedial support.",
    }

    save_res = await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json=answers_payload,
        headers=caseworker_user["headers"],
    )
    assert save_res.status_code == 200
    saved_data = save_res.json()
    assert saved_data["status"] == "IN_PROGRESS"

    # Verify deterministic indicator calculation
    ind = saved_data["indicator_summary"]
    assert ind["active_concerns_count"] >= 1
    assert ind["protective_capacities_count"] >= 3

    # 4. Complete assessment
    complete_res = await client.post(
        f"/api/v1/assessments/{asm_id}/complete",
        json={
            "determination": "SAFETY_PLAN_CREATED",
            "determination_notes": "Safety plan executed and agreed with grandmother and worker.",
        },
        headers=caseworker_user["headers"],
    )
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["completed_at"] is not None

    # 5. Lock assessment
    lock_res = await client.post(
        f"/api/v1/assessments/{asm_id}/lock",
        json={"reason": "Assessment locked following supervisor review."},
        headers=caseworker_user["headers"],
    )
    assert lock_res.status_code == 200
    locked_data = lock_res.json()
    assert locked_data["status"] == "LOCKED"
    assert locked_data["is_locked"] is True

    # 6. Attempting to modify answers while locked must fail with 400 Bad Request
    fail_save = await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json=answers_payload,
        headers=caseworker_user["headers"],
    )
    assert fail_save.status_code == 400
    err_msg = fail_save.json().get("detail") or fail_save.json().get("error", {}).get("message", "")
    assert "locked" in err_msg.lower()
