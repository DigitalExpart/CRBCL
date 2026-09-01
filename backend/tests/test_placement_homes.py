"""Unit and integration tests for Placement Homes, Members, Licensing, Visits, Contacts, Assessments & Map."""

import uuid
from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.models.placement_home import PlacementHome, PlacementHomeLicense, PlacementHomeMember
from app.models.user import User


@pytest.mark.asyncio
async def test_placement_home_crud_and_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test creating, fetching, filtering, and updating placement homes."""
    headers = caseworker_user["headers"]

    # 1. Create Placement Home
    create_payload = {
        "name": "Eagle Feather Customary Care Home",
        "home_type": "KINSHIP",
        "status": "ACTIVE",
        "licensing_status": "PENDING",
        "total_capacity": 3,
        "address_line_1": "452 Saulteaux Way",
        "city": "Regina",
        "province": "Saskatchewan",
        "postal_code": "S4P 2M9",
        "community": "Muscowpetung First Nation",
        "latitude": 50.4547,
        "longitude": -104.6067,
        "phone": "306-555-8910",
        "primary_caregiver_name": "Eleanor Desjarlais",
        "intake_criteria_notes": "Kinship customary placement for Treaty 4 children.",
    }

    res = await client.post("/api/v1/placement-homes", headers=headers, json=create_payload)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["name"] == "Eagle Feather Customary Care Home"
    assert data["home_code"].startswith("PH-")
    assert data["total_capacity"] == 3
    assert data["occupied_beds"] == 0
    assert data["available_beds"] == 3
    home_id = data["id"]

    # 2. Get Home Details
    get_res = await client.get(f"/api/v1/placement-homes/{home_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["community"] == "Muscowpetung First Nation"

    # 3. Update Home Attributes
    update_res = await client.patch(
        f"/api/v1/placement-homes/{home_id}",
        headers=headers,
        json={"total_capacity": 4, "licensing_status": "ACTIVE"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["total_capacity"] == 4
    assert updated_data["licensing_status"] == "ACTIVE"
    assert updated_data["available_beds"] == 4

    # 4. Filter Homes
    list_res = await client.get(
        "/api/v1/placement-homes?community=Muscowpetung&home_type=KINSHIP",
        headers=headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(h["id"] == home_id for h in list_data["items"])


@pytest.mark.asyncio
async def test_placement_home_members_management(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test adding, updating, and removing household members."""
    headers = caseworker_user["headers"]

    # 1. Create Home & Person
    home = PlacementHome(
        home_code=f"PH-TEST-{uuid.uuid4().hex[:6]}",
        name="Buffalo Lodge Foster Home",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
        city="Regina",
    )
    person = Person(
        first_name="Gordon",
        last_name="Keewatin",
        date_of_birth=date(1980, 5, 12),
        gender="MALE",
    )
    db_session.add_all([home, person])
    await db_session.flush()

    # 2. Add Member to Home
    member_payload = {
        "person_id": str(person.id),
        "role": "PRIMARY_CAREGIVER",
        "start_date": str(date.today()),
        "is_active": True,
        "notes": "Approved foster parent candidate.",
    }
    res = await client.post(f"/api/v1/placement-homes/{home.id}/members", headers=headers, json=member_payload)
    assert res.status_code == 201, res.text
    m_data = res.json()
    assert m_data["role"] == "PRIMARY_CAREGIVER"
    assert m_data["person_name"] == "Gordon Keewatin"
    member_id = m_data["id"]

    # 3. Update Member Role
    patch_res = await client.patch(
        f"/api/v1/placement-homes/{home.id}/members/{member_id}",
        headers=headers,
        json={"role": "SECONDARY_CAREGIVER", "notes": "Updated role"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["role"] == "SECONDARY_CAREGIVER"

    # 4. Remove Member
    del_res = await client.delete(f"/api/v1/placement-homes/{home.id}/members/{member_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify Detail no longer includes deleted member
    detail_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_res.status_code == 200
    assert len(detail_res.json()["members"]) == 0


@pytest.mark.asyncio
async def test_placement_home_licensing_and_renewal_history(
    client: AsyncClient,
    db_session: AsyncSession,
    supervisor_user: dict,
):
    """Test creating a license and renewing it without destructive overwrite of historical terms."""
    headers = supervisor_user["headers"]

    home = PlacementHome(
        home_code=f"PH-LIC-{uuid.uuid4().hex[:6]}",
        name="Sweetgrass Haven",
        home_type="LICENSED_FOSTER",
        total_capacity=2,
        city="Regina",
    )
    db_session.add(home)
    await db_session.flush()

    today = date.today()
    one_year = today + timedelta(days=365)

    # 1. Create Initial License (License A)
    lic_a_payload = {
        "license_number": "LIC-2025-001",
        "license_type": "PROVISIONAL",
        "status": "ACTIVE",
        "effective_date": str(today - timedelta(days=365)),
        "expiry_date": str(today),
        "issuing_authority": "Ministry of Social Services",
        "max_capacity": 2,
        "conditions": "Provisional license pending CPR recertification.",
    }
    lic_a_res = await client.post(f"/api/v1/placement-homes/{home.id}/licenses", headers=headers, json=lic_a_payload)
    assert lic_a_res.status_code == 201, lic_a_res.text
    lic_a_id = lic_a_res.json()["id"]

    # 2. Renew License (License B)
    renew_payload = {
        "new_license_number": "LIC-2026-002",
        "license_type": "STANDARD_FOSTER",
        "effective_date": str(today),
        "expiry_date": str(one_year),
        "issuing_authority": "Ministry of Social Services",
        "max_capacity": 3,
        "conditions": "Full standard license granted.",
    }
    renew_res = await client.post(
        f"/api/v1/placement-homes/{home.id}/licenses/renew", headers=headers, json=renew_payload
    )
    assert renew_res.status_code == 201, renew_res.text
    lic_b_data = renew_res.json()
    assert lic_b_data["license_number"] == "LIC-2026-002"
    assert lic_b_data["status"] == "ACTIVE"

    # 3. Verify Home Detail retains both historical and current licenses
    detail_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_res.status_code == 200
    home_detail = detail_res.json()
    assert home_detail["total_capacity"] == 3
    assert home_detail["current_license"]["license_number"] == "LIC-2026-002"

    all_licenses = home_detail["licenses"]
    assert len(all_licenses) == 2
    lic_a_retrieved = next(lic for lic in all_licenses if lic["id"] == lic_a_id)
    assert lic_a_retrieved["status"] == "EXPIRED"
    assert lic_a_retrieved["license_number"] == "LIC-2025-001"


@pytest.mark.asyncio
async def test_placement_home_visits_and_contacts(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test logging inspections/visits and contact logs."""
    headers = caseworker_user["headers"]

    home = PlacementHome(
        home_code=f"PH-VST-{uuid.uuid4().hex[:6]}",
        name="Red Willow Sanctuary",
        home_type="THERAPEUTIC",
        total_capacity=4,
        city="Regina",
    )
    person = Person(
        first_name="Clara",
        last_name="Standingready",
        date_of_birth=date(1975, 8, 20),
        gender="FEMALE",
    )
    db_session.add_all([home, person])
    await db_session.flush()

    # 1. Create Visit
    visit_payload = {
        "visit_date": str(date.today()),
        "visit_type": "ROUTINE_INSPECTION",
        "purpose": "Quarterly health, safety, and fire inspection.",
        "summary": "Dwelling is clean, smoke detectors operational, food pantry fully stocked.",
        "observations": "Children have dedicated bedrooms with individual cultural items.",
        "follow_up_required": True,
        "follow_up_due_date": str(date.today() + timedelta(days=14)),
        "status": "COMPLETED",
    }
    v_res = await client.post(f"/api/v1/placement-homes/{home.id}/visits", headers=headers, json=visit_payload)
    assert v_res.status_code == 201, v_res.text
    assert v_res.json()["follow_up_required"] is True

    # 2. Create Contact Log
    contact_payload = {
        "person_id": str(person.id),
        "contact_type": "PHONE",
        "duration_minutes": 25,
        "subject": "Check-in on school supplies and transportation",
        "notes": "Spoke with caregiver regarding specialized busing schedule.",
        "follow_up_action": "Email school district transportation coordinator.",
    }
    c_res = await client.post(f"/api/v1/placement-homes/{home.id}/contact-logs", headers=headers, json=contact_payload)
    assert c_res.status_code == 201, c_res.text
    assert c_res.json()["duration_minutes"] == 25

    # 3. Verify in Home Detail
    detail_res = await client.get(f"/api/v1/placement-homes/{home.id}", headers=headers)
    assert detail_res.status_code == 200
    data = detail_res.json()
    assert len(data["visits"]) == 1
    assert len(data["contact_logs"]) == 1


@pytest.mark.asyncio
async def test_placement_home_map_and_metrics(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Test map endpoint and operational dashboard metrics."""
    headers = caseworker_user["headers"]

    home = PlacementHome(
        home_code=f"PH-MAP-{uuid.uuid4().hex[:6]}",
        name="Wascana Creek Group Home",
        home_type="FACILITY",
        total_capacity=6,
        status="ACTIVE",
        licensing_status="ACTIVE",
        latitude=50.4452,
        longitude=-104.6189,
        city="Regina",
        community="Central",
    )
    db_session.add(home)
    await db_session.flush()

    # 1. Test Map Endpoint
    map_res = await client.get("/api/v1/placement-homes/map", headers=headers)
    assert map_res.status_code == 200
    markers = map_res.json()
    assert isinstance(markers, list)
    target = next((m for m in markers if m["id"] == str(home.id)), None)
    assert target is not None
    assert target["latitude"] == 50.4452
    assert target["longitude"] == -104.6189
    assert target["total_capacity"] == 6

    # 2. Test Metrics Endpoint
    metrics_res = await client.get("/api/v1/placement-homes/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()
    assert metrics["total_homes"] >= 1
    assert metrics["total_beds"] >= 6
    assert "available_beds" in metrics
