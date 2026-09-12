"""Person repository with sub-profile management and fuzzy search."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.person import (
    Person,
    PersonSequence,
)
from app.repositories.base import BaseRepository


class PersonRepository(BaseRepository[Person]):
    def __init__(self, db: AsyncSession):
        super().__init__(Person, db)

    async def generate_person_id_number(self) -> str:
        """Concurrency-safe sequence generator for permanent 10-digit numeric Person ID."""
        stmt = (
            select(PersonSequence)
            .where(PersonSequence.sequence_name == "person_id")
            .with_for_update()
        )
        try:
            res = await self.db.execute(stmt)
            seq = res.scalar_one_or_none()
        except Exception:
            # Fallback for dialects (such as SQLite in tests) where with_for_update is unsupported
            stmt_fallback = select(PersonSequence).where(PersonSequence.sequence_name == "person_id")
            res = await self.db.execute(stmt_fallback)
            seq = res.scalar_one_or_none()

        if not seq:
            seq = PersonSequence(sequence_name="person_id", last_value=1100000000)
            self.db.add(seq)
        if seq.last_value >= 9999999999:
            raise RuntimeError("10-digit Person ID sequence namespace exhausted (reached 9,999,999,999)")

        seq.last_value += 1
        await self.db.flush()
        return str(seq.last_value)

    async def get_by_person_id_number(self, person_id_number: str) -> Person | None:
        """Fetch person by numeric Person ID."""
        stmt = (
            select(Person)
            .where(Person.person_id_number == person_id_number, Person.deleted_at.is_(None))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def search_people(
        self,
        query_text: str | None = None,
        person_id_number: str | None = None,
        date_of_birth: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Person], int]:
        """Search canonical persons by name, ID number, and DOB."""
        stmt = select(Person).where(Person.deleted_at.is_(None))

        if person_id_number and person_id_number.strip():
            stmt = stmt.where(Person.person_id_number.ilike(f"%{person_id_number.strip()}%"))
        elif query_text and query_text.strip().isdigit():
            clean_digits = query_text.strip()
            stmt = stmt.where(
                or_(
                    Person.person_id_number.ilike(f"%{clean_digits}%"),
                    Person.phone.ilike(f"%{clean_digits}%"),
                )
            )
        elif query_text and query_text.strip():
            term = f"%{query_text.strip()}%"
            stmt = stmt.where(
                or_(
                    Person.first_name.ilike(term),
                    Person.last_name.ilike(term),
                    Person.preferred_name.ilike(term),
                    Person.aliases.ilike(term),
                )
            )

        if date_of_birth:
            stmt = stmt.where(Person.date_of_birth == date_of_birth)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = stmt.order_by(Person.last_name.asc(), Person.first_name.asc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        items = list(res.scalars().all())
        return items, total


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
        person_id_number: str | None = None,
        limit: int = 10,
    ) -> list[tuple[Person, float, list[str]]]:
        """
        Fuzzy duplicate detection returning candidates with similarity scores and matching factors.
        """
        query = select(Person).where(Person.deleted_at.is_(None))

        conditions = []
        if first_name and first_name.strip():
            conditions.append(Person.first_name.ilike(f"%{first_name.strip()}%"))
        if last_name and last_name.strip():
            conditions.append(Person.last_name.ilike(f"%{last_name.strip()}%"))
        if person_id_number and person_id_number.strip():
            conditions.append(Person.person_id_number == person_id_number.strip())
        if treaty_number and treaty_number.strip():
            conditions.append(Person.treaty_number == treaty_number.strip())
        if health_card_number and health_card_number.strip():
            conditions.append(Person.health_card_number == health_card_number.strip())
        if phone and phone.strip():
            conditions.append(Person.phone == phone.strip())
        if email and email.strip():
            conditions.append(Person.email.ilike(email.strip()))

        if not conditions:
            return []

        query = query.where(or_(*conditions)).limit(limit)
        result = await self.db.execute(query)
        candidates = list(result.scalars().all())

        scored_candidates = []
        for p in candidates:
            score = 0.0
            factors = []

            # Exact Person ID match
            if (
                person_id_number
                and p.person_id_number
                and p.person_id_number.strip() == person_id_number.strip()
            ):
                score += 1.00
                factors.append("Exact Person ID match")

            # Name similarity
            if last_name and last_name.strip() and p.last_name:
                if p.last_name.lower() == last_name.strip().lower():
                    score += 0.35
                    factors.append("Exact last name match")
                elif last_name.strip().lower() in p.last_name.lower() or p.last_name.lower() in last_name.strip().lower():
                    score += 0.20
                    factors.append("Partial last name match")

            if first_name and first_name.strip() and p.first_name:
                if p.first_name.lower() == first_name.strip().lower():
                    score += 0.25
                    factors.append("Exact first name match")
                elif first_name.strip().lower() in p.first_name.lower() or p.first_name.lower() in first_name.strip().lower():
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
