"""Service layer for Sprint B — Clinical Notes, Programs, Grants, Incidents & Appointments."""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sprint_b_models import (
    Appointment,
    ClinicalNote,
    ClinicalNoteAddendum,
    FundingGrant,
    Incident,
    Program,
)
from app.repositories.sprint_b_repo import SprintBRepository


class SprintBService:
    def __init__(self, db: AsyncSession):
        self.repo = SprintBRepository(db)

    # 1. Clinical Notes Lifecycle
    async def create_clinical_note(self, data: dict[str, Any], author_id: uuid.UUID) -> ClinicalNote:
        note = ClinicalNote(
            client_id=uuid.UUID(data["client_id"]),
            case_id=uuid.UUID(data["case_id"]) if data.get("case_id") else None,
            author_id=author_id,
            note_type=data.get("note_type", "LPN_OBSERVATION"),
            subject=data["subject"],
            narrative=data["narrative"],
            confidentiality=data.get("confidentiality", "CONFIDENTIAL"),
            status="DRAFT",
        )
        return await self.repo.create_clinical_note(note)

    async def get_clinical_note(self, note_id: uuid.UUID) -> ClinicalNote:
        note = await self.repo.get_clinical_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Clinical note not found")
        return note

    async def list_clinical_notes_for_client(self, client_id: uuid.UUID) -> Sequence[ClinicalNote]:
        return await self.repo.list_clinical_notes_for_client(client_id)

    async def lock_clinical_note(self, note_id: uuid.UUID, user_id: uuid.UUID) -> ClinicalNote:
        note = await self.get_clinical_note(note_id)
        if note.status == "LOCKED":
            raise HTTPException(status_code=400, detail="Clinical note is already locked")
        note.status = "LOCKED"
        note.locked_at = datetime.utcnow()
        note.locked_by_id = user_id
        return await self.repo.update_clinical_note(note)

    async def add_clinical_addendum(
        self, note_id: uuid.UUID, narrative: str, author_id: uuid.UUID
    ) -> ClinicalNoteAddendum:
        note = await self.get_clinical_note(note_id)
        if note.status != "LOCKED":
            raise HTTPException(status_code=400, detail="Addenda can only be added to LOCKED clinical notes")
        addendum = ClinicalNoteAddendum(
            clinical_note_id=note_id,
            author_id=author_id,
            narrative=narrative,
        )
        return await self.repo.add_clinical_addendum(addendum)

    # 2. Programs
    async def create_program(self, data: dict[str, Any]) -> Program:
        program = Program(
            name=data["name"],
            category=data.get("category", "Cultural Programs"),
            status=data.get("status", "ACTIVE"),
            description=data.get("description"),
            capacity=int(data.get("capacity", 20)),
            enrolled_count=int(data.get("enrolled_count", 0)),
            location=data.get("location"),
            coordinator_name=data.get("coordinator_name"),
            budget=float(data.get("budget", 0.0)),
        )
        return await self.repo.create_program(program)

    async def list_programs(self) -> Sequence[Program]:
        return await self.repo.list_programs()

    # 3. Funding Grants
    async def create_grant(self, data: dict[str, Any]) -> FundingGrant:
        grant = FundingGrant(
            grant_name=data["grant_name"],
            funder_name=data["funder_name"],
            amount=float(data["amount"]),
            status=data.get("status", "ACTIVE"),
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date()
            if isinstance(data["start_date"], str)
            else data["start_date"],
            end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date()
            if data.get("end_date") and isinstance(data["end_date"], str)
            else data.get("end_date"),
            restrictions=data.get("restrictions"),
            notes=data.get("notes"),
        )
        return await self.repo.create_grant(grant)

    async def list_grants(self) -> Sequence[FundingGrant]:
        return await self.repo.list_grants()

    # 4. Incidents
    async def create_incident(self, data: dict[str, Any]) -> Incident:
        incident = Incident(
            title=data["title"],
            incident_type=data.get("incident_type", "Critical Incident"),
            severity=data.get("severity", "MEDIUM"),
            status=data.get("status", "OPEN"),
            client_id=uuid.UUID(data["client_id"]) if data.get("client_id") else None,
            case_id=uuid.UUID(data["case_id"]) if data.get("case_id") else None,
            incident_date=datetime.fromisoformat(data["incident_date"])
            if isinstance(data["incident_date"], str)
            else data["incident_date"],
            location=data["location"],
            description=data["description"],
            actions_taken=data.get("actions_taken"),
            reported_by_name=data["reported_by_name"],
            witnesses=data.get("witnesses"),
        )
        return await self.repo.create_incident(incident)

    async def list_incidents(self) -> Sequence[Incident]:
        return await self.repo.list_incidents()

    # 5. Appointments
    async def create_appointment(self, data: dict[str, Any]) -> Appointment:
        appt = Appointment(
            title=data["title"],
            appointment_type=data.get("appointment_type", "General"),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"])
            if isinstance(data["scheduled_at"], str)
            else data["scheduled_at"],
            duration_minutes=int(data.get("duration_minutes", 60)),
            location=data.get("location"),
            client_id=uuid.UUID(data["client_id"]) if data.get("client_id") else None,
            case_id=uuid.UUID(data["case_id"]) if data.get("case_id") else None,
            status=data.get("status", "SCHEDULED"),
            notes=data.get("notes"),
        )
        return await self.repo.create_appointment(appt)

    async def list_appointments(self) -> Sequence[Appointment]:
        return await self.repo.list_appointments()
