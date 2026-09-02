"""Repository for Sprint B — Clinical Notes, Programs, Grants, Incidents & Appointments."""

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sprint_b_models import (
    Appointment,
    ClinicalNote,
    ClinicalNoteAddendum,
    FundingGrant,
    Incident,
    Program,
)


class SprintBRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # 1. Clinical Notes
    async def create_clinical_note(self, note: ClinicalNote) -> ClinicalNote:
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(note)
        return note

    async def get_clinical_note(self, note_id: uuid.UUID) -> ClinicalNote | None:
        result = await self.db.execute(
            select(ClinicalNote).where(ClinicalNote.id == note_id, ClinicalNote.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def list_clinical_notes_for_client(self, client_id: uuid.UUID) -> Sequence[ClinicalNote]:
        result = await self.db.execute(
            select(ClinicalNote)
            .where(ClinicalNote.client_id == client_id, ClinicalNote.deleted_at.is_(None))
            .order_by(ClinicalNote.created_at.desc())
        )
        return result.scalars().all()

    async def add_clinical_addendum(self, addendum: ClinicalNoteAddendum) -> ClinicalNoteAddendum:
        self.db.add(addendum)
        await self.db.commit()
        await self.db.refresh(addendum)
        return addendum

    async def update_clinical_note(self, note: ClinicalNote) -> ClinicalNote:
        await self.db.commit()
        await self.db.refresh(note)
        return note

    # 2. Programs
    async def create_program(self, program: Program) -> Program:
        self.db.add(program)
        await self.db.commit()
        await self.db.refresh(program)
        return program

    async def list_programs(self) -> Sequence[Program]:
        result = await self.db.execute(select(Program).where(Program.deleted_at.is_(None)).order_by(Program.name.asc()))
        return result.scalars().all()

    # 3. Funding Grants
    async def create_grant(self, grant: FundingGrant) -> FundingGrant:
        self.db.add(grant)
        await self.db.commit()
        await self.db.refresh(grant)
        return grant

    async def list_grants(self) -> Sequence[FundingGrant]:
        result = await self.db.execute(
            select(FundingGrant).where(FundingGrant.deleted_at.is_(None)).order_by(FundingGrant.grant_name.asc())
        )
        return result.scalars().all()

    # 4. Incidents
    async def create_incident(self, incident: Incident) -> Incident:
        self.db.add(incident)
        await self.db.commit()
        await self.db.refresh(incident)
        return incident

    async def list_incidents(self) -> Sequence[Incident]:
        result = await self.db.execute(
            select(Incident).where(Incident.deleted_at.is_(None)).order_by(Incident.incident_date.desc())
        )
        return result.scalars().all()

    # 5. Appointments
    async def create_appointment(self, appt: Appointment) -> Appointment:
        self.db.add(appt)
        await self.db.commit()
        await self.db.refresh(appt)
        return appt

    async def list_appointments(self) -> Sequence[Appointment]:
        result = await self.db.execute(
            select(Appointment).where(Appointment.deleted_at.is_(None)).order_by(Appointment.scheduled_at.asc())
        )
        return result.scalars().all()
