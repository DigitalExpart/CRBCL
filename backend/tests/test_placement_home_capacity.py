"""Concurrency, capacity integrity, respite preservation, discharge release, and privacy redaction tests."""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseRestriction
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome


@pytest.mark.asyncio
async def test_placement_home_capacity_and_overbooking_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test that Placement Home capacity limits are strictly enforced and overbooking returns 409 Conflict."""
    headers = caseworker_user["headers"]

    # 1. Setup: Home with capacity = 1
    home = PlacementHome(
        home_code=f"PH-CAP-{uuid.uuid4().hex[:6]}",
        name="Little Bear Kinship Home",
        home_type="KINSHIP",
        total_capacity=1,
        status="ACTIVE",
        city="Regina",
    )
    # Child 1 & Child 2
    child_1 = Person(first_name="Tommy", last_name="Bear", date_of_birth=date(2018, 2, 10))
    child_2 = Person(first_name="Sarah", last_name="Bear", date_of_birth=date(2020, 6, 15))
    case = Case(case_number=f"CASE-{uuid.uuid4().hex[:6]}", title="Bear Family Case", status="OPEN")
    db_session.add_all([home, child_1, child_2, case])
    await db_session.flush()

    # 2. Place Child 1 into Home -> Should Succeed (Occupancy 0 -> 1)
    p1_payload = {
        "child_id": str(child_1.id),
        "placement_home_id": str(home.id),
        "placement_type": "KINSHIP",
        "start_date": str(date.today()),
        "provider_name": "Little Bear Kinship Home",
    }
    res1 = await client.post(f"/api/v1/cases/{case.id}/placements", headers=headers, json=p1_payload)
    assert res1.status_code == 201, res1.text

    # Verify home occupancy is now 1 and available beds is 0
    detail_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_res.status_code == 200
    home_data = detail_res.json()
    assert home_data["occupied_beds"] == 1
    assert home_data["available_beds"] == 0

    # 3. Attempt to place Child 2 into same Home -> Should return 409 Conflict
    p2_payload = {
        "child_id": str(child_2.id),
        "placement_home_id": str(home.id),
        "placement_type": "KINSHIP",
        "start_date": str(date.today()),
        "provider_name": "Little Bear Kinship Home",
    }
    res2 = await client.post(f"/api/v1/cases/{case.id}/placements", headers=headers, json=p2_payload)
    assert res2.status_code == 409, res2.text
    err_body = res2.json()
    msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "full capacity" in msg.lower()


@pytest.mark.asyncio
async def test_capacity_released_on_discharge(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    supervisor_user: dict,
):
    """Test that discharging a child from a placement episode automatically restores home capacity."""
    headers = caseworker_user["headers"]
    sup_headers = supervisor_user["headers"]

    home = PlacementHome(
        home_code=f"PH-DIS-{uuid.uuid4().hex[:6]}",
        name="Morning Star Family Home",
        home_type="LICENSED_FOSTER",
        total_capacity=1,
        status="ACTIVE",
        city="Regina",
    )
    child = Person(first_name="Dante", last_name="Lavallee", date_of_birth=date(2017, 1, 1))
    case = Case(case_number=f"CASE-{uuid.uuid4().hex[:6]}", title="Lavallee Family", status="OPEN")
    db_session.add_all([home, child, case])
    await db_session.flush()

    # 1. Place Child
    p_res = await client.post(
        f"/api/v1/cases/{case.id}/placements",
        headers=headers,
        json={
            "child_id": str(child.id),
            "placement_home_id": str(home.id),
            "placement_type": "FOSTER_HOME",
            "start_date": str(date.today() - timedelta(days=30)),
        },
    )
    assert p_res.status_code == 201, p_res.text
    placement_id = p_res.json()["id"]

    # Verify home occupancy = 1
    detail_before = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_before.json()["occupied_beds"] == 1
    assert detail_before.json()["available_beds"] == 0

    # 2. Discharge Placement (Route is /placements/{id}/discharge)
    discharge_payload = {
        "discharge_date": str(date.today()),
        "discharge_type": "REUNIFICATION",
        "destination_name": "Parental Home (Lavallee)",
        "destination_relationship": "Biological Parents",
        "post_discharge_supervision_plan": "Bi-weekly wellness check-ins for 6 months.",
        "notes": "Reunited safely with biological parents under family safety plan.",
    }
    d_res = await client.post(f"/api/v1/placements/{placement_id}/discharge", headers=sup_headers, json=discharge_payload)
    assert d_res.status_code == 201, d_res.text


    # Verify home occupancy is now 0 and available beds is restored to 1
    detail_after = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_after.json()["occupied_beds"] == 0
    assert detail_after.json()["available_beds"] == 1


@pytest.mark.asyncio
async def test_respite_does_not_double_consume_or_release_primary_capacity(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test that a temporary respite stay does not alter the primary placement home's bed occupancy."""
    headers = caseworker_user["headers"]

    home = PlacementHome(
        home_code=f"PH-RESP-{uuid.uuid4().hex[:6]}",
        name="Thunderbird Foster Home",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
        status="ACTIVE",
        city="Regina",
    )
    child = Person(first_name="Jacob", last_name="Acoose", date_of_birth=date(2019, 4, 10))
    case = Case(case_number=f"CASE-{uuid.uuid4().hex[:6]}", title="Acoose Family Case", status="OPEN")
    db_session.add_all([home, child, case])
    await db_session.flush()

    # 1. Place Child
    p_res = await client.post(
        f"/api/v1/cases/{case.id}/placements",
        headers=headers,
        json={
            "child_id": str(child.id),
            "placement_home_id": str(home.id),
            "placement_type": "FOSTER_HOME",
            "start_date": str(date.today() - timedelta(days=10)),
        },
    )
    assert p_res.status_code == 201, p_res.text
    placement_id = p_res.json()["id"]

    # Verify occupancy = 1
    assert (await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)).json()["occupied_beds"] == 1

    # 2. Schedule Respite Stay (e.g. weekend relief)
    r_res = await client.post(
        f"/api/v1/placements/{placement_id}/respite",
        headers=headers,
        json={
            "respite_provider_name": "Auntie Brenda Respite",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=2)),
            "reason": "Caregiver medical respite",
        },
    )
    assert r_res.status_code == 201, r_res.text

    # Verify primary home occupancy remains 1 (bed remains reserved for the child)
    assert (await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)).json()["occupied_beds"] == 1


