"""Test suite for Assessment Lifecycle, Director Unlock/Reassignment, and Comparison Engine."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_director_unlock_governance_and_audit(
    client: AsyncClient,
    caseworker_user,
    executive_director_user,
    seed_templates,
):
    # 1. Create case & start assessment
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Test Case for Unlock Governance", "case_type": "Child Safety", "status": "Open", "priority": "Medium"},
        headers=caseworker_user["headers"],
    )
    case_id = case_res.json()["id"]

    start_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "HOME_ASSESSMENT"},
        headers=caseworker_user["headers"],
    )
    asm_id = start_res.json()["id"]
    version_data = start_res.json()["template_version"]

    q_map = {q["key"]: q["id"] for sec in version_data["sections"] for q in sec["questions"]}
    opt_map = {f"{q['key']}:{opt['key']}": opt["id"] for sec in version_data["sections"] for q in sec["questions"] for opt in q["options"]}

    # Save answers & complete
    await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json={
            "answers": [
                {"question_id": q_map["substance_use_detected"], "boolean_value": False},
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
                    "selected_option_ids": [opt_map["home_safety_outcome:CHILD_SAFE_AT_HOME"]],
                },
            ],
            "determination": "CHILD_SAFE_AT_HOME",
        },
        headers=caseworker_user["headers"],
    )

    await client.post(
        f"/api/v1/assessments/{asm_id}/complete",
        json={"determination": "CHILD_SAFE_AT_HOME"},
        headers=caseworker_user["headers"],
    )

    # Lock assessment
    await client.post(
        f"/api/v1/assessments/{asm_id}/lock",
        headers=caseworker_user["headers"],
    )

    # 2. Caseworker tries to unlock -> 403 Forbidden
    cw_unlock = await client.post(
        f"/api/v1/assessments/{asm_id}/unlock",
        json={"reason": "Need to fix typo in notes"},
        headers=caseworker_user["headers"],
    )
    assert cw_unlock.status_code == 403

    # 3. Director unlocks with mandatory reason
    dir_unlock = await client.post(
        f"/api/v1/assessments/{asm_id}/unlock",
        json={"reason": "Court requested supplemental living condition details; approved for amendment."},
        headers=executive_director_user["headers"],
    )
    assert dir_unlock.status_code == 200
    unlocked_data = dir_unlock.json()
    assert unlocked_data["status"] == "COMPLETED"
    assert unlocked_data["is_locked"] is False
    assert len(unlocked_data["unlock_events"]) == 1
    assert "Court requested" in unlocked_data["unlock_events"][0]["reason"]


@pytest.mark.asyncio
async def test_director_reassignment_to_different_case(
    client: AsyncClient,
    caseworker_user,
    executive_director_user,
    seed_templates,
):
    # 1. Create two cases
    case1_res = await client.post(
        "/api/v1/cases",
        json={"title": "Case 1", "case_type": "Child Safety", "status": "Open", "priority": "Medium"},
        headers=caseworker_user["headers"],
    )
    case1_id = case1_res.json()["id"]

    case2_res = await client.post(
        "/api/v1/cases",
        json={"title": "Case 2 Correct Destination", "case_type": "Child Safety", "status": "Open", "priority": "Medium"},
        headers=caseworker_user["headers"],
    )
    case2_id = case2_res.json()["id"]

    # Start assessment on Case 1
    start_res = await client.post(
        f"/api/v1/cases/{case1_id}/assessments",
        json={"case_id": case1_id, "template_key": "HOME_ASSESSMENT"},
        headers=caseworker_user["headers"],
    )
    asm_id = start_res.json()["id"]

    # 2. Caseworker tries to reassign -> 403 Forbidden
    cw_reassign = await client.post(
        f"/api/v1/assessments/{asm_id}/reassign",
        json={"target_case_id": case2_id, "reason": "Misfiled under wrong case number."},
        headers=caseworker_user["headers"],
    )
    assert cw_reassign.status_code == 403

    # 3. Director reassigns to Case 2
    dir_reassign = await client.post(
        f"/api/v1/assessments/{asm_id}/reassign",
        json={"target_case_id": case2_id, "reason": "Administrative correction; misfiled during intake intake review."},
        headers=executive_director_user["headers"],
    )
    assert dir_reassign.status_code == 200
    reassigned_data = dir_reassign.json()
    assert reassigned_data["case_id"] == case2_id


@pytest.mark.asyncio
async def test_time_series_assessment_comparison(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    # 1. Create case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Comparison Family Case", "case_type": "Child Safety", "status": "Open", "priority": "High"},
        headers=caseworker_user["headers"],
    )
    case_id = case_res.json()["id"]

    # 2. Start Assessment 1 (Baseline - with concerns)
    asm1_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "HOME_ASSESSMENT", "title": "Month 1 Home Assessment"},
        headers=caseworker_user["headers"],
    )
    asm1_id = asm1_res.json()["id"]
    version_data = asm1_res.json()["template_version"]
    q_map = {q["key"]: q["id"] for sec in version_data["sections"] for q in sec["questions"]}
    opt_map = {f"{q['key']}:{opt['key']}": opt["id"] for sec in version_data["sections"] for q in sec["questions"] for opt in q["options"]}

    await client.put(
        f"/api/v1/assessments/{asm1_id}/answers",
        json={
            "answers": [
                {"question_id": q_map["substance_use_detected"], "boolean_value": True},
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
            ],
            "determination": "SAFETY_PLAN_CREATED",
        },
        headers=caseworker_user["headers"],
    )
    await client.post(
        f"/api/v1/assessments/{asm1_id}/complete",
        json={"determination": "SAFETY_PLAN_CREATED"},
        headers=caseworker_user["headers"],
    )

    # 3. Start Assessment 2 (Follow-up - resolved concerns)
    asm2_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "HOME_ASSESSMENT", "title": "Month 3 Re-Assessment"},
        headers=caseworker_user["headers"],
    )
    asm2_id = asm2_res.json()["id"]

    await client.put(
        f"/api/v1/assessments/{asm2_id}/answers",
        json={
            "answers": [
                {"question_id": q_map["substance_use_detected"], "boolean_value": False},  # CHANGED from True to False!
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
                    "selected_option_ids": [opt_map["home_safety_outcome:CHILD_SAFE_AT_HOME"]],
                },
            ],
            "determination": "CHILD_SAFE_AT_HOME",
        },
        headers=caseworker_user["headers"],
    )
    await client.post(
        f"/api/v1/assessments/{asm2_id}/complete",
        json={"determination": "CHILD_SAFE_AT_HOME"},
        headers=caseworker_user["headers"],
    )

    # 4. Compare both assessments
    compare_res = await client.get(
        f"/api/v1/assessments/compare?ids={asm1_id},{asm2_id}",
        headers=caseworker_user["headers"],
    )
    assert compare_res.status_code == 200
    comp_data = compare_res.json()
    assert comp_data["template_key"] == "HOME_ASSESSMENT"
    assert len(comp_data["assessments"]) == 2

    # Check that substance_use_detected is flagged as is_changed = True
    substance_q = next(q for q in comp_data["questions"] if q["question_key"] == "substance_use_detected")
    assert substance_q["is_changed"] is True
    assert substance_q["values"][0]["boolean_value"] is True
    assert substance_q["values"][1]["boolean_value"] is False

    # Check that running_water is is_changed = False
    water_q = next(q for q in comp_data["questions"] if q["question_key"] == "running_water")
    assert water_q["is_changed"] is False
