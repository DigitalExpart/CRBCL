"""Team repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.repositories.base import BaseRepository


class TeamRepository(BaseRepository[Team]):
    def __init__(self, db: AsyncSession):
        super().__init__(Team, db)

    async def list_active_teams(self) -> list[Team]:
        query = select(Team).where(Team.is_active == True).order_by(Team.sort_order.asc())  # noqa: E712
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Team | None:
        query = select(Team).where(Team.code == code)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
