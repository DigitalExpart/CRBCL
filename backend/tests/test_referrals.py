"""Comprehensive integration test suite for Phase 3 Intake, Referrals, Screening & Approvals."""

import uuid
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.person import Person
from app.models.timeline import TimelineEvent


@pytest.mark.asyncio
async def test_create_and_list_referrals(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    """Test referral creation with sequence number INT-YYYY-NNNNNN."""
    payload = {
        "received_date": "2026-08-30",
        "received_method": "phone",
        "community": "Muscowpetung Saulteaux Nation",
        "priority": "High",
        "risk_level": "High",
        "summary": "Community member called regarding welfare concern for two children.",
        "immediate_safety_concerns": False,
        "law_enforcement_involved": False,
        "reporter": {
            "is_anonymous": False,
            "is_mandated_reporter": True,
            "reporter_name": "Nurse Brenda",
            "organization": "Community Health Center",
            "phone": "306-555-0122",
        },
        "concerns": [
            {"concern_type": "neglect", "is_primary": True, "severity": "High", "description": "Unmet medical needs"},
            {"concern_type": "housing_insecurity", "is_primary": False, "severity": "Moderate"},
        ],
    }

    res = await client.post("/api/v1/referrals", json=payload, headers=caseworker_user["headers"])
    assert res.status_code == 201
    data = res.json()
    assert "INT-" in data["referral_number"]
    assert data["status"] == "DRAFT"
    assert data["community"] == "Muscowpetung Saulteaux Nation"
    assert data["priority"] == "High"

    referral_id = data["id"]

    # List referrals
    list_res = await client.get("/api/v1/referrals", headers=caseworker_user["headers"])
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == referral_id for item in list_data["items"])


