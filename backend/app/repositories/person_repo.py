"""Person repository with sub-profile management and fuzzy search."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.person import (
    Person,
)
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    def __init__(self, db: AsyncSession):
        super().__init__(Person, db)

    async def get_full(self, person_id: uuid.UUID) -> Person | None:
        """Fetch complete person profile with all sub-profiles."""
        query = (
            select(Person)
            .where(Person.id == person_id, Person.deleted_at.is_(None))
            .options(
                selectinload(Person.addresses),
                selectinload(Person.contacts),
                selectinload(Person.physical_description),
                selectinload(Person.cultural_profile),
                selectinload(Person.strengths),
                selectinload(Person.challenges),
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def find_duplicates(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: str | None = None,
        treaty_number: str | None = None,
        health_card_number: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        limit: int = 10,
    ) -> list[tuple[Person, float, list[str]]]:
        """
        Fuzzy duplicate detection returning candidates with similarity scores and matching factors.
        """
        query = select(Person).where(Person.deleted_at.is_(None))

        # Build candidate filter conditions
        conditions = [
            Person.first_name.ilike(f"%{first_name}%"),
            Person.last_name.ilike(f"%{last_name}%"),
        ]
        if treaty_number:
            conditions.append(Person.treaty_number == treaty_number)
        if health_card_number:
            conditions.append(Person.health_card_number == health_card_number)
        if phone:
            conditions.append(Person.phone == phone)
        if email:
            conditions.append(Person.email.ilike(email))

        query = query.where(or_(*conditions)).limit(limit)
        result = await self.db.execute(query)
        candidates = list(result.scalars().all())

        scored_candidates = []
        for p in candidates:
            score = 0.0
            factors = []

            # Name similarity
            if p.last_name.lower() == last_name.lower():
                score += 0.35
                factors.append("Exact last name match")
            elif last_name.lower() in p.last_name.lower() or p.last_name.lower() in last_name.lower():
                score += 0.20
                factors.append("Partial last name match")

            if p.first_name.lower() == first_name.lower():
                score += 0.25
                factors.append("Exact first name match")
            elif first_name.lower() in p.first_name.lower() or p.first_name.lower() in first_name.lower():
                score += 0.15
                factors.append("Partial first name match")

            # DOB match
            if date_of_birth and p.date_of_birth and str(p.date_of_birth) == str(date_of_birth):
                score += 0.30
                factors.append("Exact date of birth match")

            # Identifier match (high confidence)
            if treaty_number and p.treaty_number and p.treaty_number.strip() == treaty_number.strip():
                score += 0.40
                factors.append("Exact treaty number match")

            if (
                health_card_number
                and p.health_card_number
                and p.health_card_number.strip() == health_card_number.strip()
            ):
                score += 0.40
                factors.append("Exact health card number match")

            if phone and p.phone and p.phone.strip() == phone.strip():
                score += 0.20
                factors.append("Exact phone match")

            # Normalize score to max 1.0
            normalized_score = min(round(score, 2), 1.0)
            if normalized_score >= 0.30:
                scored_candidates.append((p, normalized_score, factors))

        return sorted(scored_candidates, key=lambda x: x[1], reverse=True)
