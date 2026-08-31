"""Test suite for Assessment Template and Version Management."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_seed_and_list_assessment_templates(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    """Verify seeded templates exist and can be listed by authorized caseworkers."""
    res = await client.get("/api/v1/assessment-templates", headers=caseworker_user["headers"])
    assert res.status_code == 200
    data = res.json()
    keys = {t["key"] for t in data}
    assert "HOME_ASSESSMENT" in keys
    assert "THREAT_ASSESSMENT" in keys
    assert "AIEI_ASSESSMENT" in keys

    # Verify published_version metadata
    home_tmpl = next(t for t in data if t["key"] == "HOME_ASSESSMENT")
    assert home_tmpl["published_version"] is not None
    assert home_tmpl["published_version"]["version_number"] == 1
    assert home_tmpl["published_version"]["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_get_template_details_and_full_structure(
    client: AsyncClient,
    caseworker_user,
    seed_templates,
):
    """Verify retrieving template details includes sections, questions, and options."""
    res = await client.get("/api/v1/assessment-templates/HOME_ASSESSMENT", headers=caseworker_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == "HOME_ASSESSMENT"
    assert data["active_version"] is not None
    assert len(data["active_version"]["sections"]) == 4

    section_keys = {s["key"] for s in data["active_version"]["sections"]}
    assert "HOME_CONCERNS" in section_keys
    assert "PHYSICAL_STATUS" in section_keys
    assert "CAREGIVER_CAPACITIES" in section_keys
    assert "HOME_DETERMINATION" in section_keys


@pytest.mark.asyncio
async def test_template_versioning_and_immutability(
    client: AsyncClient,
    executive_director_user,
    seed_templates,
):
    """Verify published versions are immutable, and creating a new draft version succeeds."""
    # 1. Fetch template
    res = await client.get("/api/v1/assessment-templates/HOME_ASSESSMENT", headers=executive_director_user["headers"])
    assert res.status_code == 200
    tmpl_data = res.json()
    tmpl_id = tmpl_data["id"]
    pub_version_id = tmpl_data["active_version"]["id"]

    # 2. Attempting to add a section to a PUBLISHED version must fail with 400 Bad Request
    fail_res = await client.post(
        f"/api/v1/assessment-templates/versions/{pub_version_id}/sections",
        json={"key": "NEW_SECTION", "title": "New Section"},
        headers=executive_director_user["headers"],
    )
    assert fail_res.status_code == 400
    err_msg = fail_res.json().get("detail") or fail_res.json().get("error", {}).get("message", "")
    assert "immutable" in err_msg.lower()

    # 3. Create a new draft version v2 cloning v1
    v2_res = await client.post(
        f"/api/v1/assessment-templates/{tmpl_id}/versions",
        json={"change_notes": "Version 2 with updated questions", "clone_from_version_id": pub_version_id},
        headers=executive_director_user["headers"],
    )
    assert v2_res.status_code == 201
    v2_data = v2_res.json()
    assert v2_data["version_number"] == 2
    assert v2_data["status"] == "DRAFT"
    assert len(v2_data["sections"]) == 4
    v2_id = v2_data["id"]

    # 4. Add a new section to the DRAFT version
    sec_res = await client.post(
        f"/api/v1/assessment-templates/versions/{v2_id}/sections",
        json={"key": "ADDITIONAL_RESOURCES", "title": "Additional Resources", "sort_order": 5},
        headers=executive_director_user["headers"],
    )
    assert sec_res.status_code == 201
    sec_id = sec_res.json()["id"]

    # 5. Add a question to the new section
    q_res = await client.post(
        f"/api/v1/assessment-templates/sections/{sec_id}/questions",
        json={
            "key": "fire_extinguisher_present",
            "label": "Is there an inspected fire extinguisher on site?",
            "question_type": "BOOLEAN",
            "is_required": True,
            "sort_order": 1,
        },
        headers=executive_director_user["headers"],
    )
    assert q_res.status_code == 201

    # 6. Publish version 2
    pub_res = await client.post(
        f"/api/v1/assessment-templates/versions/{v2_id}/publish",
        headers=executive_director_user["headers"],
    )
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == "PUBLISHED"

    # 7. Check template now has active version 2 with 5 sections
    check_res = await client.get(f"/api/v1/assessment-templates/{tmpl_id}", headers=executive_director_user["headers"])
    assert check_res.status_code == 200
    assert check_res.json()["active_version"]["version_number"] == 2
    assert len(check_res.json()["active_version"]["sections"]) == 5
