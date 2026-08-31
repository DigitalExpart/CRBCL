"""Tests for Child & Case Transfer Request Workflows and Supervisor Approvals."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.team import Team


@pytest.mark.anyio
async def test_case_transfer_lifecycle(client: AsyncClient, supervisor_user: dict, db_session):
    headers = supervisor_user["headers"]

    # 1. Fetch or create two distinct teams
    from app.models.team import TeamMembership
    teams_res = await db_session.execute(select(Team).limit(2))
    teams = teams_res.scalars().all()
    source_team = teams[0]
    if len(teams) < 2:
        destination_team = Team(code="prevention_team", name="Prevention Team", short_name="Prev")
        db_session.add(destination_team)
        await db_session.flush()
    else:
        destination_team = teams[1]

    # Grant supervisor access to destination team
    db_session.add(TeamMembership(user_id=supervisor_user["user"].id, team_id=destination_team.id))
    await db_session.commit()

    # 2. Create Case assigned to source team
    case_res = await client.post(
        "/api/v1/cases",
        json={
            "title": "Youth Transition File",
            "case_type": "PREVENTION",
            "assigned_team_id": str(source_team.id),
        },
        headers=headers,
    )
    assert case_res.status_code == 201
    case_id = case_res.json()["id"]

    # 3. Create Transfer Request (Draft)
    transfer_payload = {
        "destination_team_id": str(destination_team.id),
        "reason": "Youth turning 18; transferring from Prevention to Post-Majority support.",
        "submit_immediately": False,
    }
    create_t_res = await client.post(
        f"/api/v1/cases/{case_id}/transfers",
        json=transfer_payload,
        headers=headers,
    )
    assert create_t_res.status_code == 201
    transfer = create_t_res.json()
    transfer_id = transfer["id"]
    assert transfer["status"] == "DRAFT"

    # 4. Submit Transfer Request
    submit_res = await client.post(
        f"/api/v1/transfers/{transfer_id}/submit",
        headers=headers,
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_APPROVAL"

    # 5. Check Pending Transfers Queue
    pending_res = await client.get("/api/v1/transfers/pending", headers=headers)
    assert pending_res.status_code == 200
    pending_list = pending_res.json()
    assert any(t["id"] == transfer_id for t in pending_list)

    # 6. Supervisor Returns for Additional Clarification
    return_res = await client.post(
        f"/api/v1/transfers/{transfer_id}/return",
        json={"review_notes": "Please attach housing readiness assessment before transfer."},
        headers=headers,
    )
    assert return_res.status_code == 200
    assert return_res.json()["status"] == "RETURNED"

    # Re-submit
    await client.post(
        f"/api/v1/transfers/{transfer_id}/submit",
        headers=headers,
    )

    # 7. Supervisor Approves Transfer
    approve_res = await client.post(
        f"/api/v1/transfers/{transfer_id}/approve",
        json={"review_notes": "Readiness assessment verified. Transfer approved."},
        headers=headers,
    )
    assert approve_res.status_code == 200
    approved_transfer = approve_res.json()
    assert approved_transfer["status"] == "APPROVED"

    # Idempotency check on second approval
    approve_again = await client.post(
        f"/api/v1/transfers/{transfer_id}/approve",
        json={"review_notes": "Duplicate call"},
        headers=headers,
    )
    assert approve_again.status_code == 200
    assert approve_again.json()["status"] == "APPROVED"

    # 8. Verify Case assigned_team_id was atomically updated to destination_team
    case_check = await client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert case_check.status_code == 200
    assert case_check.json()["assigned_team_id"] == str(destination_team.id)
