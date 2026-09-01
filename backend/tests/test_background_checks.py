"""Tests for Polymorphic Background Checks, Screening, and Placement Safety Adjudication."""

import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_background_check_workflow(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create a background check request for a kinship caregiver
    check_payload = {
        "subject_type": "PERSON",
        "subject_name": "Eleanor Cote",
        "check_type": "VULNERABLE_SECTOR",
        "request_date": "2026-08-10",
        "conducted_by_agency": "Kamsack RCMP Detachment",
        "risk_assessment_notes": "Kinship aunt applicant for customary care placement.",
    }
    create_res = await client.post(
        "/api/v1/background-checks",
        headers=headers,
        json=check_payload,
    )
    assert create_res.status_code == 201
    check = create_res.json()
    check_id = check["id"]
    assert check["status"] == "PENDING"
    assert check["is_eligible_for_placement"] is False

    # 2. Retrieve background check
    get_res = await client.get(f"/api/v1/background-checks/{check_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["subject_name"] == "Eleanor Cote"

    # 3. Update background check reference number
    update_res = await client.patch(
        f"/api/v1/background-checks/{check_id}",
        headers=headers,
        json={"clearance_reference_number": "RCMP-2026-88741-VS"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["clearance_reference_number"] == "RCMP-2026-88741-VS"

    # 4. Adjudicate background check (pass and mark eligible)
    adjudicate_payload = {
        "status": "PASSED",
        "is_eligible_for_placement": True,
        "completion_date": "2026-08-20",
        "expiry_date": "2027-08-20",
        "risk_assessment_notes": "Clean vulnerable sector clearance confirmed. Approved for kinship placement.",
    }
    adj_res = await client.post(
        f"/api/v1/background-checks/{check_id}/adjudicate",
        headers=headers,
        json=adjudicate_payload,
    )
    assert adj_res.status_code == 200
    adjudicated = adj_res.json()
    assert adjudicated["status"] == "PASSED"
    assert adjudicated["is_eligible_for_placement"] is True
    assert adjudicated["adjudicated_by"] is not None
    assert adjudicated["adjudicated_at"] is not None

    # 5. List background checks with filters
    list_res = await client.get(
        "/api/v1/background-checks?status=PASSED&check_type=VULNERABLE_SECTOR",
        headers=headers,
    )
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] >= 1
    assert any(c["id"] == check_id for c in data["items"])
