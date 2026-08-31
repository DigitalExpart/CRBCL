"""Tests for Case Lifecycle State Machine, Status History, and Controlled Closure/Reopening."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_case_lifecycle_create_close_reopen(client: AsyncClient, supervisor_user: dict):
    headers = supervisor_user["headers"]

    # 1. Create Case
    create_payload = {
        "title": "Investigation into Family Wellness",
        "case_type": "PROTECTION",
        "priority": "High",
        "risk_level": "High",
        "stage": "INVESTIGATION",
        "description": "Child protection safety assessment matter.",
    }
    create_res = await client.post("/api/v1/cases", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    case_data = create_res.json()
    case_id = case_data["id"]
    assert case_data["status"] == "Open"
    assert case_data["stage"] == "INVESTIGATION"
    assert case_data["case_number"].startswith("CRB-")

    # 2. Attempt to arbitrarily change status via generic PATCH (Must be rejected)
    patch_res = await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "Closed"},
        headers=headers,
    )
    assert patch_res.status_code == 400
    assert "cannot be changed directly" in patch_res.text

    # 3. Controlled Closure
    close_payload = {
        "closed_reason": "Family wellness plan successfully completed. All safety goals achieved.",
        "closed_date": "2026-08-30",
    }
    close_res = await client.post(
        f"/api/v1/cases/{case_id}/close",
        json=close_payload,
        headers=headers,
    )
    assert close_res.status_code == 200
    closed_data = close_res.json()
    assert closed_data["status"] == "Closed"
    assert closed_data["stage"] == "CLOSURE"
    assert closed_data["closed_reason"] == close_payload["closed_reason"]

    # 4. Controlled Reopen
    reopen_payload = {
        "reopened_reason": "New concern reported requiring follow-up assessment.",
    }
    reopen_res = await client.post(
        f"/api/v1/cases/{case_id}/reopen",
        json=reopen_payload,
        headers=headers,
    )
    assert reopen_res.status_code == 200
    reopened_data = reopen_res.json()
    assert reopened_data["status"] == "Reopened"
    assert reopened_data["stage"] == "INVESTIGATION"
    assert reopened_data["reopened_reason"] == reopen_payload["reopened_reason"]

    # 5. Verify Status History
    history_res = await client.get(
        f"/api/v1/cases/{case_id}/status-history",
        headers=headers,
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) >= 3  # Initial Open, Closed, Reopened
    statuses = [h["new_status"] for h in history]
    assert "Open" in statuses
    assert "Closed" in statuses
    assert "Reopened" in statuses

    # 6. Verify Case Snapshot
    snapshot_res = await client.get(
        f"/api/v1/cases/{case_id}/snapshot",
        headers=headers,
    )
    assert snapshot_res.status_code == 200
    snapshot = snapshot_res.json()
    assert snapshot["case_number"] == case_data["case_number"]
    assert snapshot["status"] == "Reopened"
    assert "alerts" in snapshot
