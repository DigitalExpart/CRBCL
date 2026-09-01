"""Fleet Management API Router for CRBCL (Phase 12)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.fleet import (
    InsuranceCreate,
    InsuranceResponse,
    LocationRecordRequest,
    LocationResponse,
    MaintenanceCompleteRequest,
    MaintenanceCreate,
    MaintenanceResponse,
    TripCheckinRequest,
    TripCheckoutRequest,
    TripResponse,
    VehicleCreate,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.fleet_service import FleetService

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])


# ── 1. Fleet Dashboard Overview ──────────────────────────────────
@router.get(
    "/dashboard",
    summary="Fetch Fleet operational metrics",
    dependencies=[Depends(require_permission(Permissions.FLEET_READ))],
)
async def get_fleet_dashboard(db: AsyncSession = Depends(get_db)):
    """Aggregate fleet KPIs (Total, Available, In-Use, Maintenance, Insurance Expiring, Active Trips)."""
    return await FleetService.get_fleet_dashboard_metrics(db)


# ── 2. Vehicles Directory & Lifecycle ────────────────────────────
@router.get(
    "/vehicles",
    response_model=list[VehicleResponse],
    summary="List agency vehicles",
    dependencies=[Depends(require_permission(Permissions.FLEET_VEHICLE_READ))],
)
async def list_vehicles(
    status: str | None = Query(None, description="Filter by status (AVAILABLE, IN_USE, etc.)"),
    vehicle_type: str | None = Query(None, description="Filter by vehicle type (CAR, VAN, SUV, etc.)"),
    search: str | None = Query(None, description="Search plate, internal ID, make, or model"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve filterable directory of agency vehicles."""
    return await FleetService.get_vehicles(
        db, status_filter=status, vehicle_type=vehicle_type, search=search, limit=limit, offset=offset
    )


@router.post(
    "/vehicles",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new vehicle",
    dependencies=[Depends(require_permission(Permissions.FLEET_VEHICLE_CREATE))],
)
async def create_vehicle(payload: VehicleCreate, db: AsyncSession = Depends(get_db)):
    """Register a new vehicle asset into the agency fleet."""
    return await FleetService.create_vehicle(db, payload.model_dump())


@router.get(
    "/vehicles/{vehicle_id}",
    summary="Get vehicle detail profile",
    dependencies=[Depends(require_permission(Permissions.FLEET_VEHICLE_READ))],
)
async def get_vehicle_detail(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch complete vehicle profile with last known location and stale location indicator."""
    return await FleetService.get_vehicle_detail(db, vehicle_id)


@router.put(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle details",
    dependencies=[Depends(require_permission(Permissions.FLEET_VEHICLE_UPDATE))],
)
async def update_vehicle(vehicle_id: uuid.UUID, payload: VehicleUpdate, db: AsyncSession = Depends(get_db)):
    """Update vehicle specifications or parameters."""
    return await FleetService.update_vehicle(db, vehicle_id, payload.model_dump(exclude_unset=True))


@router.delete(
    "/vehicles/{vehicle_id}/archive",
    response_model=VehicleResponse,
    summary="Archive vehicle",
    dependencies=[Depends(require_permission(Permissions.FLEET_VEHICLE_ARCHIVE))],
)
async def archive_vehicle(vehicle_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Soft-delete vehicle, marking status RETIRED while preserving full history."""
    return await FleetService.archive_vehicle(db, vehicle_id)


# ── 3. Check-Out & Check-In Lifecycles ───────────────────────────
@router.post(
    "/vehicles/{vehicle_id}/checkout",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check out a vehicle for a trip",
    dependencies=[Depends(require_permission(Permissions.FLEET_TRIP_CHECKOUT))],
)
async def checkout_vehicle(vehicle_id: uuid.UUID, payload: TripCheckoutRequest, db: AsyncSession = Depends(get_db)):
    """Check out a vehicle with PostgreSQL atomic concurrency protection (HTTP 409 Conflict on double checkout)."""
    return await FleetService.checkout_vehicle(db, vehicle_id, payload.model_dump())


@router.post(
    "/trips/{trip_id}/checkin",
    response_model=TripResponse,
    summary="Check in a vehicle",
    dependencies=[Depends(require_permission(Permissions.FLEET_TRIP_CHECKIN))],
)
async def checkin_vehicle(trip_id: uuid.UUID, payload: TripCheckinRequest, db: AsyncSession = Depends(get_db)):
    """Check in a vehicle, verifying odometer monotonicity and updating vehicle mileage."""
    return await FleetService.checkin_vehicle(db, trip_id, payload.model_dump())


# ── 4. Maintenance & Insurance ───────────────────────────────────
@router.post(
    "/maintenance",
    response_model=MaintenanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule maintenance",
    dependencies=[Depends(require_permission(Permissions.FLEET_MAINTENANCE_MANAGE))],
)
async def schedule_maintenance(payload: MaintenanceCreate, db: AsyncSession = Depends(get_db)):
    """Schedule preventive or corrective vehicle maintenance."""
    return await FleetService.schedule_maintenance(db, payload.model_dump())


@router.put(
    "/maintenance/{maintenance_id}/complete",
    response_model=MaintenanceResponse,
    summary="Complete maintenance",
    dependencies=[Depends(require_permission(Permissions.FLEET_MAINTENANCE_MANAGE))],
)
async def complete_maintenance(
    maintenance_id: uuid.UUID, payload: MaintenanceCompleteRequest, db: AsyncSession = Depends(get_db)
):
    """Mark maintenance completed and restore vehicle to AVAILABLE."""
    return await FleetService.complete_maintenance(db, maintenance_id, payload.model_dump(exclude_unset=True))


@router.post(
    "/insurance",
    response_model=InsuranceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log insurance policy",
    dependencies=[Depends(require_permission(Permissions.FLEET_INSURANCE_MANAGE))],
)
async def create_insurance_policy(payload: InsuranceCreate, db: AsyncSession = Depends(get_db)):
    """Log or renew a vehicle insurance policy."""
    return await FleetService.create_insurance_policy(db, payload.model_dump())


# ── 5. Location Privacy & Geofences ──────────────────────────────
@router.post(
    "/vehicles/{vehicle_id}/location",
    response_model=LocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record vehicle location ping",
    dependencies=[Depends(require_permission(Permissions.FLEET_LOCATION_CAPTURE))],
)
async def record_vehicle_location(
    vehicle_id: uuid.UUID, payload: LocationRecordRequest, db: AsyncSession = Depends(get_db)
):
    """Record manual or browser GPS coordinates for a vehicle."""
    data = payload.model_dump()
    data["vehicle_id"] = vehicle_id
    return await FleetService.record_vehicle_location(db, data)
