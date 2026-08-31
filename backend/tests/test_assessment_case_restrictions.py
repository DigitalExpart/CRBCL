import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_case_restriction_blocks_assessments(
    client: AsyncClient,
    caseworker_user,
    supervisor_user,
    seed_templates,
):
    # 1. Supervisor creates a case
    case_res = await client.post(
        "/api/v1/cases",
        json={
            "title": "Restricted Family Safety File",
            "case_type": "Child Safety",
            "status": "Open",
            "priority": "High",
        },
        headers=supervisor_user["headers"],
    )
    case_id = case_res.json()["id"]

    # 2. Supervisor starts an assessment on the case
    asm_res = await client.post(
        f"/api/v1/cases/{case_id}/assessments",
        json={"case_id": case_id, "template_key": "HOME_ASSESSMENT", "title": "Confidential Assessment"},
        headers=supervisor_user["headers"],
    )
    assert asm_res.status_code == 201
    asm_id = asm_res.json()["id"]

    # 3. Restrict Caseworker from this Case (conflict of interest)
    restrict_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        json={
            "user_id": str(caseworker_user["user"].id),
            "restriction_type": "conflict_of_interest",
            "reason": "Caseworker is related to family member.",
        },
        headers=supervisor_user["headers"],
    )
    assert restrict_res.status_code == 201

    # 4. Caseworker attempts to list assessments for the restricted case -> 403 Forbidden
    list_res = await client.get(f"/api/v1/cases/{case_id}/assessments", headers=caseworker_user["headers"])
    assert list_res.status_code == 403
    assert (
        "restriction" in (list_res.json().get("detail") or list_res.json().get("error", {}).get("message", "")).lower()
    )

    # 5. Caseworker attempts to fetch the specific assessment by ID -> 403 Forbidden
    get_res = await client.get(f"/api/v1/assessments/{asm_id}", headers=caseworker_user["headers"])
    assert get_res.status_code == 403
    assert "restriction" in (get_res.json().get("detail") or get_res.json().get("error", {}).get("message", "")).lower()

    # 6. Caseworker attempts to save answers on the restricted assessment -> 403 Forbidden
    save_res = await client.put(
        f"/api/v1/assessments/{asm_id}/answers",
        json={"answers": []},
        headers=caseworker_user["headers"],
    )
    assert save_res.status_code == 403
    assert (
        "restriction" in (save_res.json().get("detail") or save_res.json().get("error", {}).get("message", "")).lower()
    )

    # 7. Supervisor (not restricted) can access the assessment without issue -> 200 OK
    sup_get = await client.get(f"/api/v1/assessments/{asm_id}", headers=supervisor_user["headers"])
    assert sup_get.status_code == 200
