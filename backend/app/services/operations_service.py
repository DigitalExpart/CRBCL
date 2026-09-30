"""Service layer for Office Coordinator operations."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fleet import Vehicle
from app.models.operations import (
    OperationsRequest,
    RoomBooking,
    SupplyItem,
    VehicleKeyLog,
    VehicleReservation,
)
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
    VehicleReservationCreate,
    VehicleReservationResponse,
    VehicleReservationUpdate,
)


class OperationsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── 1. Operations Requests ───────────────────────────────────
    async def create_request(self, payload: OperationsRequestCreate, requester_id: uuid.UUID) -> OperationsRequestResponse:
        year_str = str(datetime.now(UTC).year)
        count_res = await self.db.execute(select(func.count(OperationsRequest.id)))
        count = (count_res.scalar_one() or 0) + 1
        req_number = f"REQ-{year_str}-{count:04d}"

        req = OperationsRequest(
            request_number=req_number,
            category=payload.category,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            status="OPEN",
            requester_id=requester_id,
            department=payload.department,
        )
        self.db.add(req)
        await self.db.flush()
        await self.db.refresh(req)
        return self._build_request_response(req)

    async def list_requests(
        self,
        category: str | None = None,
        status_filter: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[OperationsRequestResponse], int]:
        stmt = select(OperationsRequest)
        if category:
            stmt = stmt.where(OperationsRequest.category == category)
        if status_filter:
            stmt = stmt.where(OperationsRequest.status == status_filter)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(OperationsRequest.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return [self._build_request_response(r) for r in res.scalars().all()], total

    async def update_request(self, request_id: uuid.UUID, payload: OperationsRequestUpdate) -> OperationsRequestResponse:
        res = await self.db.execute(select(OperationsRequest).where(OperationsRequest.id == request_id))
        req = res.scalar_one_or_none()
        if not req:
            raise ValueError("Operational request not found")

        if payload.status is not None:
            req.status = payload.status
            if payload.status == "COMPLETED" and not req.resolved_at:
                req.resolved_at = datetime.now(UTC)
        if payload.priority is not None:
            req.priority = payload.priority
        if payload.assigned_to_id is not None:
            req.assigned_to_id = payload.assigned_to_id
        if payload.resolution_notes is not None:
            req.resolution_notes = payload.resolution_notes

        await self.db.flush()
        await self.db.refresh(req)
        return self._build_request_response(req)

    def _build_request_response(self, r: OperationsRequest) -> OperationsRequestResponse:
        return OperationsRequestResponse(
            id=r.id,
            request_number=r.request_number,
            category=r.category,
            title=r.title,
            description=r.description,
            priority=r.priority,
            status=r.status,
            requester_id=r.requester_id,
            requester_name=r.requester.full_name if r.requester else None,
            assigned_to_id=r.assigned_to_id,
            assigned_to_name=r.assigned_to.full_name if r.assigned_to else None,
            department=r.department,
            resolution_notes=r.resolution_notes,
            resolved_at=r.resolved_at,
            created_at=r.created_at,
        )

    # ── 2. Vehicle Reservations ──────────────────────────────────
    async def create_reservation(
        self, payload: VehicleReservationCreate, user_id: uuid.UUID
    ) -> VehicleReservationResponse:
        if payload.start_time >= payload.end_time:
            raise ValueError("Start time must be strictly before end time.")

        # Check vehicle existence
        v_res = await self.db.execute(select(Vehicle).where(Vehicle.id == payload.vehicle_id))
        vehicle = v_res.scalar_one_or_none()
        if not vehicle:
            raise ValueError("Vehicle not found.")

        # Conflict check: ensure no overlapping CONFIRMED/CHECKED_OUT reservations
        overlap_stmt = select(VehicleReservation).where(
            VehicleReservation.vehicle_id == payload.vehicle_id,
            VehicleReservation.status.in_(["CONFIRMED", "CHECKED_OUT"]),
            and_(
                VehicleReservation.start_time < payload.end_time,
                VehicleReservation.end_time > payload.start_time,
            ),
        )
        overlap = (await self.db.execute(overlap_stmt)).scalar_one_or_none()
        if overlap:
            raise ValueError("Vehicle is already reserved for the requested time window.")

        res = VehicleReservation(
            vehicle_id=payload.vehicle_id,
            reserved_by_id=user_id,
            start_time=payload.start_time,
            end_time=payload.end_time,
            purpose=payload.purpose,
            destination=payload.destination,
            passengers_count=payload.passengers_count,
            status="CONFIRMED",
            notes=payload.notes,
        )
        self.db.add(res)
        await self.db.flush()
        await self.db.refresh(res)
        return self._build_reservation_response(res)

    async def list_reservations(
        self, vehicle_id: uuid.UUID | None = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[VehicleReservationResponse], int]:
        stmt = select(VehicleReservation)
        if vehicle_id:
            stmt = stmt.where(VehicleReservation.vehicle_id == vehicle_id)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleReservation.start_time.asc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return [self._build_reservation_response(r) for r in res.scalars().all()], total

    async def update_reservation(
        self, reservation_id: uuid.UUID, payload: VehicleReservationUpdate
    ) -> VehicleReservationResponse:
        res = await self.db.execute(select(VehicleReservation).where(VehicleReservation.id == reservation_id))
        reservation = res.scalar_one_or_none()
        if not reservation:
            raise ValueError("Reservation not found.")

        if payload.status:
            reservation.status = payload.status
        if payload.notes is not None:
            reservation.notes = payload.notes

        await self.db.flush()
        await self.db.refresh(reservation)
        return self._build_reservation_response(reservation)

    def _build_reservation_response(self, r: VehicleReservation) -> VehicleReservationResponse:
        v_name = f"{r.vehicle.year} {r.vehicle.make} {r.vehicle.model}" if r.vehicle else None
        return VehicleReservationResponse(
            id=r.id,
            vehicle_id=r.vehicle_id,
            vehicle_name=v_name,
            licence_plate=r.vehicle.licence_plate if r.vehicle else None,
            reserved_by_id=r.reserved_by_id,
            reserved_by_name=r.reserved_by.full_name if r.reserved_by else None,
            start_time=r.start_time,
            end_time=r.end_time,
            purpose=r.purpose,
            destination=r.destination,
            passengers_count=r.passengers_count,
            status=r.status,
            notes=r.notes,
            created_at=r.created_at,
        )

    # ── 3. Vehicle Key Custody Logs ──────────────────────────────
    async def checkout_key(self, payload: VehicleKeyCheckoutRequest, issued_by_id: uuid.UUID) -> VehicleKeyLogResponse:
        v_res = await self.db.execute(select(Vehicle).where(Vehicle.id == payload.vehicle_id))
        if not v_res.scalar_one_or_none():
            raise ValueError("Vehicle not found.")

        # Check if key is already checked out for this vehicle
        active_key = await self.db.execute(
            select(VehicleKeyLog).where(
                VehicleKeyLog.vehicle_id == payload.vehicle_id,
                VehicleKeyLog.status == "CHECKED_OUT",
            )
        )
        if active_key.scalar_one_or_none():
            raise ValueError("Vehicle key is already checked out.")

        log = VehicleKeyLog(
            vehicle_id=payload.vehicle_id,
            key_tag=payload.key_tag,
            staff_id=payload.staff_id,
            issued_by_id=issued_by_id,
            checked_out_at=datetime.now(UTC),
            status="CHECKED_OUT",
            notes=payload.notes,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return self._build_key_log_response(log)

    async def return_key(self, key_log_id: uuid.UUID, notes: str | None = None) -> VehicleKeyLogResponse:
        res = await self.db.execute(select(VehicleKeyLog).where(VehicleKeyLog.id == key_log_id))
        log = res.scalar_one_or_none()
        if not log:
            raise ValueError("Key checkout record not found.")

        log.status = "RETURNED"
        log.returned_at = datetime.now(UTC)
        if notes:
            log.notes = f"{log.notes or ''} | Return: {notes}".strip(" |")

        await self.db.flush()
        await self.db.refresh(log)
        return self._build_key_log_response(log)

    async def list_key_logs(
        self, status_filter: str | None = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[VehicleKeyLogResponse], int]:
        stmt = select(VehicleKeyLog)
        if status_filter:
            stmt = stmt.where(VehicleKeyLog.status == status_filter)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(VehicleKeyLog.checked_out_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return [self._build_key_log_response(r) for r in res.scalars().all()], total

    def _build_key_log_response(self, r: VehicleKeyLog) -> VehicleKeyLogResponse:
        v_name = f"{r.vehicle.year} {r.vehicle.make} {r.vehicle.model}" if r.vehicle else None
        return VehicleKeyLogResponse(
            id=r.id,
            vehicle_id=r.vehicle_id,
            vehicle_name=v_name,
            key_tag=r.key_tag,
            staff_id=r.staff_id,
            staff_name=r.staff.full_name if r.staff else None,
            issued_by_id=r.issued_by_id,
            issued_by_name=r.issued_by.full_name if r.issued_by else None,
            checked_out_at=r.checked_out_at,
            returned_at=r.returned_at,
            status=r.status,
            notes=r.notes,
        )

    # ── 4. Room Bookings ─────────────────────────────────────────
    async def create_room_booking(self, payload: RoomBookingCreate, user_id: uuid.UUID) -> RoomBookingResponse:
        if payload.start_time >= payload.end_time:
            raise ValueError("Start time must be strictly before end time.")

        # Conflict check for room
        overlap_stmt = select(RoomBooking).where(
            RoomBooking.room_name == payload.room_name,
            RoomBooking.status == "CONFIRMED",
            and_(
                RoomBooking.start_time < payload.end_time,
                RoomBooking.end_time > payload.start_time,
            ),
        )
        overlap = (await self.db.execute(overlap_stmt)).scalar_one_or_none()
        if overlap:
            raise ValueError(f"Room '{payload.room_name}' is already booked for the requested time window.")

        booking = RoomBooking(
            room_name=payload.room_name,
            booked_by_id=user_id,
            title=payload.title,
            start_time=payload.start_time,
            end_time=payload.end_time,
            attendees_count=payload.attendees_count,
            status="CONFIRMED",
            notes=payload.notes,
        )
        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)
        return self._build_room_booking_response(booking)

    async def list_room_bookings(
        self, room_name: str | None = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[RoomBookingResponse], int]:
        stmt = select(RoomBooking)
        if room_name:
            stmt = stmt.where(RoomBooking.room_name == room_name)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(RoomBooking.start_time.asc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return [self._build_room_booking_response(r) for r in res.scalars().all()], total

    def _build_room_booking_response(self, r: RoomBooking) -> RoomBookingResponse:
        return RoomBookingResponse(
            id=r.id,
            room_name=r.room_name,
            booked_by_id=r.booked_by_id,
            booked_by_name=r.booked_by.full_name if r.booked_by else None,
            title=r.title,
            start_time=r.start_time,
            end_time=r.end_time,
            attendees_count=r.attendees_count,
            status=r.status,
            notes=r.notes,
            created_at=r.created_at,
        )

    # ── 5. Supplies Inventory ────────────────────────────────────
    async def create_supply_item(self, payload: SupplyItemCreate) -> SupplyItemResponse:
        status_val = self._calc_supply_status(payload.quantity, payload.reorder_threshold)
        item = SupplyItem(
            item_name=payload.item_name,
            category=payload.category,
            quantity=payload.quantity,
            unit=payload.unit,
            location=payload.location,
            reorder_threshold=payload.reorder_threshold,
            status=status_val,
            notes=payload.notes,
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return self._build_supply_response(item)

    async def update_supply_item(self, item_id: uuid.UUID, payload: SupplyItemUpdate) -> SupplyItemResponse:
        res = await self.db.execute(select(SupplyItem).where(SupplyItem.id == item_id))
        item = res.scalar_one_or_none()
        if not item:
            raise ValueError("Supply item not found.")

        if payload.quantity is not None:
            item.quantity = payload.quantity
        if payload.location is not None:
            item.location = payload.location
        if payload.reorder_threshold is not None:
            item.reorder_threshold = payload.reorder_threshold
        if payload.notes is not None:
            item.notes = payload.notes

        item.status = self._calc_supply_status(item.quantity, item.reorder_threshold)
        await self.db.flush()
        await self.db.refresh(item)
        return self._build_supply_response(item)

    async def list_supply_items(
        self, category: str | None = None, status_filter: str | None = None, offset: int = 0, limit: int = 50
    ) -> tuple[list[SupplyItemResponse], int]:
        stmt = select(SupplyItem)
        if category:
            stmt = stmt.where(SupplyItem.category == category)
        if status_filter:
            stmt = stmt.where(SupplyItem.status == status_filter)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = stmt.order_by(SupplyItem.item_name.asc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        return [self._build_supply_response(r) for r in res.scalars().all()], total

    def _calc_supply_status(self, qty: int, threshold: int) -> str:
        if qty <= 0:
            return "OUT_OF_STOCK"
        if qty <= threshold:
            return "LOW_STOCK"
        return "IN_STOCK"

    def _build_supply_response(self, r: SupplyItem) -> SupplyItemResponse:
        return SupplyItemResponse(
            id=r.id,
            item_name=r.item_name,
            category=r.category,
            quantity=r.quantity,
            unit=r.unit,
            location=r.location,
            reorder_threshold=r.reorder_threshold,
            status=r.status,
            notes=r.notes,
            created_at=r.created_at,
        )

    # ── 6. Overview Aggregates ───────────────────────────────────
    async def get_overview(self) -> OperationsOverviewResponse:
        open_reqs = (
            await self.db.execute(
                select(func.count(OperationsRequest.id)).where(
                    OperationsRequest.status.in_(["OPEN", "IN_PROGRESS", "PENDING_APPROVAL"])
                )
            )
        ).scalar_one() or 0

        active_res = (
            await self.db.execute(
                select(func.count(VehicleReservation.id)).where(
                    VehicleReservation.status.in_(["CONFIRMED", "CHECKED_OUT"])
                )
            )
        ).scalar_one() or 0

        keys_out = (
            await self.db.execute(
                select(func.count(VehicleKeyLog.id)).where(VehicleKeyLog.status == "CHECKED_OUT")
            )
        ).scalar_one() or 0

        avail_vehicles = (
            await self.db.execute(
                select(func.count(Vehicle.id)).where(
                    Vehicle.status == "AVAILABLE", Vehicle.archived_at.is_(None)
                )
            )
        ).scalar_one() or 0

        low_supplies = (
            await self.db.execute(
                select(func.count(SupplyItem.id)).where(SupplyItem.status.in_(["LOW_STOCK", "OUT_OF_STOCK"]))
            )
        ).scalar_one() or 0

        today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now(UTC).replace(hour=23, minute=59, long=59, microsecond=999999) if hasattr(datetime, "long") else datetime.now(UTC).replace(hour=23, minute=59, second=59, microsecond=999999)

        today_rooms = (
            await self.db.execute(
                select(func.count(RoomBooking.id)).where(
                    RoomBooking.status == "CONFIRMED",
                    RoomBooking.start_time >= today_start,
                    RoomBooking.start_time <= today_end,
                )
            )
        ).scalar_one() or 0

        return OperationsOverviewResponse(
            open_requests_count=open_reqs,
            active_reservations_count=active_res,
            keys_checked_out_count=keys_out,
            available_vehicles_count=avail_vehicles,
            low_stock_supplies_count=low_supplies,
            today_room_bookings_count=today_rooms,
        )
