"""API Router for Office Coordinator operations & operational coordination."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_any_permission
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.operations import (
    OperationsOverviewResponse,
    OperationsRequestCreate,
    OperationsRequestResponse,
    OperationsRequestUpdate,
    RoomBookingCreate,
    RoomBookingResponse,
    SupplyItemCreate,
    SupplyItemResponse,
    SupplyItemUpdate,
    VehicleKeyCheckoutRequest,
    VehicleKeyLogResponse,
    VehicleKeyReturnRequest,
    VehicleReservationCreate,
    VehicleReservationResponse,
    VehicleReservationUpdate,
)
from app.services.dashboard_registry_service import DashboardRegistryService
from app.services.operations_service import OperationsService

router = APIRouter(prefix="/operations", tags=["Office Coordinator Operations"])


async def verify_office_coordinator_enabled(db: AsyncSession = Depends(get_db)) -> None:
    """Enforce server-side workspace availability."""
    registry = DashboardRegistryService(db)
    if not await registry.is_workspace_enabled("office_coordinator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "WORKSPACE_DISABLED", "message": "Office Coordinator workspace is currently disabled by administrative policy."}},
        )


@router.get(
    "/overview",
    response_model=OperationsOverviewResponse,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def get_operations_overview(
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
            Permissions.FLEET_READ,
            Permissions.FACILITIES_READ,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Aggregated status counts for Office Coordinator operational dashboard."""
    service = OperationsService(db)
    return await service.get_overview()


