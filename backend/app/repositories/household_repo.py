"""Household and residential membership repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.relationship import Household, HouseholdMembership
from app.repositories.base import BaseRepository


class HouseholdRepository(BaseRepository[Household]):
    def __init__(self, db: AsyncSession):
        super().__init__(Household, db)

    async def list_households(
        self,
        query_text: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Household], int]:
        query = (
            select(Household)
            .where(Household.is_active == True)  # noqa: E712
            .options(selectinload(Household.memberships).selectinload(HouseholdMembership.person))
        )

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(Household.name.ilike(search_pattern) | Household.address_line_1.ilike(search_pattern))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(Household.name.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_with_members(self, household_id: uuid.UUID) -> Household | None:
        query = (
            select(Household)
            .where(Household.id == household_id)
            .options(selectinload(Household.memberships).selectinload(HouseholdMembership.person))
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def add_member(
        self,
        household_id: uuid.UUID,
        person_id: uuid.UUID,
        role: str = "Resident",
        notes: str = "",
    ) -> HouseholdMembership:
        membership = HouseholdMembership(
            household_id=household_id,
            person_id=person_id,
            role=role,
            is_current=True,
            notes=notes,
        )
        self.db.add(membership)
        await self.db.flush()
        return membership
