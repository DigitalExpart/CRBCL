"""Family repository with search and team scoping."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.family import Family
from app.repositories.base import BaseRepository


class FamilyRepository(BaseRepository[Family]):
    def __init__(self, db: AsyncSession):
        super().__init__(Family, db)

    async def search(
        self,
        query_text: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        accessible_team_ids: set[uuid.UUID] | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
    ) -> tuple[list[Family], int]:
        query = select(Family).where(Family.deleted_at.is_(None))

        if accessible_team_ids is not None:
            query = query.where(
                or_(
                    Family.assigned_team_id.in_(accessible_team_ids),
                    Family.assigned_team_id.is_(None),
                )
            )

        if status:
            query = query.where(Family.status == status)

        if risk_level:
            query = query.where(Family.risk_level == risk_level)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                or_(
                    Family.family_name.ilike(search_pattern),
                    Family.primary_contact_name.ilike(search_pattern),
                    Family.primary_contact_phone.ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        if sort_by:
            is_desc = sort_by.startswith("-")
            field = sort_by[1:] if is_desc else sort_by
            if hasattr(Family, field):
                col = getattr(Family, field)
                query = query.order_by(col.desc() if is_desc else col.asc())
        else:
            query = query.order_by(Family.created_at.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