# ── Operations Requests ──────────────────────────────────────
@router.post(
    "/requests",
    response_model=OperationsRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def create_operations_request(
    payload: OperationsRequestCreate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.OPERATIONS_REQUEST_MANAGE,
            Permissions.OPERATIONS_REQUEST_READ,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Submit a centralized operational request or facilities/fleet ticket."""
    service = OperationsService(db)
    created = await service.create_request(payload, requester_id=user.id)
    await db.commit()
    return created


@router.get(
    "/requests",
    response_model=PaginatedResponse[OperationsRequestResponse],
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def list_operations_requests(
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.OPERATIONS_REQUEST_MANAGE,
            Permissions.OPERATIONS_REQUEST_READ,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """List operational tickets with category and status filtering."""
    service = OperationsService(db)
    items, total = await service.list_requests(
        category=category, status_filter=status_filter, offset=offset, limit=limit
    )
    return PaginatedResponse[OperationsRequestResponse](
        items=items,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.patch(
    "/requests/{request_id}",
    response_model=OperationsRequestResponse,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def update_operations_request(
    request_id: uuid.UUID,
    payload: OperationsRequestUpdate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.OPERATIONS_REQUEST_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update operational request assignment, priority, or resolution notes."""
    service = OperationsService(db)
    try:
        updated = await service.update_request(request_id, payload)
        await db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


# ── Vehicle Reservations ─────────────────────────────────────
@router.post(
    "/reservations",
    response_model=VehicleReservationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def create_vehicle_reservation(
    payload: VehicleReservationCreate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_RESERVATION_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create an advance vehicle reservation with time conflict prevention."""
    service = OperationsService(db)
    try:
        reservation = await service.create_reservation(payload, user_id=user.id)
        await db.commit()
        return reservation
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.get(
    "/reservations",
    response_model=PaginatedResponse[VehicleReservationResponse],
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def list_vehicle_reservations(
    vehicle_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_RESERVATION_MANAGE,
            Permissions.FLEET_READ,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """List vehicle reservations ordered by start time."""
    service = OperationsService(db)
    items, total = await service.list_reservations(vehicle_id=vehicle_id, offset=offset, limit=limit)
    return PaginatedResponse[VehicleReservationResponse](
        items=items,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.patch(
    "/reservations/{reservation_id}",
    response_model=VehicleReservationResponse,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def update_vehicle_reservation(
    reservation_id: uuid.UUID,
    payload: VehicleReservationUpdate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_RESERVATION_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Modify reservation status or operational notes."""
    service = OperationsService(db)
    try:
        updated = await service.update_reservation(reservation_id, payload)
        await db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


# ── Vehicle Key Custody Logs ──────────────────────────────────
@router.post(
    "/keys/checkout",
    response_model=VehicleKeyLogResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def checkout_vehicle_key(
    payload: VehicleKeyCheckoutRequest,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_KEY_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Log key custody checkout to an authorized staff recipient."""
    service = OperationsService(db)
    try:
        log = await service.checkout_key(payload, issued_by_id=user.id)
        await db.commit()
        return log
    except ValueError as e:
        status_code = status.HTTP_400_BAD_REQUEST if "already checked out" in str(e) else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=str(e)) from None


@router.post(
    "/keys/{key_log_id}/return",
    response_model=VehicleKeyLogResponse,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def return_vehicle_key(
    key_log_id: uuid.UUID,
    payload: VehicleKeyReturnRequest,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_KEY_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Record key return and restore vehicle key accountability."""
    service = OperationsService(db)
    try:
        log = await service.return_key(key_log_id, notes=payload.notes)
        await db.commit()
        return log
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.get(
    "/keys",
    response_model=PaginatedResponse[VehicleKeyLogResponse],
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def list_vehicle_key_logs(
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.FLEET_KEY_MANAGE,
            Permissions.FLEET_READ,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """List vehicle key custody log records."""
    service = OperationsService(db)
    items, total = await service.list_key_logs(status_filter=status_filter, offset=offset, limit=limit)
    return PaginatedResponse[VehicleKeyLogResponse](
        items=items,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


# ── Room Bookings ────────────────────────────────────────────
@router.post(
    "/rooms",
    response_model=RoomBookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def create_room_booking(
    payload: RoomBookingCreate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.ROOM_BOOKING_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Book a meeting room or facility space with double-booking prevention."""
    service = OperationsService(db)
    try:
        booking = await service.create_room_booking(payload, user_id=user.id)
        await db.commit()
        return booking
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.get(
    "/rooms",
    response_model=PaginatedResponse[RoomBookingResponse],
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def list_room_bookings(
    room_name: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.ROOM_BOOKING_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """List scheduled room bookings."""
    service = OperationsService(db)
    items, total = await service.list_room_bookings(room_name=room_name, offset=offset, limit=limit)
    return PaginatedResponse[RoomBookingResponse](
        items=items,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


# ── Supply Items ─────────────────────────────────────────────
@router.post(
    "/supplies",
    response_model=SupplyItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def create_supply_item(
    payload: SupplyItemCreate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.SUPPLY_INVENTORY_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Add a new inventory supply item."""
    service = OperationsService(db)
    item = await service.create_supply_item(payload)
    await db.commit()
    return item


@router.patch(
    "/supplies/{item_id}",
    response_model=SupplyItemResponse,
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def update_supply_item(
    item_id: uuid.UUID,
    payload: SupplyItemUpdate,
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.SUPPLY_INVENTORY_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update inventory quantity or threshold."""
    service = OperationsService(db)
    try:
        updated = await service.update_supply_item(item_id, payload)
        await db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None


@router.get(
    "/supplies",
    response_model=PaginatedResponse[SupplyItemResponse],
    dependencies=[Depends(verify_office_coordinator_enabled)],
)
async def list_supply_items(
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    user: User = Depends(
        require_any_permission(
            Permissions.OFFICE_COORDINATOR_DASHBOARD_READ,
            Permissions.SUPPLY_INVENTORY_MANAGE,
            Permissions.ADMIN_CONFIGURATION_MANAGE,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """List supplies inventory items."""
    service = OperationsService(db)
    items, total = await service.list_supply_items(
        category=category, status_filter=status_filter, offset=offset, limit=limit
    )
    return PaginatedResponse[SupplyItemResponse](
        items=items,
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )
