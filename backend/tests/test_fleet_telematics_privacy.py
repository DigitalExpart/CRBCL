"""Tests for Telematics Provider Abstraction, Location Privacy, and Dashboard Metrics (Phase 12)."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.telematics.fake_provider import FakeProvider


@pytest.mark.asyncio
async def test_fake_telematics_provider_feed_and_deduplication(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test FakeProvider telematics feed normalization, location logging, and deduplication."""
    headers = caseworker_user["headers"]

    # 1. Create vehicle
    v_data = {
        "vehicle_internal_id": "V-GPS-303",
        "make": "Ford",
        "model": "F-150",
        "year": 2023,
        "licence_plate": "SK-GPS-303",
        "vehicle_type": "TRUCK",
        "status": "AVAILABLE",
    }
    v_id = (await client.post("/api/v1/fleet/vehicles", json=v_data, headers=headers)).json()["id"]

    # 2. Test FakeProvider direct query
    fake_prov = FakeProvider()
    latest_ping = await fake_prov.get_latest_location("V-GPS-303")
    assert latest_ping is not None
    assert latest_ping.latitude == 50.4452
    assert latest_ping.longitude == -104.6189

    # 3. Log location via API
    loc_payload = {
        "latitude": 50.4452,
        "longitude": -104.6189,
        "source": "MANUAL",
        "provider_event_id": "evt-unique-ping-001",
    }
    loc_res = await client.post(f"/api/v1/fleet/vehicles/{v_id}/location", json=loc_payload, headers=headers)
    assert loc_res.status_code == 201, loc_res.text
    first_ping_id = loc_res.json()["id"]

    # 4. Re-log SAME location ping (deduplication check) -> Should return same location ID without error
    loc_res_dup = await client.post(f"/api/v1/fleet/vehicles/{v_id}/location", json=loc_payload, headers=headers)
    assert loc_res_dup.status_code == 201
    assert loc_res_dup.json()["id"] == first_ping_id


@pytest.mark.asyncio
async def test_fleet_dashboard_metrics_aggregation(
    client: AsyncClient, db_session: AsyncSession, caseworker_user: dict
):
    """Test Fleet Dashboard aggregate KPI counts endpoint."""
    headers = caseworker_user["headers"]

    dash_res = await client.get("/api/v1/fleet/dashboard", headers=headers)
    assert dash_res.status_code == 200, dash_res.text
    metrics = dash_res.json()
    assert "total_vehicles" in metrics
    assert "available_count" in metrics
    assert "in_use_count" in metrics
    assert "maintenance_count" in metrics
    assert "active_trips_count" in metrics
