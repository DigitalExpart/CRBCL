"""Case note repository with locking support, filtering, addenda, and contact metrics."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_note import CaseNote, CaseNoteAddendum, CaseNoteAttachment, CaseNotePerson
from app.repositories.base import BaseRepository


class CaseNoteRepository(BaseRepository[CaseNote]):
    def __init__(self, db: AsyncSession):
        super().__init__(CaseNote, db)

    async def get_by_id_with_details(self, note_id: uuid.UUID) -> CaseNote | None:
        """Fetch note with addenda, people, and attachments."""
        stmt = (
            select(CaseNote)
            .where(CaseNote.id == note_id, CaseNote.deleted_at.is_(None))
            .options(
                selectinload(CaseNote.addenda).selectinload(CaseNoteAddendum.author),
                selectinload(CaseNote.people).selectinload(CaseNotePerson.person),
                selectinload(CaseNote.attachments),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_for_case(
        self,
        case_id: uuid.UUID,
        include_confidential: bool = True,
        contact_type: str | None = None,
        location: str | None = None,
        status: str | None = None,
        appointment_status: str | None = None,
        author_name: str | None = None,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        offset: int = 0,
        limit: int = 50,
        sort_order: str = "desc",
    ) -> tuple[list[CaseNote], int]:
        query = select(CaseNote).where(
            CaseNote.case_id == case_id,
            CaseNote.deleted_at.is_(None),
        )

        if not include_confidential:
            query = query.where(CaseNote.is_confidential == False)  # noqa: E712

        if contact_type and contact_type != "all":
            query = query.where(CaseNote.contact_type == contact_type)

        if location and location != "all":
            query = query.where(CaseNote.location == location)

        if status and status != "all":
            query = query.where(CaseNote.status == status)

        if appointment_status and appointment_status != "all":
            query = query.where(CaseNote.appointment_status == appointment_status)

        if author_name:
            query = query.where(CaseNote.author_name.ilike(f"%{author_name}%"))

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    CaseNote.subject.ilike(search_pattern),
                    CaseNote.content.ilike(search_pattern),
                )
            )

        if start_date:
            query = query.where(func.date(CaseNote.created_at) >= start_date)

        if end_date:
            query = query.where(func.date(CaseNote.created_at) <= end_date)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.options(
            selectinload(CaseNote.addenda).selectinload(CaseNoteAddendum.author),
            selectinload(CaseNote.people).selectinload(CaseNotePerson.person),
            selectinload(CaseNote.attachments),
        )

        if sort_order.lower() == "asc":
            query = query.order_by(CaseNote.created_at.asc())
        else:
            query = query.order_by(CaseNote.created_at.desc())

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_case_metrics(self, case_id: uuid.UUID) -> dict:
        """Calculate attendance metrics and service breakdown server-side."""
        # Total counts by appointment_status
        status_stmt = (
            select(CaseNote.appointment_status, func.count(CaseNote.id))
            .where(
                CaseNote.case_id == case_id,
                CaseNote.deleted_at.is_(None),
                CaseNote.appointment_status.is_not(None),
            )
            .group_by(CaseNote.appointment_status)
        )
        status_res = await self.db.execute(status_stmt)
        status_counts = {row[0]: row[1] for row in status_res.all()}

        # Total counts by contact_type
        contact_stmt = (
            select(CaseNote.contact_type, func.count(CaseNote.id))
            .where(
                CaseNote.case_id == case_id,
                CaseNote.deleted_at.is_(None),
                CaseNote.contact_type.is_not(None),
            )
            .group_by(CaseNote.contact_type)
        )
        contact_res = await self.db.execute(contact_stmt)
        contact_counts = {row[0]: row[1] for row in contact_res.all()}

        # Total notes count
        total_stmt = select(func.count(CaseNote.id)).where(
            CaseNote.case_id == case_id,
            CaseNote.deleted_at.is_(None),
        )
        total_notes = (await self.db.execute(total_stmt)).scalar_one()

        return {
            "total_notes": total_notes,
            "attendance": {
                "attended": status_counts.get("ATTENDED", 0),
                "no_show": status_counts.get("NO_SHOW", 0),
                "cancelled": status_counts.get("CANCELLED", 0),
                "rescheduled": status_counts.get("RESCHEDULED", 0),
            },
            "contact_types": contact_counts,
        }
