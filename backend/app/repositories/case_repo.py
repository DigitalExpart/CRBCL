"""Case repository with search and team scoping."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.repositories.base import BaseRepository


class CaseRepository(BaseRepository[Case]):
    def __init__(self, db: AsyncSession):
        super().__init__(Case, db)

    async def generate_case_number(self) -> str:
        """Generate a human-readable case number: CRB-YYYYMM-XXXX."""
        now = datetime.now(timezone.utc)
        prefix = f"CRB-{now.strftime('%Y%m')}"
        count_res = await self.db.execute(
            select(func.count()).select_from(Case).where(Case.case_number.like(f"{prefix}%"))
        )
        count = count_res.scalar_one() + 1
        return f"{prefix}-{count:04d}"

    async def search(
        self,
        query_text: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        case_type: str | None = None,
        client_id: uuid.UUID | None = None,
        family_id: uuid.UUID | None = None,
        accessible_team_ids: set[uuid.UUID] | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
    ) -> tuple[list[Case], int]:
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

        if priority:
            query = query.where(Case.priority == priority)

        if case_type:
            query = query.where(Case.case_type == case_type)

        if client_id:
            query = query.where(Case.client_id == client_id)

        if family_id:
            query = query.where(Case.family_id == family_id)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                or_(
                    Case.case_number.ilike(search_pattern),
                    Case.title.ilike(search_pattern),
                    Case.assigned_worker_name.ilike(search_pattern),
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
