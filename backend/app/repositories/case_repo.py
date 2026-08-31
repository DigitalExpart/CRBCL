"""Case repository with atomic sequence generation and server-side multi-criteria search."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseSequence
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    def __init__(self, db: AsyncSession):
        super().__init__(Case, db)

    async def generate_case_number(self) -> str:
        """Generate a concurrency-safe, server-side atomic case number: CRB-YYYYMM-XXXX."""
        now = datetime.now(UTC)
        period = now.strftime("%Y%m")  # e.g., '202608'

        # Row lock sequence record for the current period (with fallback if dialect doesn't support with_for_update)
        stmt = select(CaseSequence).where(CaseSequence.period == period)
        try:
            stmt = stmt.with_for_update()
            res = await self.db.execute(stmt)
            seq = res.scalar_one_or_none()
        except Exception:
            res = await self.db.execute(select(CaseSequence).where(CaseSequence.period == period))
            seq = res.scalar_one_or_none()

        if not seq:
            # Check existing cases in this period to align sequence if records already exist
            prefix = f"CRB-{period}"
            count_res = await self.db.execute(
                select(func.count()).select_from(Case).where(Case.case_number.like(f"{prefix}%"))
            )
            initial_val = count_res.scalar_one() + 1
            seq = CaseSequence(period=period, last_value=initial_val)
            self.db.add(seq)
            await self.db.flush()
            val = initial_val
        else:
            seq.last_value += 1
            await self.db.flush()
            val = seq.last_value

        return f"CRB-{period}-{val:04d}"

    async def search(
        self,
        query_text: str | None = None,
        status: str | None = None,
        stage: str | None = None,
        priority: str | None = None,
        risk_level: str | None = None,
        case_type: str | None = None,
        client_id: uuid.UUID | None = None,
        family_id: uuid.UUID | None = None,
        assigned_worker_id: uuid.UUID | None = None,
        assigned_team_id: uuid.UUID | None = None,
        accessible_team_ids: set[uuid.UUID] | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
    ) -> tuple[list[Case], int]:
        """Server-side multi-parameter case search with team scoping."""
        query = select(Case).where(Case.deleted_at.is_(None))

        if accessible_team_ids is not None:
            query = query.where(
                or_(
                    Case.assigned_team_id.in_(accessible_team_ids),
                    Case.assigned_team_id.is_(None),
                )
            )

        if status and status != "all":
            query = query.where(Case.status == status)

        if stage and stage != "all":
            query = query.where(Case.stage == stage)

        if priority and priority != "all":
            query = query.where(Case.priority == priority)

        if risk_level and risk_level != "all":
            query = query.where(Case.risk_level == risk_level)

        if case_type and case_type != "all":
            query = query.where(Case.case_type == case_type)

        if client_id:
            query = query.where(Case.client_id == client_id)

        if family_id:
            query = query.where(Case.family_id == family_id)

        if assigned_worker_id:
            query = query.where(Case.assigned_worker_id == assigned_worker_id)

        if assigned_team_id:
            query = query.where(Case.assigned_team_id == assigned_team_id)

        if start_date:
            query = query.where(Case.intake_date >= start_date)

        if end_date:
            query = query.where(Case.intake_date <= end_date)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                or_(
                    Case.case_number.ilike(search_pattern),
                    Case.title.ilike(search_pattern),
                    Case.assigned_worker_name.ilike(search_pattern),
                    Case.description.ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        if sort_by:
            is_desc = sort_by.startswith("-")
            field = sort_by[1:] if is_desc else sort_by
            if hasattr(Case, field):
                col = getattr(Case, field)
                query = query.order_by(col.desc() if is_desc else col.asc())
        else:
            query = query.order_by(Case.created_at.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
