"""Case note repository with locking support."""

from __future__ import annotations

import uuid
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_note import CaseNote
from app.repositories.base import BaseRepository


class CaseNoteRepository(BaseRepository[CaseNote]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseNote, db)

    async def list_for_case(
        self,
        case_id: uuid.UUID,
        include_confidential: bool = True,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[CaseNote], int]:
        query = select(CaseNote).where(
            CaseNote.case_id == case_id,
            CaseNote.deleted_at.is_(None),
        )

        if not include_confidential:
            query = query.where(CaseNote.is_confidential == False)  # noqa: E712

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(CaseNote.created_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
