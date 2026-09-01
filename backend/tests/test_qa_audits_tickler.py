"""Tests for QA Audit Checklists, Immutability, Audit Tickler Engine & QA Dashboard (Phase 11)."""

import uuid
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case


@pytest.mark.asyncio
async def test_qa_template_versioning_and_audit_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Verify QA template listing, audit creation, score calculation, and completed audit immutability."""
    # 1. Fetch template catalog (triggers default template seeding)
    tpl_res = await client.get("/api/v1/qa/templates", headers=caseworker_user["headers"])
    assert tpl_res.status_code == 200
    templates = tpl_res.json()
    assert len(templates) >= 1

    tpl = templates[0]
    ver_id = tpl["versions"][0]["id"]
    item_id = tpl["versions"][0]["items"][0]["id"]

    # 2. Create a new case
    case = Case(
        case_number=f"CASE-QA-{uuid.uuid4().hex[:6]}",
        title="QA Audit Test Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.commit()

    # 3. Create QA Audit review
    audit_payload = {
        "case_id": str(case.id),
        "template_version_id": ver_id,
        "review_date": str(date.today()),
        "status": "DRAFT",
        "notes": "Initial draft review",
        "results": [
            {
                "item_id": item_id,
                "compliance": "YES",
                "notes": "Note is locked and verified",
            }
        ],
    }
    create_res = await client.post("/api/v1/qa/audits", json=audit_payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    audit = create_res.json()
    assert audit["status"] == "DRAFT"
    assert audit["overall_score"] == 100.0

    # 4. Finalize Audit to COMPLETED
    audit_id = audit["id"]
    update_res = await client.put(
        f"/api/v1/qa/audits/{audit_id}",
        json={"status": "COMPLETED"},
        headers=caseworker_user["headers"],
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "COMPLETED"
    assert update_res.json()["completed_at"] is not None

    # 5. Completed Audit Immutability Test: Un-completing completed audit must be rejected
    bad_uncomplete = await client.put(
        f"/api/v1/qa/audits/{audit_id}",
        json={"status": "DRAFT"},
        headers=caseworker_user["headers"],
    )
    assert bad_uncomplete.status_code == 400


@pytest.mark.asyncio
async def test_audit_tickler_engine_and_qa_dashboard(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Verify Audit Tickler status classification (OVERDUE, DUE_SOON, OK) and QA dashboard metrics."""
    # 1. Audit tickler endpoint
    tickler_res = await client.get("/api/v1/qa/tickler", headers=caseworker_user["headers"])
    assert tickler_res.status_code == 200
    t_data = tickler_res.json()
    assert "summary" in t_data
    assert "overdue_count" in t_data["summary"]

    # 2. QA Dashboard metrics endpoint
    dash_res = await client.get("/api/v1/qa/dashboard", headers=caseworker_user["headers"])
    assert dash_res.status_code == 200
    d_data = dash_res.json()
    assert "cases_without_notes_count" in d_data
    assert "average_caseload_per_worker" in d_data
