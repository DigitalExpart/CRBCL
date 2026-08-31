"""Duplicate detection service using fuzzy matching and similarity scoring."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.person_repo import PersonRepository


class DuplicateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.person_repo = PersonRepository(db)

    async def check_duplicates(
        self,
        first_name: str,
        last_name: str,
        date_of_birth: str | None = None,
        treaty_number: str | None = None,
        health_card_number: str | None = None,
        phone: str | None = None,
        email: str | None = None,
    ) -> list[dict]:
        """
        Check for potential duplicate individuals before profile creation.
        Returns list of candidate records with similarity score and matching factors.
        """
        results = await self.person_repo.find_duplicates(
            first_name=first_name,
            last_name=last_name,
            date_of_birth=date_of_birth,
            treaty_number=treaty_number,
            health_card_number=health_card_number,
            phone=phone,
            email=email,
        )

        candidates = []
        for person, score, factors in results:
            candidates.append(
                {
                    "person_id": str(person.id),
                    "first_name": person.first_name,
                    "last_name": person.last_name,
                    "date_of_birth": str(person.date_of_birth) if person.date_of_birth else None,
                    "treaty_number": person.treaty_number,
                    "health_card_number": person.health_card_number,
                    "similarity_score": score,
                    "matching_factors": factors,
                }
            )
        return candidates
