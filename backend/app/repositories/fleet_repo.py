"""Fleet Repository for database access and queries (Phase 12)."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fleet import (
    FleetGeofence,
    Vehicle,
    VehicleInsurancePolicy,
    VehicleLocation,
    VehicleMaintenance,
    VehicleTrip,
)


class FleetRepository:
    """Repository handling database operations for Fleet Management."""

    # ── 1. Vehicles ───────────────────────────────────────────────
    @staticmethod
    async def get_vehicles(
        session: AsyncSession,
        status: str | None = None,
        vehicle_type: str | None = None,
        search: str | None = None,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Vehicle]:
        stmt = select(Vehicle).options(selectinload(Vehicle.current_driver))
        if not include_archived:
            stmt = stmt.where(Vehicle.archived_at.is_(None))
        if status:
            stmt = stmt.where(Vehicle.status == status)
        if vehicle_type:
            stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)
        if search:
            s_term = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Vehicle.vehicle_internal_id.ilike(s_term),
                    Vehicle.licence_plate.ilike(s_term),
                    Vehicle.make.ilike(s_term),
                    Vehicle.model.ilike(s_term),
                )
            )
        stmt = stmt.order_by(Vehicle.vehicle_internal_id.asc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    @staticmethod
    async def get_vehicle_by_id(session: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
        stmt = (
            select(Vehicle)
            .options(
                selectinload(Vehicle.current_driver),
                selectinload(Vehicle.trips),
                selectinload(Vehicle.maintenance_records),
                selectinload(Vehicle.insurance_policies),
                selectinload(Vehicle.locations),
            )
            .where(Vehicle.id == vehicle_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_vehicle(session: AsyncSession, vehicle_data: dict[str, Any]) -> Vehicle:
        v = Vehicle(**vehicle_data)
        session.add(v)
        await session.flush()
        return v

    @staticmethod
    async def update_vehicle(session: AsyncSession, vehicle: Vehicle, update_data: dict[str, Any]) -> Vehicle:
        for key, val in update_data.items():
            if hasattr(vehicle, key) and val is not None:
                setattr(vehicle, key, val)
        await session.flush()
        return vehicle

    @staticmethod
    async def archive_vehicle(session: AsyncSession, vehicle: Vehicle) -> Vehicle:
        vehicle.archived_at = datetime.utcnow()
        vehicle.status = "RETIRED"
        await session.flush()
        return vehicle

    # ── 2. Vehicle Trips & Concurrency ─────────────────────────────
    @staticmethod
    async def get_active_trip_for_vehicle(session: AsyncSession, vehicle_id: uuid.UUID) -> VehicleTrip | None:
        stmt = select(VehicleTrip).where(
            and_(VehicleTrip.vehicle_id == vehicle_id, VehicleTrip.status == "CHECKED_OUT")
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def create_trip(session: AsyncSession, trip_data: dict[str, Any]) -> VehicleTrip:
        trip = VehicleTrip(**trip_data)
        session.add(trip)
        await session.flush()
        return trip

    @staticmethod
    async def get_trip_by_id(session: AsyncSession, trip_id: uuid.UUID) -> VehicleTrip | None:
        stmt = (
            select(VehicleTrip)
            .options(
                selectinload(VehicleTrip.driver),
                selectinload(VehicleTrip.case),
                selectinload(VehicleTrip.client),
            )
            .where(VehicleTrip.id == trip_id)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()


    @staticmethod
    async def get_trips(
        session: AsyncSession,
        vehicle_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[VehicleTrip]:
        stmt = select(VehicleTrip).options(
            selectinload(VehicleTrip.vehicle),
            selectinload(VehicleTrip.driver),
        )
        if vehicle_id:
            stmt = stmt.where(VehicleTrip.vehicle_id == vehicle_id)
        if driver_id:
            stmt = stmt.where(VehicleTrip.driver_id == driver_id)
        if status:
            stmt = stmt.where(VehicleTrip.status == status)
        stmt = stmt.order_by(VehicleTrip.start_time.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    # ── 3. Maintenance ─────────────────────────────────────────────
    @staticmethod
    async def create_maintenance(session: AsyncSession, maintenance_data: dict[str, Any]) -> VehicleMaintenance:
        m = VehicleMaintenance(**maintenance_data)
        session.add(m)
        await session.flush()
        return m

    @staticmethod
    async def get_maintenance_records(
        session: AsyncSession,
        vehicle_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[VehicleMaintenance]:
        stmt = select(VehicleMaintenance).options(selectinload(VehicleMaintenance.vehicle))
        if vehicle_id:
            stmt = stmt.where(VehicleMaintenance.vehicle_id == vehicle_id)
        if status:
            stmt = stmt.where(VehicleMaintenance.status == status)
        stmt = stmt.order_by(VehicleMaintenance.created_at.desc()).limit(limit)
        res = await session.execute(stmt)
        return list(res.scalars().all())

    # ── 4. Insurance ───────────────────────────────────────────────
    @staticmethod
    async def create_insurance_policy(session: AsyncSession, policy_data: dict[str, Any]) -> VehicleInsurancePolicy:
        p = VehicleInsurancePolicy(**policy_data)
        session.add(p)
        await session.flush()
        return p

    @staticmethod
    async def get_insurance_policies(
        session: AsyncSession, vehicle_id: uuid.UUID | None = None
    ) -> list[VehicleInsurancePolicy]:
        stmt = select(VehicleInsurancePolicy).options(selectinload(VehicleInsurancePolicy.vehicle))
        if vehicle_id:
            stmt = stmt.where(VehicleInsurancePolicy.vehicle_id == vehicle_id)
        stmt = stmt.order_by(VehicleInsurancePolicy.expiry_date.desc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    # ── 5. Locations & Telematics ─────────────────────────────────
    @staticmethod
    async def create_location(session: AsyncSession, location_data: dict[str, Any]) -> VehicleLocation:
        loc = VehicleLocation(**location_data)
        session.add(loc)
        await session.flush()
        return loc

    @staticmethod
    async def get_latest_vehicle_location(session: AsyncSession, vehicle_id: uuid.UUID) -> VehicleLocation | None:
        stmt = (
            select(VehicleLocation)
            .where(VehicleLocation.vehicle_id == vehicle_id)
            .order_by(VehicleLocation.recorded_at.desc())
            .limit(1)
        )
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def get_vehicle_locations(
        session: AsyncSession, vehicle_id: uuid.UUID, limit: int = 100
    ) -> list[VehicleLocation]:
        stmt = (
            select(VehicleLocation)
            .where(VehicleLocation.vehicle_id == vehicle_id)
            .order_by(VehicleLocation.recorded_at.desc())
            .limit(limit)
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    # ── 6. Geofences ───────────────────────────────────────────────
    @staticmethod
    async def create_geofence(session: AsyncSession, geofence_data: dict[str, Any]) -> FleetGeofence:
        g = FleetGeofence(**geofence_data)
        session.add(g)
        await session.flush()
        return g

    @staticmethod
    async def get_geofences(session: AsyncSession, active_only: bool = True) -> list[FleetGeofence]:
        stmt = select(FleetGeofence)
        if active_only:
            stmt = stmt.where(FleetGeofence.is_active.is_(True))
        res = await session.execute(stmt)
        return list(res.scalars().all())