@pytest.mark.asyncio
async def test_placement_history_case_privacy_redaction(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test that historical placements redact child & case identity when the user has an active case conflict restriction."""
    headers = caseworker_user["headers"]
    user_id = caseworker_user["user"].id

    # 1. Setup Home, 2 Children on 2 separate Cases
    home = PlacementHome(
        home_code=f"PH-RED-{uuid.uuid4().hex[:6]}",
        name="Whispering Pines Care Facility",
        home_type="FACILITY",
        total_capacity=5,
        city="Regina",
    )
    child_open = Person(first_name="Michael", last_name="Stone", date_of_birth=date(2015, 3, 1))
    case_open = Case(case_number=f"CASE-OPEN-{uuid.uuid4().hex[:4]}", title="Stone Family", status="OPEN")

    child_restricted = Person(first_name="Kylie", last_name="Confidential", date_of_birth=date(2016, 7, 7))
    case_restricted = Case(case_number=f"CASE-RESTR-{uuid.uuid4().hex[:4]}", title="Confidential High Profile", status="OPEN")

    db_session.add_all([home, child_open, case_open, child_restricted, case_restricted])
    await db_session.flush()

    # 2. Add Active Placements for both
    ep1 = PlacementEpisode(
        case_id=case_open.id,
        child_id=child_open.id,
        placement_home_id=home.id,
        placement_type="GROUP_HOME",
        provider_name="Whispering Pines Care Facility",
        start_date=date.today() - timedelta(days=60),
        status="ACTIVE",
    )
    ep2 = PlacementEpisode(
        case_id=case_restricted.id,
        child_id=child_restricted.id,
        placement_home_id=home.id,
        placement_type="GROUP_HOME",
        provider_name="Whispering Pines Care Facility",
        start_date=date.today() - timedelta(days=30),
        status="ACTIVE",
    )
    db_session.add_all([ep1, ep2])
    await db_session.flush()

    # 3. Apply Case Restriction against caseworker_user on case_restricted
    restriction = CaseRestriction(
        case_id=case_restricted.id,
        user_id=user_id,
        reason="Conflict of interest: Worker is related to family member.",
        is_active=True,
    )
    db_session.add(restriction)
    await db_session.flush()

    # 4. Fetch Home Placement History as caseworker_user
    hist_res = await client.get(f"/api/v1/placement-homes/{home.id}/placements", headers=headers)
    assert hist_res.status_code == 200, hist_res.text
    history = hist_res.json()
    assert len(history) == 2

    # Open case record: child & case details visible
    open_item = next(h for h in history if h["placement_id"] == str(ep1.id))
    assert open_item["is_redacted"] is False
    assert "Michael Stone" in open_item["child_name"]
    assert open_item["case_number"] == case_open.case_number

    # Restricted case record: child & case details MUST BE REDACTED
    restr_item = next(h for h in history if h["placement_id"] == str(ep2.id))
    assert restr_item["is_redacted"] is True
    assert "[RESTRICTED" in restr_item["child_name"]
    assert restr_item["case_number"] == "[CONFIDENTIAL / RESTRICTED]"
    assert restr_item["case_id"] is None
    assert restr_item["child_id"] is None
    assert restr_item["duration_days"] >= 30