@pytest.mark.asyncio
async def test_reporter_privacy_and_redaction(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    """Verify confidential reporter is redacted or viewable according to permissions."""
    payload = {
        "received_date": "2026-08-30",
        "received_method": "in_person",
        "summary": "Walk-in report with confidential reporter.",
        "reporter": {
            "is_anonymous": False,
            "is_mandated_reporter": False,
            "reporter_name": "Confidential Informant",
            "phone": "306-555-9999",
            "relationship_to_family": "Neighbor",
        },
    }
    create_res = await client.post("/api/v1/referrals", json=payload, headers=caseworker_user["headers"])
    assert create_res.status_code == 201
    referral_id = create_res.json()["id"]

    # Caseworker with intake.reporter.read can read full reporter info
    get_res = await client.get(f"/api/v1/referrals/{referral_id}", headers=caseworker_user["headers"])
    assert get_res.status_code == 200
    rep_data = get_res.json()["reporter"]
    assert rep_data is not None
    assert rep_data["reporter_name"] == "Confidential Informant"
    assert rep_data["phone"] == "306-555-9999"


@pytest.mark.asyncio
async def test_involved_people_and_concerns(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    """Test associating multiple persons (children and adults) and structured concerns."""
    # Seed 2 canonical persons
    p1 = Person(first_name="Liam", last_name="Bear", date_of_birth=date(2018, 4, 10))
    p2 = Person(first_name="Mary", last_name="Bear", date_of_birth=date(1985, 2, 14))
    db_session.add_all([p1, p2])
    await db_session.commit()

    # Create referral
    ref_res = await client.post(
        "/api/v1/referrals",
        json={"received_date": "2026-08-30", "summary": "Family support referral"},
        headers=caseworker_user["headers"],
    )
    ref_id = ref_res.json()["id"]

    # Add child
    rp1 = await client.post(
        f"/api/v1/referrals/{ref_id}/people",
        json={"person_id": str(p1.id), "role": "child", "relationship_to_child": "Self"},
        headers=caseworker_user["headers"],
    )
    assert rp1.status_code == 201

    # Add mother
    rp2 = await client.post(
        f"/api/v1/referrals/{ref_id}/people",
        json={"person_id": str(p2.id), "role": "parent", "relationship_to_child": "Mother", "is_primary_caregiver": True},
        headers=caseworker_user["headers"],
    )
    assert rp2.status_code == 201

    # Add concern
    c_res = await client.post(
        f"/api/v1/referrals/{ref_id}/concerns",
        json={"concern_type": "food_insecurity", "is_primary": True, "severity": "Moderate"},
        headers=caseworker_user["headers"],
    )
    assert c_res.status_code == 201

    # Verify detail
    detail_res = await client.get(f"/api/v1/referrals/{ref_id}", headers=caseworker_user["headers"])
    data = detail_res.json()
    assert len(data["people"]) == 2
    assert data["children_count"] == 1
    assert data["primary_concern"] == "food_insecurity"


@pytest.mark.asyncio
async def test_referral_linking_and_prior_history(client: AsyncClient, caseworker_user, db_session: AsyncSession):
    """Test relational cross-linking between referrals and discovering prior history."""
    p = Person(first_name="Elijah", last_name="Standingready", date_of_birth=date(2012, 6, 20))
    db_session.add(p)
    await db_session.commit()

    # Create first referral
    ref1_res = await client.post(
        "/api/v1/referrals",
        json={"received_date": "2026-07-01", "summary": "First report in July", "people": [{"person_id": str(p.id), "role": "child"}]},
        headers=caseworker_user["headers"],
    )
    ref1_id = ref1_res.json()["id"]

    # Create second referral
    ref2_res = await client.post(
        "/api/v1/referrals",
        json={"received_date": "2026-08-30", "summary": "Second report in August", "people": [{"person_id": str(p.id), "role": "child"}]},
        headers=caseworker_user["headers"],
    )
    ref2_id = ref2_res.json()["id"]

    # Link referrals
    link_res = await client.post(
        f"/api/v1/referrals/{ref2_id}/links",
        json={"target_referral_id": ref1_id, "link_type": "prior_history", "reason": "Follow-up investigation"},
        headers=caseworker_user["headers"],
    )
    assert link_res.status_code == 201

    # Check prior history on ref2
    hist_res = await client.get(f"/api/v1/referrals/{ref2_id}/history", headers=caseworker_user["headers"])
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["prior_referrals"]) >= 1
    assert hist_data["prior_referrals"][0]["referral_id"] == ref1_id


@pytest.mark.asyncio
async def test_multi_child_disposition_and_supervisor_approval(
    client: AsyncClient, caseworker_user, supervisor_user, db_session: AsyncSession
):
    """
    Test complete multi-child disposition workflow:
    - Child A -> Protection
    - Child B -> Prevention
    - Child C -> Screen Out
    - Worker submits -> Supervisor approves -> Distinct resulting case routing
    """
    # 1. Seed 3 Children
    c1 = Person(first_name="Ava", last_name="Lodge", date_of_birth=date(2016, 1, 1))
    c2 = Person(first_name="Ben", last_name="Lodge", date_of_birth=date(2018, 2, 2))
    c3 = Person(first_name="Cora", last_name="Lodge", date_of_birth=date(2020, 3, 3))
    db_session.add_all([c1, c2, c3])
    await db_session.commit()

    # 2. Create Referral
    ref_res = await client.post(
        "/api/v1/referrals",
        json={
            "received_date": "2026-08-30",
            "summary": "Assessment for 3 siblings.",
            "concerns": [{"concern_type": "neglect", "is_primary": True, "severity": "High"}],
            "people": [
                {"person_id": str(c1.id), "role": "child"},
                {"person_id": str(c2.id), "role": "child"},
                {"person_id": str(c3.id), "role": "child"},
            ],
        },
        headers=caseworker_user["headers"],
    )
    ref_id = ref_res.json()["id"]

    # 3. Worker submits with distinct dispositions for all 3 children
    decision_payload = {
        "overall_recommendation": "Recommend immediate protection investigation for Ava, voluntary prevention for Ben, and screen out for Cora.",
        "rationale": "Ava has acute medical neglect. Ben benefits from prevention counselling. Cora is safely supported by kinship caregiver.",
        "dispositions": [
            {"person_id": str(c1.id), "decision": "PROTECTION", "reason": "Severe medical neglect requires statutory investigation."},
            {"person_id": str(c2.id), "decision": "PREVENTION", "reason": "Voluntary youth wellness and tutoring support."},
            {"person_id": str(c3.id), "decision": "SCREEN_OUT", "reason": "No child welfare safety concerns present."},
        ],
    }

    submit_res = await client.post(
        f"/api/v1/referrals/{ref_id}/submit",
        json=decision_payload,
        headers=caseworker_user["headers"],
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_SUPERVISOR"

    # 4. Supervisor approves
    approve_payload = {"supervisor_notes": "Concur with worker assessment. Approved for routing."}
    approve_res = await client.post(
        f"/api/v1/referrals/{ref_id}/approve",
        json=approve_payload,
        headers=supervisor_user["headers"],
    )
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "APPROVED"

    # 5. Verify resulting cases created
    ref_uuid = uuid.UUID(ref_id)
    cases_res = await db_session.execute(select(Case).where(Case.origin_referral_id == ref_uuid))
    cases = list(cases_res.scalars().all())

    # Exactly 2 cases opened (Protection for Ava, Prevention for Ben; none for Cora)
    assert len(cases) == 2
    case_types = {c.case_type for c in cases}
    assert "Child Safety (Protection)" in case_types
    assert "Family Prevention" in case_types

    # Verify Sacred Timeline Events generated
    timeline_res = await db_session.execute(
        select(TimelineEvent).where(TimelineEvent.entity_id == ref_uuid)
    )
    timeline_events = list(timeline_res.scalars().all())
    event_types = {te.event_type for te in timeline_events}
    assert "REFERRAL_RECEIVED" in event_types
    assert "INTAKE_SUBMITTED" in event_types
    assert "INTAKE_APPROVED" in event_types


@pytest.mark.asyncio
async def test_supervisor_return_workflow(
    client: AsyncClient, caseworker_user, supervisor_user, db_session: AsyncSession
):
    """Test supervisor returning referral with required revision comments, then worker resubmits."""
    p = Person(first_name="Jordan", last_name="Test", date_of_birth=date(2015, 5, 5))
    db_session.add(p)
    await db_session.commit()

    ref_res = await client.post(
        "/api/v1/referrals",
        json={
            "received_date": "2026-08-30",
            "summary": "Test intake for return flow.",
            "concerns": [{"concern_type": "physical_abuse", "is_primary": True}],
            "people": [{"person_id": str(p.id), "role": "child"}],
        },
        headers=caseworker_user["headers"],
    )
    ref_id = ref_res.json()["id"]

    # Submit
    await client.post(
        f"/api/v1/referrals/{ref_id}/submit",
        json={
            "overall_recommendation": "Open protection case",
            "rationale": "Initial review",
            "dispositions": [{"person_id": str(p.id), "decision": "PROTECTION", "reason": "Physical harm"}],
        },
        headers=caseworker_user["headers"],
    )

    # Supervisor returns
    return_res = await client.post(
        f"/api/v1/referrals/{ref_id}/return",
        json={"return_reason": "Please interview the school principal and add collateral information."},
        headers=supervisor_user["headers"],
    )
    assert return_res.status_code == 200
    returned_data = return_res.json()
    assert returned_data["status"] == "RETURNED"
    assert returned_data["decision"]["return_reason"] == "Please interview the school principal and add collateral information."

    # Worker updates and resubmits
    resubmit_res = await client.post(
        f"/api/v1/referrals/{ref_id}/submit",
        json={
            "overall_recommendation": "Open protection case after collateral interview",
            "rationale": "Interviewed principal. Bruising confirmed.",
            "dispositions": [{"person_id": str(p.id), "decision": "PROTECTION", "reason": "Confirmed physical harm"}],
        },
        headers=caseworker_user["headers"],
    )
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "PENDING_SUPERVISOR"


@pytest.mark.asyncio
async def test_it_admin_isolated_from_intake(client: AsyncClient, it_admin_user):
    """Verify IT Admin cannot read or manage intake referrals (strict clinical isolation)."""
    res = await client.get("/api/v1/referrals", headers=it_admin_user["headers"])
    assert res.status_code == 403
