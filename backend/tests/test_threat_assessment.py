"""Test suite for Threat Assessment indicators, present/impending danger, and completion."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_threat_assessment_danger_indicators_and_completion(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    # 1. Create a test case
    case_res = await client.post(
        "/api/v1/cases",
        json={
            "title": "Emergency Referral Safety Investigation",
            "case_type": "Child Safety",
            "status": "Open",
            "priority": "Urgent",
        },
        headers=caseworker_user["headers"],
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Start THREAT_ASSESSMENT
    start_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "THREAT_ASSESSMENT", "title": "Initial Threat & Danger Screening"},
        headers=caseworker_user["headers"],
    )
    assert start_res.status_code == 201
    asm_data = start_res.json()
    asm_id = asm_data["id"]
    version_data = asm_data["template_version"]

    q_map = {}
    opt_map = {}
    for sec in version_data["sections"]:
        for q in sec["questions"]:
            q_map[q["key"]] = q["id"]
            for opt in q["options"]:
                opt_map[f"{q['key']}:{opt['key']}"] = opt["id"]

    # 3. Enter answers with Impending Danger identified
    answers_payload = {
        "answers": [
            {"question_id": q_map["immediate_physical_harm"], "boolean_value": False},
            {"question_id": q_map["caregiver_incapacitated"], "boolean_value": False},
            {"question_id": q_map["child_in_acute_peril"], "boolean_value": False},
            {"question_id": q_map["uncontrolled_escalating_threat"], "boolean_value": True},
            {"question_id": q_map["vulnerable_child"], "boolean_value": True},
            {
                "question_id": q_map["impending_danger_notes"],
                "text_value": "Escalating domestic conflict; infant in residence.",
            },
            {"question_id": q_map["kinship_safety_placement"], "boolean_value": True},
            {"question_id": q_map["community_supports_active"], "boolean_value": True},
            {
                "question_id": q_map["intervention_details"],
                "text_value": "Maternal aunt providing 24/7 in-home protective care.",
            },
            {
                "question_id": q_map["threat_determination_outcome"],
                "selected_option_ids": [opt_map["threat_determination_outcome:CONDITIONALLY_SAFE"]],
            },
            {
                "question_id": q_map["clinical_safety_rationale"],
                "text_value": "Impending danger controlled by immediate kinship safety network.",
            },
        ],
        "determination": "CONDITIONALLY_SAFE",
        "determination_notes": "Safety interventions in place controlling impending danger.",
    }

    save_res = await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json=answers_payload,
        headers=caseworker_user["headers"],
    )
    assert save_res.status_code == 200
    saved_data = save_res.json()

    # Verify indicator counts
    ind = saved_data["indicator_summary"]
    assert ind["impending_danger_count"] >= 1
    assert ind["present_danger_count"] == 0

    # 4. Complete Threat Assessment
    complete_res = await client.post(
        f"/api/v1/assessments/{asm_id}/complete",
        json={
            "determination": "CONDITIONALLY_SAFE",
            "determination_notes": "Kinship plan active and verified on site.",
        },
        headers=caseworker_user["headers"],
    )
    assert complete_res.status_code == 200
    comp_data = complete_res.json()
    assert comp_data["status"] == "COMPLETED"
    assert comp_data["determination"] == "CONDITIONALLY_SAFE"
