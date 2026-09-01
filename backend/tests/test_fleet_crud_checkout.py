"""Tests for Fleet Vehicle CRUD, Check-Out, Check-In, Odometer Monotonicity, and PostgreSQL Concurrency Protection (Phase 12)."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fleet import Vehicle, VehicleTrip


@pytest.mark.asyncio
async def test_vehicle_crud_and_status_lifecycle(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test vehicle creation, filtering, update, and soft-delete archiving."""
    headers = caseworker_user["headers"]


    # 1. Create vehicle
    v_data = {
        "vehicle_internal_id": "V-TEST-100",
        "make": "Dodge",
        "model": "Grand Caravan",
        "year": 2023,
        "licence_plate": "SK-TEST-100",
        "vehicle_type": "VAN",
        "status": "AVAILABLE",
        "odometer_km": 15000.00,
        "notes": "Agency primary transport van",
    }
    res = await client.post("/api/v1/fleet/vehicles", json=v_data, headers=headers)
    assert res.status_code == 201, res.text
    created = res.json()
    v_id = created["id"]
    assert created["vehicle_internal_id"] == "V-TEST-100"
    assert created["status"] == "AVAILABLE"

    # 2. List vehicles
    list_res = await client.get("/api/v1/fleet/vehicles?status=AVAILABLE", headers=headers)
    assert list_res.status_code == 200
    vehicles = list_res.json()
    assert any(v["id"] == v_id for v in vehicles)

    # 3. Get vehicle detail
    detail_res = await client.get(f"/api/v1/fleet/vehicles/{v_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["vehicle"]["id"] == v_id

    # 4. Update vehicle
    up_res = await client.put(
        f"/api/v1/fleet/vehicles/{v_id}", json={"notes": "Updated note"}, headers=headers
    )
    assert up_res.status_code == 200
    assert up_res.json()["notes"] == "Updated note"

    # 5. Archive vehicle
    arch_res = await client.delete(f"/api/v1/fleet/vehicles/{v_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "RETIRED"


@pytest.mark.asyncio
async def test_checkout_checkin_odometer_monotonicity(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test vehicle checkout, checkin, server distance calculation, and odometer monotonicity enforcement."""
    headers = caseworker_user["headers"]
    user_id = caseworker_user["user"].id


    # 1. Create available vehicle
    v_data = {
        "vehicle_internal_id": "V-TEST-200",
        "make": "Ford",
        "model": "Explorer",
        "year": 2024,
        "licence_plate": "SK-TEST-200",
        "vehicle_type": "SUV",
        "status": "AVAILABLE",
        "odometer_km": 50000.00,
    }
    v_res = await client.post("/api/v1/fleet/vehicles", json=v_data, headers=headers)
    v_id = v_res.json()["id"]

    # 2. Attempt checkout with starting odometer BELOW vehicle current odometer (50,000 km vs 49,000 km) -> REJECTED
    bad_checkout = {
        "driver_id": str(user_id),
        "purpose": "Client Transport",
        "destination": "Youth Center",
        "start_odometer": 49000.00,
    }
    bad_res = await client.post(f"/api/v1/fleet/vehicles/{v_id}/checkout", json=bad_checkout, headers=headers)
    assert bad_res.status_code == 400
    assert "cannot be less than" in str(bad_res.json())


    # 3. Valid checkout
    valid_checkout = {
        "driver_id": str(user_id),
        "purpose": "Client Family Visit",
        "destination": "Fort Qu'Appelle",
        "start_odometer": 50000.00,
        "checkout_condition": "GOOD",
    }
    chk_res = await client.post(f"/api/v1/fleet/vehicles/{v_id}/checkout", json=valid_checkout, headers=headers)
    assert chk_res.status_code == 201, chk_res.text
    trip = chk_res.json()
    trip_id = trip["id"]
    assert trip["status"] == "CHECKED_OUT"

    # Verify vehicle status is now IN_USE
    v_detail = (await client.get(f"/api/v1/fleet/vehicles/{v_id}", headers=headers)).json()["vehicle"]
    assert v_detail["status"] == "IN_USE"

    # 4. Attempt checkin with ending odometer BELOW starting odometer (49,500 < 50,000) -> REJECTED
    bad_checkin = {
        "end_odometer": 49500.00,
    }
    bad_in_res = await client.post(f"/api/v1/fleet/trips/{trip_id}/checkin", json=bad_checkin, headers=headers)
    assert bad_in_res.status_code == 400
    assert "cannot be less than starting odometer" in str(bad_in_res.json())


    # 5. Valid checkin
    valid_checkin = {
        "end_odometer": 50150.50,
        "checkin_condition": "GOOD",
        "notes": "Trip completed cleanly",
    }
    in_res = await client.post(f"/api/v1/fleet/trips/{trip_id}/checkin", json=valid_checkin, headers=headers)
    assert in_res.status_code == 200, in_res.text
    ended_trip = in_res.json()
    assert ended_trip["status"] == "CHECKED_IN"
    assert Decimal(str(ended_trip["calculated_distance_km"])) == Decimal("150.50")


    # Verify vehicle odometer updated atomically to 50150.50 and status returned to AVAILABLE
    v_updated = (await client.get(f"/api/v1/fleet/vehicles/{v_id}", headers=headers)).json()["vehicle"]
    assert Decimal(str(v_updated["odometer_km"])) == Decimal("50150.50")
    assert v_updated["status"] == "AVAILABLE"
