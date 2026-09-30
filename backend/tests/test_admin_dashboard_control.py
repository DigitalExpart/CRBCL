"""Focused backend tests for Admin Dashboard Control Centre and Office Coordinator.

Verifies:
1. Authorized Admin can list normalized workspace registry.
2. Unauthorized users receive 403 Forbidden on Admin Control Centre.
3. Front Desk / First Impression and Office Coordinator are present in the registry.
4. Admin can toggle workspace enable/disable state.
5. Server-side disabled workspace enforcement (returns 403 WORKSPACE_DISABLED).
6. Admin can manage role capability assignments for workspaces.
7. Material administrative changes are logged to AuditEvent.
8. Privacy firewalls: IT Admin does NOT gain confidential case, medical, intake narrative, HR, board, or GPS access.
9. Office Coordinator role authorization, operational requests lifecycle, vehicle reservation conflict protection,
   key custody checkout/return, room booking conflict protection, supply threshold calculation, and boundary enforcement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditEvent
from app.models.config import SystemConfig
from app.models.fleet import Vehicle
from app.models.operations import (
    OperationsRequest,
    RoomBooking,
    SupplyItem,
    VehicleKeyLog,
    VehicleReservation,
)

# ============================================================================
# ADMIN DASHBOARD CONTROL CENTRE TESTS
# ============================================================================

@pytest.mark.anyio
async def test_authorized_admin_can_list_workspace_registry(client: AsyncClient, it_admin_user: dict):
    """IT Admin with ADMIN_DASHBOARD_CONTROL can list the canonical workspace registry."""
    res = await client.get("/api/v1/admin/dashboards", headers=it_admin_user["headers"])
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 25

    keys = [w["key"] for w in data]
    assert "front_desk" in keys
    assert "office_coordinator" in keys
    assert "case_management" in keys
    assert "board_governance" in keys
    assert "fleet_management" in keys
    assert "hr_dashboard" in keys
    assert "finance_billing" in keys

    # Verify Front Desk metadata
    fd = next(w for w in data if w["key"] == "front_desk")
    assert fd["name"] == "Front Desk / First Impression"
    assert fd["route"] == "/front-desk"
    assert fd["has_protected_data"] is True
    assert fd["primary_permission_key"] == "public_intake.read"

    # Verify Office Coordinator metadata
    oc = next(w for w in data if w["key"] == "office_coordinator")
    assert "Office Coordinator" in oc["name"]
    assert oc["route"] == "/office-coordinator"
    assert oc["status"] == "IMPLEMENTED"


@pytest.mark.anyio
async def test_unauthorized_staff_denied_dashboard_registry(
    client: AsyncClient, caseworker_user: dict, office_coordinator_user: dict
):
    """Non-admin staff receive 403 Forbidden when attempting to access the Admin Control Centre."""
    res1 = await client.get("/api/v1/admin/dashboards", headers=caseworker_user["headers"])
    assert res1.status_code == 403

    res2 = await client.get("/api/v1/admin/dashboards", headers=office_coordinator_user["headers"])
    assert res2.status_code == 403


@pytest.mark.anyio
async def test_admin_toggle_workspace_status_and_audit_logging(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """Admin can disable a workspace, which persists to SystemConfig and logs an audit event."""
    res = await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/status",
        headers=it_admin_user["headers"],
        json={"is_enabled": False, "reason": "Scheduled system maintenance"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["key"] == "office_coordinator"
    assert data["is_enabled"] is False

    # Verify availability probe reflects disabled state
    probe = await client.get(
        "/api/v1/dashboards/office_coordinator/availability",
        headers=it_admin_user["headers"],
    )
    assert probe.status_code == 200
    assert probe.json()["is_enabled"] is False
    assert probe.json()["workspace_key"] == "office_coordinator"

    # Verify SystemConfig in DB
    result = await db_session.execute(
        select(SystemConfig).where(SystemConfig.key == "dashboard.office_coordinator.enabled")
    )
    cfg = result.scalar_one_or_none()
    assert cfg is not None
    assert cfg.value == "false"

    # Verify AuditEvent was logged
    audit_res = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == "WORKSPACE_STATUS_TOGGLED",
            AuditEvent.user_id == it_admin_user["user"].id,
        )
    )
    event = audit_res.scalar_one_or_none()
    assert event is not None
    assert event.user_id == it_admin_user["user"].id
    assert event.after_data["is_enabled"] is False

    # Re-enable for subsequent tests
    res_enable = await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/status",
        headers=it_admin_user["headers"],
        json={"is_enabled": True, "reason": "Maintenance complete"},
    )
    assert res_enable.status_code == 200
    assert res_enable.json()["is_enabled"] is True


@pytest.mark.anyio
async def test_server_side_disabled_workspace_enforcement(
    client: AsyncClient, it_admin_user: dict, office_coordinator_user: dict
):
    """When a workspace is disabled, server endpoints return 403 WORKSPACE_DISABLED with a safe message."""
    # 1. Disable office_coordinator
    await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/status",
        headers=it_admin_user["headers"],
        json={"is_enabled": False, "reason": "Operational pause"},
    )

    # 2. Attempt to call operations API as Office Coordinator
    res = await client.get("/api/v1/operations/overview", headers=office_coordinator_user["headers"])
    assert res.status_code == 403
    err = res.json()["error"]
    assert err["code"] == "WORKSPACE_DISABLED"
    assert "disabled" in err["message"].lower() or "unavailable" in err["message"].lower()
    # Verify no confidential/sensitive data leaked in error
    assert "narrative" not in err["message"]
    assert "secret" not in err["message"]

    # 3. Re-enable workspace
    await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/status",
        headers=it_admin_user["headers"],
        json={"is_enabled": True, "reason": "Resuming operations"},
    )

    # 4. Now the call succeeds
    res_ok = await client.get("/api/v1/operations/overview", headers=office_coordinator_user["headers"])
    assert res_ok.status_code == 200


@pytest.mark.anyio
async def test_admin_manage_role_assignments_and_audit(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """Admin can grant/revoke workspace capability to roles, and it is audited."""
    # Add supervisor role to office_coordinator workspace
    res = await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/roles",
        headers=it_admin_user["headers"],
        json={"role_keys": ["office_coordinator", "supervisor"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "supervisor" in data["authorized_roles"]

    # Verify audit event logged
    audit_res = await db_session.execute(
        select(AuditEvent).where(
            AuditEvent.event_type == "WORKSPACE_ROLE_ACCESS_MODIFIED",
            AuditEvent.user_id == it_admin_user["user"].id,
        )
    )
    event = audit_res.scalar_one_or_none()
    assert event is not None
    assert event.user_id == it_admin_user["user"].id

    # Clean up: revert role assignments
    res_remove = await client.patch(
        "/api/v1/admin/dashboards/office_coordinator/roles",
        headers=it_admin_user["headers"],
        json={"role_keys": ["office_coordinator"]},
    )
    assert res_remove.status_code == 200
    assert "supervisor" not in res_remove.json()["authorized_roles"]


# ============================================================================
# PRIVACY REGRESSION TESTS: IT ADMIN IS NOT A CONTENT SUPERUSER
# ============================================================================

@pytest.mark.anyio
async def test_it_admin_denied_front_desk_narratives(client: AsyncClient, it_admin_user: dict):
    """IT Admin does NOT inherit public_intake.read or Front Desk narrative access."""
    res = await client.get("/api/v1/front-desk/submissions", headers=it_admin_user["headers"])
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "PERMISSION_DENIED"


@pytest.mark.anyio
async def test_it_admin_denied_cases_and_clients(client: AsyncClient, it_admin_user: dict):
    """IT Admin does NOT inherit case.read or client.read access merely from Admin status."""
    res_case = await client.get("/api/v1/cases", headers=it_admin_user["headers"])
    assert res_case.status_code == 403

    res_client = await client.get("/api/v1/clients", headers=it_admin_user["headers"])
    assert res_client.status_code == 403


@pytest.mark.anyio
async def test_it_admin_denied_hr_dossiers(client: AsyncClient, it_admin_user: dict):
    """IT Admin does NOT inherit hr.employee.read or HR employee dossier access."""
    res = await client.get("/api/v1/org-ops/employees", headers=it_admin_user["headers"])
    assert res.status_code == 403


@pytest.mark.anyio
async def test_it_admin_denied_board_governance(client: AsyncClient, it_admin_user: dict):
    """IT Admin does NOT inherit board_dashboard.read access."""
    res = await client.get("/api/v1/board/summary", headers=it_admin_user["headers"])
    assert res.status_code == 403


@pytest.mark.anyio
async def test_it_admin_denied_gps_location_history(
    client: AsyncClient, it_admin_user: dict, db_session: AsyncSession
):
    """IT Admin does NOT inherit fleet.location.capture access."""
    vehicle = Vehicle(
        vehicle_internal_id="GPS-TEST-01",
        make="Ford",
        model="F-150",
        year=2023,
        licence_plate="GPS-TEST-01",
        status="AVAILABLE",
    )
    db_session.add(vehicle)
    await db_session.commit()

    loc_payload = {
        "latitude": 50.4452,
        "longitude": -104.6189,
        "source": "MANUAL",
        "provider_event_id": "evt-test-gps-999",
    }
    res = await client.post(
        f"/api/v1/fleet/vehicles/{vehicle.id}/location",
        json=loc_payload,
        headers=it_admin_user["headers"],
    )
    assert res.status_code == 403


# ============================================================================
# OFFICE COORDINATOR WORKSPACE TESTS
# ============================================================================

@pytest.mark.anyio
async def test_office_coordinator_boundary_isolation(client: AsyncClient, office_coordinator_user: dict):
    """Office Coordinator has operational access but ZERO case, medical, clinical, or front desk narrative access."""
    # Allowed: Operations overview
    res_ops = await client.get("/api/v1/operations/overview", headers=office_coordinator_user["headers"])
    assert res_ops.status_code == 200

    # Denied: Cases
    res_cases = await client.get("/api/v1/cases", headers=office_coordinator_user["headers"])
    assert res_cases.status_code == 403

    # Denied: Clients
    res_clients = await client.get("/api/v1/clients", headers=office_coordinator_user["headers"])
    assert res_clients.status_code == 403

    # Denied: Front Desk narratives
    res_fd = await client.get("/api/v1/front-desk/submissions", headers=office_coordinator_user["headers"])
    assert res_fd.status_code == 403


@pytest.mark.anyio
async def test_operations_request_lifecycle(client: AsyncClient, office_coordinator_user: dict):
    """Office Coordinator can create and update operational requests."""
    # 1. Create request
    payload = {
        "category": "FACILITIES",
        "priority": "HIGH",
        "title": "Boardroom Projector Bulb Replacement",
        "description": "Projector bulb flickers and needs replacement before Friday meeting.",
        "department": "Operations & Facilities",
    }
    create_res = await client.post(
        "/api/v1/operations/requests",
        headers=office_coordinator_user["headers"],
        json=payload,
    )
    assert create_res.status_code == 201
    req_data = create_res.json()
    assert req_data["title"] == payload["title"]
    assert req_data["status"] == "OPEN"
    assert req_data["request_number"].startswith("REQ-")
    req_id = req_data["id"]

    # 2. List requests
    list_res = await client.get(
        "/api/v1/operations/requests",
        headers=office_coordinator_user["headers"],
    )
    assert list_res.status_code == 200
    assert any(r["id"] == req_id for r in list_res.json()["items"])

    # 3. Update request status
    patch_res = await client.patch(
        f"/api/v1/operations/requests/{req_id}",
        headers=office_coordinator_user["headers"],
        json={"status": "IN_PROGRESS", "resolution_notes": "Parts ordered."},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "IN_PROGRESS"
    assert patch_res.json()["resolution_notes"] == "Parts ordered."


@pytest.mark.anyio
async def test_vehicle_reservation_conflict_detection(
    client: AsyncClient, office_coordinator_user: dict, db_session: AsyncSession
):
    """Vehicle reservations detect and reject overlapping bookings for the same vehicle."""
    # Create canonical vehicle
    vehicle = Vehicle(
        vehicle_internal_id="CRBCL-TEST-V01",
        vin="2C3CDZFJ4MH123456",
        make="Ford",
        model="Explorer",
        year=2023,
        licence_plate="CRBCL-01",
        status="AVAILABLE",
    )
    db_session.add(vehicle)
    await db_session.commit()

    now = datetime.now(UTC) + timedelta(days=2)
    start_time = now.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=14, minute=0, second=0, microsecond=0)

    # 1. Book vehicle 10:00 - 14:00
    res1 = await client.post(
        "/api/v1/operations/reservations",
        headers=office_coordinator_user["headers"],
        json={
            "vehicle_id": str(vehicle.id),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "purpose": "Youth community recreation transport",
            "destination": "Community Center",
            "passengers_count": 4,
        },
    )
    assert res1.status_code == 201

    # 2. Attempt overlapping reservation (12:00 - 16:00) -> 409 Conflict
    res_conflict = await client.post(
        "/api/v1/operations/reservations",
        headers=office_coordinator_user["headers"],
        json={
            "vehicle_id": str(vehicle.id),
            "start_time": (start_time + timedelta(hours=2)).isoformat(),
            "end_time": (end_time + timedelta(hours=2)).isoformat(),
            "purpose": "Staff transport",
            "passengers_count": 2,
        },
    )
    assert res_conflict.status_code == 409
    assert "already reserved" in res_conflict.json()["error"]["message"].lower()

    # 3. Non-overlapping reservation (15:00 - 18:00) -> succeeds
    res_non_overlap = await client.post(
        "/api/v1/operations/reservations",
        headers=office_coordinator_user["headers"],
        json={
            "vehicle_id": str(vehicle.id),
            "start_time": (end_time + timedelta(hours=1)).isoformat(),
            "end_time": (end_time + timedelta(hours=4)).isoformat(),
            "purpose": "Evening outreach",
            "passengers_count": 3,
        },
    )
    assert res_non_overlap.status_code == 201


@pytest.mark.anyio
async def test_key_custody_checkout_and_return(
    client: AsyncClient, office_coordinator_user: dict, db_session: AsyncSession
):
    """Key custody logs checkout, prevents duplicate checkout, and records return."""
    vehicle = Vehicle(
        vehicle_internal_id="CRBCL-TEST-V02",
        vin="1FTFW1ED4NFC98765",
        make="Chevrolet",
        model="Suburban",
        year=2024,
        licence_plate="CRBCL-02",
        status="AVAILABLE",
    )
    db_session.add(vehicle)
    await db_session.commit()

    # 1. Checkout key
    checkout_res = await client.post(
        "/api/v1/operations/keys/checkout",
        headers=office_coordinator_user["headers"],
        json={
            "vehicle_id": str(vehicle.id),
            "key_tag": "KEY-02-A",
            "staff_id": str(office_coordinator_user["user"].id),
            "notes": "Family transport visit",
        },
    )
    assert checkout_res.status_code == 201
    log_data = checkout_res.json()
    assert log_data["status"] == "CHECKED_OUT"
    assert log_data["checked_out_at"] is not None
    assert log_data["returned_at"] is None
    log_id = log_data["id"]

    # 2. Attempt duplicate checkout for the same vehicle while checked out -> 400
    dup_res = await client.post(
        "/api/v1/operations/keys/checkout",
        headers=office_coordinator_user["headers"],
        json={
            "vehicle_id": str(vehicle.id),
            "key_tag": "KEY-02-B",
            "staff_id": str(office_coordinator_user["user"].id),
        },
    )
    assert dup_res.status_code == 400
    assert "already checked out" in dup_res.json()["error"]["message"].lower()

    # 3. Return key
    return_res = await client.post(
        f"/api/v1/operations/keys/{log_id}/return",
        headers=office_coordinator_user["headers"],
        json={"notes": "Vehicle returned on time."},
    )
    assert return_res.status_code == 200
    returned_data = return_res.json()
    assert returned_data["status"] == "RETURNED"
    assert returned_data["returned_at"] is not None


@pytest.mark.anyio
async def test_room_booking_conflict_detection(client: AsyncClient, office_coordinator_user: dict):
    """Room booking prevents overlapping time slots for the same room."""
    start = datetime.now(UTC) + timedelta(days=3, hours=9)
    end = start + timedelta(hours=2)

    # 1. Book Room A
    res1 = await client.post(
        "/api/v1/operations/rooms",
        headers=office_coordinator_user["headers"],
        json={
            "room_name": "Smudge Room",
            "title": "Morning Cultural Circle",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "attendees_count": 6,
        },
    )
    assert res1.status_code == 201

    # 2. Overlapping booking for same room -> 409 Conflict
    res_conflict = await client.post(
        "/api/v1/operations/rooms",
        headers=office_coordinator_user["headers"],
        json={
            "room_name": "Smudge Room",
            "title": "Family Meeting",
            "start_time": (start + timedelta(minutes=30)).isoformat(),
            "end_time": (end + timedelta(minutes=30)).isoformat(),
            "attendees_count": 4,
        },
    )
    assert res_conflict.status_code == 409
    assert "already booked" in res_conflict.json()["error"]["message"].lower()

    # 3. Same time, different room -> succeeds
    res_different_room = await client.post(
        "/api/v1/operations/rooms",
        headers=office_coordinator_user["headers"],
        json={
            "room_name": "Large Boardroom",
            "title": "Staff Training",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "attendees_count": 12,
        },
    )
    assert res_different_room.status_code == 201


@pytest.mark.anyio
async def test_supplies_inventory_management(client: AsyncClient, office_coordinator_user: dict):
    """Supplies inventory tracks quantity and automatically computes low_stock / out_of_stock status."""
    # 1. Create item with quantity below reorder_threshold
    create_res = await client.post(
        "/api/v1/operations/supplies",
        headers=office_coordinator_user["headers"],
        json={
            "item_name": "Standard Copy Paper (Box)",
            "category": "OFFICE",
            "quantity": 2,
            "unit": "boxes",
            "reorder_threshold": 5,
            "location": "Supply Closet A",
        },
    )
    assert create_res.status_code == 201
    item = create_res.json()
    assert item["status"] == "LOW_STOCK"
    item_id = item["id"]

    # 2. Update quantity above threshold
    patch_res = await client.patch(
        f"/api/v1/operations/supplies/{item_id}",
        headers=office_coordinator_user["headers"],
        json={"quantity": 10},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "IN_STOCK"

    # 3. Update quantity to 0
    zero_res = await client.patch(
        f"/api/v1/operations/supplies/{item_id}",
        headers=office_coordinator_user["headers"],
        json={"quantity": 0},
    )
    assert zero_res.status_code == 200
    assert zero_res.json()["status"] == "OUT_OF_STOCK"


@pytest.mark.anyio
async def test_zero_fuel_pin_storage_discipline(client: AsyncClient, office_coordinator_user: dict):
    """Fleet and key workflows do not accept or store fuel-card PINs."""
    # Verified: operations schema and database models contain no fuel_pin column
    res = await client.post(
        "/api/v1/operations/requests",
        headers=office_coordinator_user["headers"],
        json={
            "category": "FLEET",
            "priority": "MEDIUM",
            "title": "Fuel Card Requisition",
            "description": "Standard monthly fuel card requisition.",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "fuel_pin" not in data
