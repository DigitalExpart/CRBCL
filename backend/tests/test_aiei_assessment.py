"""Test suite for AIEI Prevention & Cultural Assessment."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_aiei_prevention_assessment_flow(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    # 1. Create a test case
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Voluntary Family Wellness Request", "case_type": "Prevention & Wellness", "status": "Open", "priority": "Medium"},
        headers=caseworker_user["headers"],
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Start AIEI_ASSESSMENT
    start_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "AIEI_ASSESSMENT", "title": "Early Intervention & Cultural Reconnection Plan"},
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

    # 3. Enter answers including multi-select cultural activities and service recommendations
    answers_payload = {
        "answers": [
            {
                "question_id": q_map["cultural_engagement_level"],
                "selected_option_ids": [opt_map["cultural_engagement_level:DESIRES_CONNECTION"]],
            },
            {"question_id": q_map["interested_in_learning_more"], "boolean_value": True},
            {"question_id": q_map["elders_clan_connection"], "text_value": "Bear Clan / Saddle Lake connection."},
            {
                "question_id": q_map["cultural_activities_desired"],
                "selected_option_ids": [
                    opt_map["cultural_activities_desired:LAND_BASED"],
                    opt_map["cultural_activities_desired:TRADITIONAL_PARENTING"],
                ],
            },
            {
                "question_id": q_map["housing_stability"],
                "selected_option_ids": [opt_map["housing_stability:OVERCROWDED_AT_RISK"]],
            },
            {
                "question_id": q_map["employment_income_sources"],
                "selected_option_ids": [
                    opt_map["employment_income_sources:PART_TIME_CASUAL"],
                    opt_map["employment_income_sources:CHILD_BENEFIT"],
                ],
            },
            {"question_id": q_map["chemical_dependency_concerns"], "boolean_value": False},
            {"question_id": q_map["other_stressors"], "text_value": "Food security and winter clothing."},
            {
                "question_id": q_map["recommended_services"],
                "selected_option_ids": [
                    opt_map["recommended_services:CULTURAL_MENTORSHIP"],
                    opt_map["recommended_services:FOOD_SECURITY"],
                    opt_map["recommended_services:FAMILY_WELLNESS_CIRCLES"],
                ],
            },
            {"question_id": q_map["prevention_plan_notes"], "text_value": "Agreed to link family with Elder cultural mentorship program."},
            {
                "question_id": q_map["aiei_determination_outcome"],
                "selected_option_ids": [opt_map["aiei_determination_outcome:COMMUNITY_PREVENTION_OPEN"]],
            },
            {"question_id": q_map["worker_signoff_notes"], "text_value": "Open voluntary prevention file approved."},
        ],
        "determination": "COMMUNITY_PREVENTION_OPEN",
        "determination_notes": "Voluntary prevention file initiated.",
    }

    save_res = await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json=answers_payload,
        headers=caseworker_user["headers"],
    )
    assert save_res.status_code == 200

    # 4. Complete AIEI Assessment
    complete_res = await client.post(
        f"/api/v1/assessments/{asm_id}/complete",
        json={
            "determination": "COMMUNITY_PREVENTION_OPEN",
            "determination_notes": "Family accepted into Prevention and Cultural Wellness program.",
        },
        headers=caseworker_user["headers"],
    )
    assert complete_res.status_code == 200
    assert complete_res.json()["status"] == "COMPLETED"
