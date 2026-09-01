"""Fleet Domain Service governing vehicle lifecycles, check-out/check-in, odometer integrity, maintenance, insurance, location privacy, and geofencing (Phase 12)."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fleet import (
    Vehicle,
    VehicleInsurancePolicy,
    VehicleLocation,
    VehicleMaintenance,
    VehicleTrip,
)
from app.repositories.fleet_repo import FleetRepository


class FleetService:
    """Service governing Vehicle lifecycle, Check-out / Check-in, OdometerMonotonicity, Telematics & Privacy."""

    # ── 1. Vehicles Directory & Lifecycle ─────────────────────────
    @classmethod
    async def create_vehicle(cls, session: AsyncSession, vehicle_data: dict[str, Any]) -> Vehicle:
        """Register a new vehicle into the agency fleet."""
        # Check internal ID and licence plate uniqueness
        existing_internal = await session.execute(
            select(Vehicle).where(Vehicle.vehicle_internal_id == vehicle_data["vehicle_internal_id"])
        )
        if existing_internal.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vehicle internal ID '{vehicle_data['vehicle_internal_id']}' already exists.",
            )

        existing_plate = await session.execute(
            select(Vehicle).where(Vehicle.licence_plate == vehicle_data["licence_plate"])
        )
        if existing_plate.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Licence plate '{vehicle_data['licence_plate']}' already registered.",
            )

        vehicle_data["status"] = vehicle_data.get("status", "AVAILABLE")
        return await FleetRepository.create_vehicle(session, vehicle_data)

    @classmethod
    async def get_vehicles(
        cls,
        session: AsyncSession,
        status_filter: str | None = None,
        vehicle_type: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Vehicle]:
        """List active vehicles with optional filtering."""
        return await FleetRepository.get_vehicles(
            session,
            status=status_filter,
            vehicle_type=vehicle_type,
            search=search,
            limit=limit,
            offset=offset,
        )

    @classmethod
    async def get_vehicle_detail(cls, session: AsyncSession, vehicle_id: uuid.UUID) -> dict[str, Any]:
        """Fetch full vehicle details with last known location and stale status."""
        v = await FleetRepository.get_vehicle_by_id(session, vehicle_id)
        if not v or v.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle '{vehicle_id}' not found.",
            )

        # Check last known location
        latest_loc = await FleetRepository.get_latest_vehicle_location(session, vehicle_id)
        is_stale = False
        if latest_loc and (datetime.utcnow() - latest_loc.recorded_at).total_seconds() > 3600:
            is_stale = True

        return {
            "vehicle": v,
            "latest_location": latest_loc,
            "is_location_stale": is_stale,
        }

    @classmethod
    async def update_vehicle(cls, session: AsyncSession, vehicle_id: uuid.UUID, update_data: dict[str, Any]) -> Vehicle:
        """Update vehicle parameters."""
        v = await FleetRepository.get_vehicle_by_id(session, vehicle_id)
        if not v or v.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle '{vehicle_id}' not found.",
            )
        await FleetRepository.update_vehicle(session, v, update_data)
        return await FleetRepository.get_vehicle_by_id(session, vehicle_id)

    @classmethod
    async def archive_vehicle(cls, session: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle:
        """Soft-delete vehicle, preserving operational history."""
        v = await FleetRepository.get_vehicle_by_id(session, vehicle_id)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle '{vehicle_id}' not found.",
            )
        # Cannot archive vehicle with an active trip
        active_trip = await FleetRepository.get_active_trip_for_vehicle(session, vehicle_id)
        if active_trip:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot archive vehicle while it has an active checked-out trip.",
            )
        await FleetRepository.archive_vehicle(session, v)
        return await FleetRepository.get_vehicle_by_id(session, vehicle_id)

    # ── 2. Check-Out & Check-In Lifecycles (Concurrency Locking) ──
    @classmethod
    async def checkout_vehicle(
        cls, session: AsyncSession, vehicle_id: uuid.UUID, checkout_data: dict[str, Any]
    ) -> VehicleTrip:
        """Check out a vehicle for a driver trip with atomic PostgreSQL concurrency protection."""
        v = await FleetRepository.get_vehicle_by_id(session, vehicle_id)
        if not v or v.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vehicle '{vehicle_id}' not found.",
            )

        if v.status in ("MAINTENANCE", "OUT_OF_SERVICE", "RETIRED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Vehicle '{v.vehicle_internal_id}' cannot be checked out because it is currently '{v.status}'.",
            )

        if v.status == "IN_USE":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vehicle '{v.vehicle_internal_id}' is already checked out by another driver.",
            )

        # Odometer Integrity Check: start_odometer cannot be less than vehicle current odometer
        start_odo = Decimal(str(checkout_data["start_odometer"]))
        if start_odo < v.odometer_km:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Starting odometer ({start_odo} km) cannot be less than vehicle's current odometer ({v.odometer_km} km).",
            )

        # Build trip payload
        trip_payload = {
            "vehicle_id": vehicle_id,
            "driver_id": checkout_data["driver_id"],
            "case_id": checkout_data.get("case_id"),
            "client_id": checkout_data.get("client_id"),
            "purpose": checkout_data["purpose"],
            "destination": checkout_data["destination"],
            "start_odometer": start_odo,
            "start_time": checkout_data.get("start_time", datetime.utcnow()),
            "status": "CHECKED_OUT",
            "checkout_condition": checkout_data.get("checkout_condition", "GOOD"),
            "notes": checkout_data.get("notes"),
        }

        try:
            trip = await FleetRepository.create_trip(session, trip_payload)
            # Update vehicle status to IN_USE and record current driver
            v.status = "IN_USE"
            v.current_driver_id = checkout_data["driver_id"]
            await session.flush()
            return trip
        except IntegrityError as err:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Vehicle '{v.vehicle_internal_id}' was checked out simultaneously by another user.",
            ) from err

    @classmethod
    async def checkin_vehicle(
        cls, session: AsyncSession, trip_id: uuid.UUID, checkin_data: dict[str, Any]
    ) -> VehicleTrip:
        """Check in a vehicle, verifying odometer monotonicity and updating current mileage."""
        trip = await FleetRepository.get_trip_by_id(session, trip_id)
        if not trip or trip.status != "CHECKED_OUT":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Trip '{trip_id}' is not currently active for check-in.",
            )

        v = await FleetRepository.get_vehicle_by_id(session, trip.vehicle_id)
        if not v:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle for this trip was not found.",
            )

        end_odo = Decimal(str(checkin_data["end_odometer"]))
        if end_odo < trip.start_odometer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ending odometer ({end_odo} km) cannot be less than starting odometer ({trip.start_odometer} km).",
            )

        distance = end_odo - trip.start_odometer

        # Update Trip
        trip.end_odometer = end_odo
        trip.calculated_distance_km = distance
        trip.end_time = checkin_data.get("end_time", datetime.utcnow())
        trip.status = "CHECKED_IN"
        trip.checkin_condition = checkin_data.get("checkin_condition", "GOOD")
        trip.has_damage_flag = checkin_data.get("has_damage_flag", False)
        trip.has_maintenance_issue = checkin_data.get("has_maintenance_issue", False)
        if checkin_data.get("notes"):
            trip.notes = f"{trip.notes or ''}\n[Check-in]: {checkin_data['notes']}".strip()

        # Update Vehicle atomic odometer
        v.odometer_km = end_odo
        v.current_driver_id = None

        if trip.has_maintenance_issue or trip.has_damage_flag:
            v.status = "MAINTENANCE"
        else:
            v.status = "AVAILABLE"

        await session.flush()
        return await FleetRepository.get_trip_by_id(session, trip.id)

    # ── 3. Maintenance Scheduling & History ───────────────────────
    @classmethod
    async def schedule_maintenance(cls, session: AsyncSession, maintenance_data: dict[str, Any]) -> VehicleMaintenance:
        """Schedule preventive or corrective vehicle maintenance."""
        v = await FleetRepository.get_vehicle_by_id(session, maintenance_data["vehicle_id"])
        if not v or v.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found.",
            )

        m = await FleetRepository.create_maintenance(session, maintenance_data)

        # Projection update on vehicle
        if maintenance_data.get("scheduled_date"):
            v.next_maintenance_date = maintenance_data["scheduled_date"]
        if maintenance_data.get("scheduled_odometer"):
            v.next_maintenance_odometer = Decimal(str(maintenance_data["scheduled_odometer"]))

        await session.flush()
        return m

    @classmethod
    async def complete_maintenance(
        cls, session: AsyncSession, maintenance_id: uuid.UUID, completion_data: dict[str, Any]
    ) -> VehicleMaintenance:
        """Mark maintenance completed and return vehicle to AVAILABLE if applicable."""
        res = await session.execute(select(VehicleMaintenance).where(VehicleMaintenance.id == maintenance_id))
        m = res.scalar_one_or_none()
        if not m:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Maintenance record not found.",
            )

        m.status = "COMPLETED"
        m.completed_date = completion_data.get("completed_date", date.today())
        if completion_data.get("completed_odometer"):
            m.completed_odometer = Decimal(str(completion_data["completed_odometer"]))
        if completion_data.get("cost"):
            m.cost = Decimal(str(completion_data["cost"]))

        # Restore vehicle status if currently MAINTENANCE
        v = await FleetRepository.get_vehicle_by_id(session, m.vehicle_id)
        if v and v.status == "MAINTENANCE":
            v.status = "AVAILABLE"

        await session.flush()
        return m

    # ── 4. Insurance Tracking & History ────────────────────────────
    @classmethod
    async def create_insurance_policy(
        cls, session: AsyncSession, policy_data: dict[str, Any]
    ) -> VehicleInsurancePolicy:
        """Log or renew a vehicle insurance policy."""
        v = await FleetRepository.get_vehicle_by_id(session, policy_data["vehicle_id"])
        if not v or v.archived_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vehicle not found.",
            )

        p = await FleetRepository.create_insurance_policy(session, policy_data)
        v.insurance_expiry = policy_data["expiry_date"]
        await session.flush()
        return p

    # ── 5. Location Privacy & Deduplication ───────────────────────
    @classmethod
    async def record_vehicle_location(cls, session: AsyncSession, location_data: dict[str, Any]) -> VehicleLocation:
        """Log a vehicle location ping with deduplication."""
        # Deduplication by provider_event_id
        event_id = location_data.get("provider_event_id")
        if event_id:
            existing_res = await session.execute(
                select(VehicleLocation).where(
                    and_(
                        VehicleLocation.vehicle_id == location_data["vehicle_id"],
                        VehicleLocation.provider_event_id == event_id,
                    )
                )
            )
            existing_loc = existing_res.scalars().first()
            if existing_loc:
                return existing_loc

        if not location_data.get("recorded_at"):
            location_data["recorded_at"] = datetime.utcnow()

        return await FleetRepository.create_location(session, location_data)

    # ── 6. Fleet Dashboard Metrics ────────────────────────────────
    @classmethod
    async def get_fleet_dashboard_metrics(cls, session: AsyncSession) -> dict[str, Any]:
        """Aggregate Fleet operational metrics for dashboard overview."""
        today_date = date.today()
        thirty_days = today_date + timedelta(days=30)

        # Count vehicles by status
        v_res = await session.execute(
            select(Vehicle.status, func.count(Vehicle.id)).where(Vehicle.archived_at.is_(None)).group_by(Vehicle.status)
        )
        status_counts = dict(v_res.all())

        total_vehicles = sum(status_counts.values())
        available_count = status_counts.get("AVAILABLE", 0)
        in_use_count = status_counts.get("IN_USE", 0)
        maintenance_count = status_counts.get("MAINTENANCE", 0)
        out_of_service_count = status_counts.get("OUT_OF_SERVICE", 0)

        # Active trips count
        active_trips_res = await session.execute(
            select(func.count(VehicleTrip.id)).where(VehicleTrip.status == "CHECKED_OUT")
        )
        active_trips_count = active_trips_res.scalar() or 0

        # Insurance expiring < 30 days
        ins_expiring_res = await session.execute(
            select(func.count(Vehicle.id)).where(
                and_(
                    Vehicle.archived_at.is_(None),
                    Vehicle.insurance_expiry <= thirty_days,
                    Vehicle.insurance_expiry >= today_date,
                )
            )
        )
        insurance_expiring_count = ins_expiring_res.scalar() or 0

        # Maintenance due < 30 days or overdue
        maint_due_res = await session.execute(
            select(func.count(VehicleMaintenance.id)).where(
                and_(
                    VehicleMaintenance.status.in_(["SCHEDULED", "DUE"]),
                    VehicleMaintenance.scheduled_date <= thirty_days,
                )
            )
        )
        maintenance_due_count = maint_due_res.scalar() or 0

        return {
            "total_vehicles": total_vehicles,
            "available_count": available_count,
            "in_use_count": in_use_count,
            "maintenance_count": maintenance_count,
            "out_of_service_count": out_of_service_count,
            "active_trips_count": active_trips_count,
            "insurance_expiring_count": insurance_expiring_count,
            "maintenance_due_count": maintenance_due_count,
        }
