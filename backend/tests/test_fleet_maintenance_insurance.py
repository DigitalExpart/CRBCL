"""Tests for Fleet Maintenance and Insurance Policy Management (Phase 12)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_maintenance_scheduling_and_completion(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test scheduling maintenance, updating vehicle status, completing service, and restoring vehicle availability."""
    headers = caseworker_user["headers"]


    # 1. Create vehicle
    v_data = {
        "vehicle_internal_id": "V-MAINT-101",
        "make": "Chevrolet",
        "model": "Tahoe",
        "year": 2022,
        "licence_plate": "SK-MAINT-101",
        "vehicle_type": "SUV",
        "status": "AVAILABLE",
        "odometer_km": 60000.00,
    }
    v_id = (await client.post("/api/v1/fleet/vehicles", json=v_data, headers=headers)).json()["id"]

    # 2. Schedule Maintenance
    m_data = {
        "vehicle_id": v_id,
        "maintenance_type": "OIL_CHANGE",
        "scheduled_date": str(date.today() + timedelta(days=7)),
        "scheduled_odometer": 65000.00,
        "provider_name": "Regina Fleet Maintenance Inc.",
        "description": "Routine 65,000 km synthetic oil and filter change",
    }
    m_res = await client.post("/api/v1/fleet/maintenance", json=m_data, headers=headers)
    assert m_res.status_code == 201, m_res.text
    m_rec = m_res.json()
    m_id = m_rec["id"]
    assert m_rec["status"] == "SCHEDULED"

    # 3. Complete Maintenance
    comp_data = {
        "completed_date": str(date.today()),
        "completed_odometer": 60100.00,
        "cost": 145.50,
        "notes": "Replaced oil filter and topped fluids.",
    }
    comp_res = await client.put(f"/api/v1/fleet/maintenance/{m_id}/complete", json=comp_data, headers=headers)
    assert comp_res.status_code == 200, comp_res.text
    completed_rec = comp_res.json()
    assert completed_rec["status"] == "COMPLETED"
    assert Decimal(str(completed_rec["cost"])) == Decimal("145.50")



@pytest.mark.asyncio
async def test_insurance_policy_tracking_and_renewals(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test insurance policy creation, expiry updates, and renewal logging."""
    headers = caseworker_user["headers"]


    # 1. Create vehicle
    v_data = {
        "vehicle_internal_id": "V-INS-202",
        "make": "Toyota",
        "model": "Sienna",
        "year": 2024,
        "licence_plate": "SK-INS-202",
        "vehicle_type": "VAN",
        "status": "AVAILABLE",
    }
    v_id = (await client.post("/api/v1/fleet/vehicles", json=v_data, headers=headers)).json()["id"]

    # 2. Log Insurance Policy
    policy_data = {
        "vehicle_id": v_id,
        "provider_name": "Saskatchewan Government Insurance (SGI)",
        "policy_number": "SGI-2026-998877",
        "effective_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=365)),
        "coverage_details": "Comprehensive commercial vehicle fleet auto insurance",
    }
    p_res = await client.post("/api/v1/fleet/insurance", json=policy_data, headers=headers)
    assert p_res.status_code == 201, p_res.text
    policy = p_res.json()
    assert policy["policy_number"] == "SGI-2026-998877"

    # Verify vehicle.insurance_expiry updated
    v_detail = (await client.get(f"/api/v1/fleet/vehicles/{v_id}", headers=headers)).json()["vehicle"]
    assert v_detail["insurance_expiry"] == str(date.today() + timedelta(days=365))
