"""Repository for Placement Homes, Members, Licenses, Visits, Contacts, and Metrics."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import and_, asc, case, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import (
    PlacementHome,
    PlacementHomeContactLog,
    PlacementHomeLicense,
    PlacementHomeMember,
    PlacementHomeVisit,
)
from app.schemas.placement_home import PlacementHomeFilter


class PlacementHomeRepository:
    """Database repository for Placement Homes domain."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, home_id: uuid.UUID) -> PlacementHome | None:
        """Fetch a placement home by ID with full details."""
        query = (
            select(PlacementHome)
            .options(
                selectinload(PlacementHome.provider),
                selectinload(PlacementHome.members).selectinload(PlacementHomeMember.person),
                selectinload(PlacementHome.licenses),
                selectinload(PlacementHome.visits).selectinload(PlacementHomeVisit.worker),
                selectinload(PlacementHome.contact_logs).selectinload(PlacementHomeContactLog.person),
                selectinload(PlacementHome.contact_logs).selectinload(PlacementHomeContactLog.worker),
            )
            .where(
                PlacementHome.id == home_id,
                PlacementHome.deleted_at.is_(None),
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(query)
        return result.scalars().first()


    async def get_for_update(self, home_id: uuid.UUID) -> PlacementHome | None:
        """Acquire a row-level lock (SELECT ... FOR UPDATE) on the placement home to ensure atomic capacity checks."""
        query = (
            select(PlacementHome)
            .where(
                PlacementHome.id == home_id,
                PlacementHome.deleted_at.is_(None),
            )
            .with_for_update()
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_code(self, home_code: str) -> PlacementHome | None:
        """Fetch a placement home by unique code."""
        query = select(PlacementHome).where(
            PlacementHome.home_code == home_code,
            PlacementHome.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_active_occupancy(self, home_id: uuid.UUID) -> int:
        """Count active placement episodes occupying beds in this home."""
        query = select(func.count(PlacementEpisode.id)).where(
            PlacementEpisode.placement_home_id == home_id,
            PlacementEpisode.status == "ACTIVE",
            PlacementEpisode.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def generate_home_code(self) -> str:
        """Generate next sequential home code e.g. PH-2026-0001."""
        year = datetime.utcnow().year
        prefix = f"PH-{year}-"
        query = (
            select(PlacementHome.home_code)
            .where(PlacementHome.home_code.like(f"{prefix}%"))
            .order_by(desc(PlacementHome.home_code))
            .limit(1)
        )
        result = await self.session.execute(query)
        last_code = result.scalar()
        if last_code:
            try:
                seq = int(last_code.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    async def list_homes(self, filters: PlacementHomeFilter) -> tuple[list[dict[str, Any]], int]:
        """List and search placement homes with occupancy calculations."""
        # Subquery for active occupancy
        occupancy_subq = (
            select(
                PlacementEpisode.placement_home_id,
                func.count(PlacementEpisode.id).label("occupied_count"),
            )
            .where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
                PlacementEpisode.placement_home_id.is_not(None),
            )
            .group_by(PlacementEpisode.placement_home_id)
            .subquery()
        )

        # Base query
        stmt = (
            select(
                PlacementHome,
                func.coalesce(occupancy_subq.c.occupied_count, 0).label("occupied_beds"),
            )
            .outerjoin(occupancy_subq, PlacementHome.id == occupancy_subq.c.placement_home_id)
            .where(PlacementHome.deleted_at.is_(None))
        )

        if not filters.is_archived:
            stmt = stmt.where(PlacementHome.is_archived.is_(False))
        else:
            stmt = stmt.where(PlacementHome.is_archived.is_(True))

        if filters.search:
            s = f"%{filters.search}%"
            stmt = stmt.where(
                or_(
                    PlacementHome.name.ilike(s),
                    PlacementHome.home_code.ilike(s),
                    PlacementHome.community.ilike(s),
                    PlacementHome.city.ilike(s),
                    PlacementHome.primary_caregiver_name.ilike(s),
                )
            )

        if filters.home_type:
            stmt = stmt.where(PlacementHome.home_type == filters.home_type)

        if filters.status:
            stmt = stmt.where(PlacementHome.status == filters.status)

        if filters.licensing_status:
            stmt = stmt.where(PlacementHome.licensing_status == filters.licensing_status)

        if filters.community:
            stmt = stmt.where(PlacementHome.community.ilike(f"%{filters.community}%"))

        if filters.available_only:
            stmt = stmt.where(
                PlacementHome.total_capacity > func.coalesce(occupancy_subq.c.occupied_count, 0)
            )

        # Count total matching
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        # Pagination & ordering
        offset = (filters.page - 1) * filters.page_size
        stmt = stmt.order_by(desc(PlacementHome.created_at)).offset(offset).limit(filters.page_size)

        result = await self.session.execute(stmt)
        rows = result.all()

        items = []
        for home, occupied_count in rows:
            avail = max(0, home.total_capacity - occupied_count)
            items.append({
                "id": home.id,
                "home_code": home.home_code,
                "name": home.name,
                "home_type": home.home_type,
                "status": home.status,
                "licensing_status": home.licensing_status,
                "total_capacity": home.total_capacity,
                "occupied_beds": occupied_count,
                "available_beds": avail,
                "community": home.community,
                "city": home.city,
                "primary_caregiver_name": home.primary_caregiver_name,
                "is_archived": home.is_archived,
                "created_at": home.created_at,
            })

        return items, total

    async def get_map_markers(self) -> list[dict[str, Any]]:
        """Get location coordinates and availability markers for all active homes."""
        occupancy_subq = (
            select(
                PlacementEpisode.placement_home_id,
                func.count(PlacementEpisode.id).label("occupied_count"),
            )
            .where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
                PlacementEpisode.placement_home_id.is_not(None),
            )
            .group_by(PlacementEpisode.placement_home_id)
            .subquery()
        )

        stmt = (
            select(
                PlacementHome,
                func.coalesce(occupancy_subq.c.occupied_count, 0).label("occupied_beds"),
            )
            .outerjoin(occupancy_subq, PlacementHome.id == occupancy_subq.c.placement_home_id)
            .where(
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
                PlacementHome.latitude.is_not(None),
                PlacementHome.longitude.is_not(None),
            )
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        markers = []
        for home, occupied_count in rows:
            markers.append({
                "id": home.id,
                "home_code": home.home_code,
                "name": home.name,
                "home_type": home.home_type,
                "status": home.status,
                "licensing_status": home.licensing_status,
                "total_capacity": home.total_capacity,
                "occupied_beds": occupied_count,
                "available_beds": max(0, home.total_capacity - occupied_count),
                "community": home.community,
                "city": home.city,
                "latitude": home.latitude,
                "longitude": home.longitude,
            })
        return markers

    async def get_metrics(self) -> dict[str, Any]:
        """Compute system-wide Placement Home operational dashboard metrics."""
        today = date.today()
        d30 = today + timedelta(days=30)
        d90 = today + timedelta(days=90)

        # 1. Total, active, licensed homes and total beds
        home_stats = await self.session.execute(
            select(
                func.count(PlacementHome.id).label("total_homes"),
                func.count(case((PlacementHome.status == "ACTIVE", 1))).label("active_homes"),
                func.count(case((PlacementHome.licensing_status == "ACTIVE", 1))).label("licensed_homes"),
                func.coalesce(func.sum(case((PlacementHome.is_archived.is_(False), PlacementHome.total_capacity))), 0).label("total_beds"),
            ).where(
                PlacementHome.deleted_at.is_(None),
            )
        )
        h_row = home_stats.first()
        total_homes = h_row.total_homes or 0
        active_homes = h_row.active_homes or 0
        licensed_homes = h_row.licensed_homes or 0
        total_beds = h_row.total_beds or 0

        # 2. Occupied beds across all active placements
        occ_res = await self.session.execute(
            select(func.count(PlacementEpisode.id)).where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.placement_home_id.is_not(None),
                PlacementEpisode.deleted_at.is_(None),
            )
        )
        occupied_beds = occ_res.scalar() or 0
        available_beds = max(0, total_beds - occupied_beds)

        # 3. Homes at full capacity
        occupancy_subq = (
            select(
                PlacementEpisode.placement_home_id,
                func.count(PlacementEpisode.id).label("occ"),
            )
            .where(
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
                PlacementEpisode.placement_home_id.is_not(None),
            )
            .group_by(PlacementEpisode.placement_home_id)
            .subquery()
        )
        full_homes_res = await self.session.execute(
            select(func.count(PlacementHome.id))
            .outerjoin(occupancy_subq, PlacementHome.id == occupancy_subq.c.placement_home_id)
            .where(
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
                PlacementHome.status == "ACTIVE",
                func.coalesce(occupancy_subq.c.occ, 0) >= PlacementHome.total_capacity,
            )
        )
        homes_at_capacity = full_homes_res.scalar() or 0

        # 4. Licensing alerts
        lic_res = await self.session.execute(
            select(
                func.count(case((and_(PlacementHomeLicense.status == "ACTIVE", PlacementHomeLicense.expiry_date <= d90, PlacementHomeLicense.expiry_date > today), 1))).label("exp_90"),
                func.count(case((and_(PlacementHomeLicense.status == "ACTIVE", PlacementHomeLicense.expiry_date <= d30, PlacementHomeLicense.expiry_date > today), 1))).label("exp_30"),
                func.count(case((or_(PlacementHomeLicense.status == "EXPIRED", and_(PlacementHomeLicense.status == "ACTIVE", PlacementHomeLicense.expiry_date < today)), 1))).label("expired"),
            ).where(
                PlacementHomeLicense.deleted_at.is_(None),
            )
        )
        l_row = lic_res.first()
        expiring_90 = l_row.exp_90 or 0
        expiring_30 = l_row.exp_30 or 0
        expired_lic = l_row.expired or 0

        return {
            "total_homes": total_homes,
            "active_homes": active_homes,
            "licensed_homes": licensed_homes,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "homes_at_capacity": homes_at_capacity,
            "expiring_licenses_90d": expiring_90,
            "expiring_licenses_30d": expiring_30,
            "expired_licenses": expired_lic,
            "expiring_background_checks": 0,
        }

    async def create(self, home: PlacementHome) -> PlacementHome:
        """Persist a new placement home."""
        self.session.add(home)
        await self.session.flush()
        return home

    async def update(self, home: PlacementHome) -> PlacementHome:
        """Update an existing placement home."""
        await self.session.flush()
        return home

    # ── Members ────────────────────────────────────────────────
    async def add_member(self, member: PlacementHomeMember) -> PlacementHomeMember:
        self.session.add(member)
        await self.session.flush()
        return member

    async def get_member(self, member_id: uuid.UUID) -> PlacementHomeMember | None:
        query = (
            select(PlacementHomeMember)
            .options(selectinload(PlacementHomeMember.person))
            .where(
                PlacementHomeMember.id == member_id,
                PlacementHomeMember.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    # ── Licenses ───────────────────────────────────────────────
    async def create_license(self, license_: PlacementHomeLicense) -> PlacementHomeLicense:
        self.session.add(license_)
        await self.session.flush()
        return license_

    async def get_license(self, license_id: uuid.UUID) -> PlacementHomeLicense | None:
        query = select(PlacementHomeLicense).where(
            PlacementHomeLicense.id == license_id,
            PlacementHomeLicense.deleted_at.is_(None),
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    # ── Visits ─────────────────────────────────────────────────
    async def create_visit(self, visit: PlacementHomeVisit) -> PlacementHomeVisit:
        self.session.add(visit)
        await self.session.flush()
        return visit

    async def get_visit(self, visit_id: uuid.UUID) -> PlacementHomeVisit | None:
        query = (
            select(PlacementHomeVisit)
            .options(selectinload(PlacementHomeVisit.worker))
            .where(
                PlacementHomeVisit.id == visit_id,
                PlacementHomeVisit.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    # ── Contact Logs ───────────────────────────────────────────
    async def create_contact_log(self, contact: PlacementHomeContactLog) -> PlacementHomeContactLog:
        self.session.add(contact)
        await self.session.flush()
        return contact

    async def get_contact_log(self, contact_id: uuid.UUID) -> PlacementHomeContactLog | None:
        query = (
            select(PlacementHomeContactLog)
            .options(
                selectinload(PlacementHomeContactLog.person),
                selectinload(PlacementHomeContactLog.worker),
            )
            .where(
                PlacementHomeContactLog.id == contact_id,
                PlacementHomeContactLog.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    # ── Placement History ──────────────────────────────────────
    async def get_placement_history(self, home_id: uuid.UUID) -> list[PlacementEpisode]:
        """Fetch all placement episodes associated with this home in reverse chronological order."""
        query = (
            select(PlacementEpisode)
            .options(
                selectinload(PlacementEpisode.child),
                selectinload(PlacementEpisode.case),
                selectinload(PlacementEpisode.discharge_episode),
            )
            .where(
                PlacementEpisode.placement_home_id == home_id,
                PlacementEpisode.deleted_at.is_(None),
            )
            .order_by(desc(PlacementEpisode.start_date))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
