"""Repository for Placements, Active Efforts, Removals, Respite, Discharge, Permanency, Visitation, Court & Background Checks."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.placement import (
    ActiveEffort,
    BackgroundCheck,
    CourtEvent,
    DischargeEpisode,
    InHomePlacement,
    PermanencyPlan,
    PlacementEpisode,
    RemovalEpisode,
    RespiteEpisode,
    VisitationPlan,
)


class PlacementRepository:
    """PostgreSQL data access layer for Phase 7 Placement domain entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Active Efforts ───────────────────────────────────────────────
    async def create_active_effort(self, effort: ActiveEffort) -> ActiveEffort:
        self.db.add(effort)
        await self.db.flush()
        return effort

    async def get_active_effort_by_id(self, effort_id: uuid.UUID) -> ActiveEffort | None:
        stmt = (
            select(ActiveEffort)
            .where(ActiveEffort.id == effort_id, ActiveEffort.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active_efforts_by_case(
        self,
        case_id: uuid.UUID,
        outcome: str | None = None,
        effort_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[ActiveEffort], int]:
        base_filter = [ActiveEffort.case_id == case_id, ActiveEffort.deleted_at.is_(None)]
        if outcome:
            base_filter.append(ActiveEffort.outcome == outcome.upper())
        if effort_type:
            base_filter.append(ActiveEffort.effort_type == effort_type.upper())

        count_stmt = select(func.count()).select_from(ActiveEffort).where(*base_filter)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(ActiveEffort)
            .where(*base_filter)
            .order_by(ActiveEffort.service_date.desc(), ActiveEffort.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    # ── Background Checks ────────────────────────────────────────────
    async def create_background_check(self, check: BackgroundCheck) -> BackgroundCheck:
        self.db.add(check)
        await self.db.flush()
        return check

    async def get_background_check_by_id(self, check_id: uuid.UUID) -> BackgroundCheck | None:
        stmt = (
            select(BackgroundCheck)
            .where(BackgroundCheck.id == check_id, BackgroundCheck.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_background_checks(
        self,
        subject_type: str | None = None,
        subject_id: uuid.UUID | None = None,
        status: str | None = None,
        check_type: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[BackgroundCheck], int]:
        filters = [BackgroundCheck.deleted_at.is_(None)]
        if subject_type:
            filters.append(BackgroundCheck.subject_type == subject_type.upper())
        if subject_id:
            filters.append(BackgroundCheck.subject_id == subject_id)
        if status:
            filters.append(BackgroundCheck.status == status.upper())
        if check_type:
            filters.append(BackgroundCheck.check_type == check_type.upper())

        count_stmt = select(func.count()).select_from(BackgroundCheck).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(BackgroundCheck)
            .where(*filters)
            .order_by(BackgroundCheck.request_date.desc(), BackgroundCheck.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    # ── In-Home Placements ───────────────────────────────────────────
    async def create_in_home_placement(self, placement: InHomePlacement) -> InHomePlacement:
        self.db.add(placement)
        await self.db.flush()
        return placement

    async def get_in_home_placement_by_id(self, placement_id: uuid.UUID) -> InHomePlacement | None:
        stmt = (
            select(InHomePlacement)
            .where(InHomePlacement.id == placement_id, InHomePlacement.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_in_home_placement_for_child(self, child_id: uuid.UUID) -> InHomePlacement | None:
        stmt = (
            select(InHomePlacement)
            .where(
                InHomePlacement.child_id == child_id,
                InHomePlacement.status == "ACTIVE",
                InHomePlacement.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_in_home_placements_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[InHomePlacement], int]:
        filters = [InHomePlacement.case_id == case_id, InHomePlacement.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(InHomePlacement).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(InHomePlacement)
            .where(*filters)
            .order_by(InHomePlacement.start_date.desc(), InHomePlacement.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_in_home_placements_by_child(self, child_id: uuid.UUID) -> list[InHomePlacement]:
        stmt = (
            select(InHomePlacement)
            .where(InHomePlacement.child_id == child_id, InHomePlacement.deleted_at.is_(None))
            .order_by(InHomePlacement.start_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Removal Episodes ─────────────────────────────────────────────
    async def create_removal_episode(self, removal: RemovalEpisode) -> RemovalEpisode:
        self.db.add(removal)
        await self.db.flush()
        return removal

    async def get_removal_episode_by_id(self, removal_id: uuid.UUID) -> RemovalEpisode | None:
        stmt = (
            select(RemovalEpisode)
            .options(selectinload(RemovalEpisode.placements))
            .where(RemovalEpisode.id == removal_id, RemovalEpisode.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_removal_episodes_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[RemovalEpisode], int]:
        filters = [RemovalEpisode.case_id == case_id, RemovalEpisode.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(RemovalEpisode).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(RemovalEpisode)
            .where(*filters)
            .order_by(RemovalEpisode.removal_date.desc(), RemovalEpisode.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_removal_episodes_by_child(self, child_id: uuid.UUID) -> list[RemovalEpisode]:
        stmt = (
            select(RemovalEpisode)
            .where(RemovalEpisode.child_id == child_id, RemovalEpisode.deleted_at.is_(None))
            .order_by(RemovalEpisode.removal_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Placement Episodes ───────────────────────────────────────────
    async def create_placement_episode(self, placement: PlacementEpisode) -> PlacementEpisode:
        self.db.add(placement)
        await self.db.flush()
        return placement

    async def get_placement_episode_by_id(self, placement_id: uuid.UUID) -> PlacementEpisode | None:
        stmt = (
            select(PlacementEpisode)
            .options(
                selectinload(PlacementEpisode.removal_episode),
                selectinload(PlacementEpisode.respite_episodes),
                selectinload(PlacementEpisode.discharge_episode),
            )
            .where(PlacementEpisode.id == placement_id, PlacementEpisode.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_placement_for_child(self, child_id: uuid.UUID) -> PlacementEpisode | None:
        stmt = (
            select(PlacementEpisode)
            .where(
                PlacementEpisode.child_id == child_id,
                PlacementEpisode.status.in_(["ACTIVE", "DISRUPTED"]),
                PlacementEpisode.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_placement_episodes_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[PlacementEpisode], int]:
        filters = [PlacementEpisode.case_id == case_id, PlacementEpisode.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(PlacementEpisode).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(PlacementEpisode)
            .where(*filters)
            .order_by(PlacementEpisode.start_date.desc(), PlacementEpisode.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_placement_episodes_by_child(self, child_id: uuid.UUID) -> list[PlacementEpisode]:
        stmt = (
            select(PlacementEpisode)
            .options(
                selectinload(PlacementEpisode.removal_episode),
                selectinload(PlacementEpisode.respite_episodes),
                selectinload(PlacementEpisode.discharge_episode),
            )
            .where(PlacementEpisode.child_id == child_id, PlacementEpisode.deleted_at.is_(None))
            .order_by(PlacementEpisode.start_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Respite Episodes ─────────────────────────────────────────────
    async def create_respite_episode(self, respite: RespiteEpisode) -> RespiteEpisode:
        self.db.add(respite)
        await self.db.flush()
        return respite

    async def get_respite_episode_by_id(self, respite_id: uuid.UUID) -> RespiteEpisode | None:
        stmt = (
            select(RespiteEpisode)
            .where(RespiteEpisode.id == respite_id, RespiteEpisode.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_respite_episodes_by_placement(
        self, placement_episode_id: uuid.UUID
    ) -> list[RespiteEpisode]:
        stmt = (
            select(RespiteEpisode)
            .where(
                RespiteEpisode.placement_episode_id == placement_episode_id,
                RespiteEpisode.deleted_at.is_(None),
            )
            .order_by(RespiteEpisode.start_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Discharge Episodes ───────────────────────────────────────────
    async def create_discharge_episode(self, discharge: DischargeEpisode) -> DischargeEpisode:
        self.db.add(discharge)
        await self.db.flush()
        return discharge

    async def get_discharge_episode_by_id(self, discharge_id: uuid.UUID) -> DischargeEpisode | None:
        stmt = (
            select(DischargeEpisode)
            .where(DischargeEpisode.id == discharge_id, DischargeEpisode.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_discharge_by_placement_id(self, placement_episode_id: uuid.UUID) -> DischargeEpisode | None:
        stmt = (
            select(DischargeEpisode)
            .where(
                DischargeEpisode.placement_episode_id == placement_episode_id,
                DischargeEpisode.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ── Permanency Plans ─────────────────────────────────────────────
    async def create_permanency_plan(self, plan: PermanencyPlan) -> PermanencyPlan:
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def get_permanency_plan_by_id(self, plan_id: uuid.UUID) -> PermanencyPlan | None:
        stmt = (
            select(PermanencyPlan)
            .where(PermanencyPlan.id == plan_id, PermanencyPlan.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_permanency_plans_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[PermanencyPlan], int]:
        filters = [PermanencyPlan.case_id == case_id, PermanencyPlan.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(PermanencyPlan).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(PermanencyPlan)
            .where(*filters)
            .order_by(PermanencyPlan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_permanency_plans_by_child(self, child_id: uuid.UUID) -> list[PermanencyPlan]:
        stmt = (
            select(PermanencyPlan)
            .where(PermanencyPlan.child_id == child_id, PermanencyPlan.deleted_at.is_(None))
            .order_by(PermanencyPlan.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Visitation Plans ─────────────────────────────────────────────
    async def create_visitation_plan(self, plan: VisitationPlan) -> VisitationPlan:
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def get_visitation_plan_by_id(self, plan_id: uuid.UUID) -> VisitationPlan | None:
        stmt = (
            select(VisitationPlan)
            .where(VisitationPlan.id == plan_id, VisitationPlan.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_visitation_plans_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[VisitationPlan], int]:
        filters = [VisitationPlan.case_id == case_id, VisitationPlan.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(VisitationPlan).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(VisitationPlan)
            .where(*filters)
            .order_by(VisitationPlan.effective_from.desc(), VisitationPlan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_visitation_plans_by_child(self, child_id: uuid.UUID) -> list[VisitationPlan]:
        stmt = (
            select(VisitationPlan)
            .where(VisitationPlan.child_id == child_id, VisitationPlan.deleted_at.is_(None))
            .order_by(VisitationPlan.effective_from.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ── Court Events ─────────────────────────────────────────────────
    async def create_court_event(self, event: CourtEvent) -> CourtEvent:
        self.db.add(event)
        await self.db.flush()
        return event

    async def get_court_event_by_id(self, event_id: uuid.UUID) -> CourtEvent | None:
        stmt = (
            select(CourtEvent)
            .where(CourtEvent.id == event_id, CourtEvent.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_court_events_by_case(
        self, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[CourtEvent], int]:
        filters = [CourtEvent.case_id == case_id, CourtEvent.deleted_at.is_(None)]
        count_stmt = select(func.count()).select_from(CourtEvent).where(*filters)
        count_res = await self.db.execute(count_stmt)
        total = count_res.scalar_one()

        stmt = (
            select(CourtEvent)
            .where(*filters)
            .order_by(CourtEvent.hearing_date.desc(), CourtEvent.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all()), total

    async def list_court_events_by_child(self, child_id: uuid.UUID) -> list[CourtEvent]:
        stmt = (
            select(CourtEvent)
            .where(CourtEvent.child_id == child_id, CourtEvent.deleted_at.is_(None))
            .order_by(CourtEvent.hearing_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
