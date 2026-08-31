"""Tests for Case Restrictions and Conflict of Interest Enforcement."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_case_restriction_central_enforcement(client: AsyncClient, supervisor_user: dict, caseworker_user: dict):
    admin_headers = supervisor_user["headers"]
    cw_headers = caseworker_user["headers"]
    cw_user_id = str(caseworker_user["user"].id)

    # 1. Create a Case as Supervisor
    case_res = await client.post(
        "/api/v1/cases",
        json={"title": "Sensitive Family Investigation", "case_type": "PROTECTION"},
        headers=admin_headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 2. Before restriction: Caseworker CAN access the case
    get_before = await client.get(f"/api/v1/cases/{case_id}", headers=cw_headers)
    assert get_before.status_code == 200

    # 3. Add Case Restriction against the caseworker (Conflict of Interest)
    restriction_payload = {
        "user_id": cw_user_id,
        "restriction_type": "conflict_of_interest",
        "reason": "Caseworker is related to caregiver in this matter.",
    }
    restrict_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions",
        json=restriction_payload,
        headers=admin_headers,
    )
    assert restrict_res.status_code == 201
    restriction_id = restrict_res.json()["id"]

    # 4. After restriction: Direct API access from the restricted user returns HTTP 403 Forbidden!
    get_after = await client.get(f"/api/v1/cases/{case_id}", headers=cw_headers)
    assert get_after.status_code == 403
    assert "Active conflict-of-interest restriction" in get_after.text

    # Snapshot access is also denied
    snapshot_denied = await client.get(f"/api/v1/cases/{case_id}/snapshot", headers=cw_headers)
    assert snapshot_denied.status_code == 403

    # 5. Supervisor removes the restriction
    remove_res = await client.post(
        f"/api/v1/cases/{case_id}/restrictions/{restriction_id}/remove",
        json={"removal_reason": "Conflict resolved after family placement change."},
        headers=admin_headers,
    )
    assert remove_res.status_code == 200
    assert remove_res.json()["is_active"] is False

    # 6. Access is restored
    get_restored = await client.get(f"/api/v1/cases/{case_id}", headers=cw_headers)
    assert get_restored.status_code == 200
