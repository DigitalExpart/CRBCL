"""Terminology governance and translation service."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.terminology import TerminologyKey, TerminologyTranslation


class TerminologyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_term(self, key: str, language: str = "en") -> str | None:
        """Fetch approved translation for key in specified language."""
        query = (
            select(TerminologyTranslation)
            .join(TerminologyKey)
            .where(
                TerminologyKey.key == key,
                TerminologyTranslation.language == language,
                TerminologyTranslation.is_approved == True,  # noqa: E712
            )
        )
        result = await self.db.execute(query)
        translation = result.scalar_one_or_none()
        return translation.value if translation else None

    async def list_terms_with_translations(self, context: str | None = None) -> list[TerminologyKey]:
        """List terminology keys with their translations."""
        query = select(TerminologyKey).options(selectinload(TerminologyKey.translations))
        if context:
            query = query.where(TerminologyKey.context == context)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def register_term(
        self,
        key: str,
        english_value: str,
        context: str = "general",
        description: str = "",
    ) -> TerminologyKey:
        """Register a new terminology key with an approved English baseline."""
        query = select(TerminologyKey).where(TerminologyKey.key == key)
        result = await self.db.execute(query)
        term = result.scalar_one_or_none()
        if not term:
            term = TerminologyKey(key=key, context=context, description=description)
            self.db.add(term)
            await self.db.flush()

            en_trans = TerminologyTranslation(
                key_id=term.id,
                language="en",
                value=english_value,
                is_approved=True,
            )
            self.db.add(en_trans)
            await self.db.flush()
        return term
