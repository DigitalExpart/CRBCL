"""Client repository with trigram text search and team scoping."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: AsyncSession):
        super().__init__(Client, db)

    async def search(
        self,
        query_text: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        team_id: uuid.UUID | None = None,
        accessible_team_ids: set[uuid.UUID] | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_by: str | None = None,
    ) -> tuple[list[Client], int]:
        """Search clients with team access scoping and text search."""
        query = select(Client).where(Client.deleted_at.is_(None))

        # Team scoping: if accessible_team_ids is provided, restrict to those teams or unassigned
        if accessible_team_ids is not None:
            query = query.where(
                or_(
                    Client.assigned_team_id.in_(accessible_team_ids),
                    Client.assigned_team_id.is_(None),
                )
            )

        if team_id is not None:
            query = query.where(Client.assigned_team_id == team_id)

        if status:
            query = query.where(Client.status == status)

        if risk_level:
            query = query.where(Client.risk_level == risk_level)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(
                or_(
                    Client.first_name.ilike(search_pattern),
                    Client.last_name.ilike(search_pattern),
                    Client.email.ilike(search_pattern),
                    Client.phone.ilike(search_pattern),
                    Client.band_nation.ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        if sort_by:
            is_desc = sort_by.startswith("-")
            field = sort_by[1:] if is_desc else sort_by
            if hasattr(Client, field):
                col = getattr(Client, field)
                query = query.order_by(col.desc() if is_desc else col.asc())
        else:
            query = query.order_by(Client.created_at.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
