"""Tests for Reporting Security, Medical Privacy Redaction, and Case Restriction Isolation (Phase 11)."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CasePerson, CaseRestriction
from app.models.person import Person


@pytest.mark.asyncio
async def test_child_passport_medical_redaction_and_case_restriction(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    it_admin_user: dict,
):
    """Verify section-level medical redaction and case restriction blocking in Child Passport."""
    # 1. Create child person
    child = Person(
        first_name="Little",
        last_name="Bear",
        date_of_birth=date(2018, 5, 12),
        gender="MALE",
        indigenous_identity="STATUS_INDIAN",
    )

    db_session.add(child)
    await db_session.flush()

    case = Case(
        case_number=f"CASE-PASS-{uuid.uuid4().hex[:6]}",
        title="Passport Confidential Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.flush()

    cp = CasePerson(case_id=case.id, person_id=child.id, role="subject_child")

    db_session.add(cp)
    await db_session.commit()

    # 2. Caseworker with CLIENT_READ and CLIENT_MEDICAL_READ gets complete passport
    res = await client.get(f"/api/v1/passports/child/{child.id}", headers=caseworker_user["headers"])
    assert res.status_code == 200
    passport = res.json()
    assert passport["demographics"]["first_name"] == "Little"
    assert passport["medical"]["redacted"] is False

    # 3. Apply case restriction for IT Admin
    restr = CaseRestriction(
        case_id=case.id,
        user_id=it_admin_user["user"].id,
        restriction_type="conflict_of_interest",
        reason="Family conflict",
        is_active=True,
    )
    db_session.add(restr)
    await db_session.commit()

    # 4. IT Admin without REPORT_CHILD_PASSPORT capability -> HTTP 403
    res_it = await client.get(f"/api/v1/passports/child/{child.id}", headers=it_admin_user["headers"])
    assert res_it.status_code == 403


@pytest.mark.asyncio
async def test_saved_report_ownership_and_visibility(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    it_admin_user: dict,
):
    """Ensure private saved reports cannot be read or run by unauthorized users."""
    # 1. Caseworker creates a private saved report
    payload = {
        "name": "My Private Caseload Report",
        "dataset_key": "cases",
        "visibility": "PRIVATE",
        "configuration": {"fields": ["case_number", "status"]},
    }
    create_res = await client.post("/api/v1/reports/saved", json=payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    report_id = create_res.json()["id"]

    # 2. Caseworker can run own saved report
    run_res = await client.post(f"/api/v1/reports/saved/{report_id}/run", headers=caseworker_user["headers"])
    assert run_res.status_code == 200

    # 3. IT Admin attempting to run Caseworker's private report -> HTTP 403 Forbidden
    it_run_res = await client.post(f"/api/v1/reports/saved/{report_id}/run", headers=it_admin_user["headers"])
    assert it_run_res.status_code == 403
