"""School and client school enrolment repository."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.school import ClientSchoolEnrolment, School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    def __init__(self, db: AsyncSession):
        super().__init__(School, db)

    async def list_schools(
        self,
        query_text: str | None = None,
        school_type: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[School], int]:
        query = select(School).where(School.is_active == True)  # noqa: E712

        if school_type:
            query = query.where(School.school_type == school_type)

        if query_text:
            search_pattern = f"%{query_text}%"
            query = query.where(School.name.ilike(search_pattern) | School.city.ilike(search_pattern))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        query = query.order_by(School.name.asc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def enroll_client(
        self,
        client_id: uuid.UUID,
        school_id: uuid.UUID,
        grade_level: str = "Grade 1",
        start_date=None,
        has_iep: bool = False,
        iep_details: str | None = None,
        school_contact_person: str | None = None,
        attendance_concerns: str | None = None,
        notes: str | None = None,
    ) -> ClientSchoolEnrolment:
        enrolment = ClientSchoolEnrolment(
            client_id=client_id,
            school_id=school_id,
            grade_level=grade_level,
            start_date=start_date,
            is_current=True,
            has_iep=has_iep,
            iep_details=iep_details,
            school_contact_person=school_contact_person,
            attendance_concerns=attendance_concerns,
            notes=notes,
        )
        self.db.add(enrolment)
        await self.db.flush()
        return enrolment

    async def list_client_enrolments(self, client_id: uuid.UUID) -> list[ClientSchoolEnrolment]:
        query = (
            select(ClientSchoolEnrolment)
            .where(ClientSchoolEnrolment.client_id == client_id)
            .options(selectinload(ClientSchoolEnrolment.school))
            .order_by(ClientSchoolEnrolment.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
