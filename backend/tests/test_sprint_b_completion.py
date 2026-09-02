"""Automated Test Suite for Sprint B — Clinical Notes, Terminology, Communications & Legacy Modules."""

import uuid
from datetime import date, datetime

import pytest

from app.models.sprint_b_models import (
    Appointment,
    ClinicalNote,
    ClinicalNoteAddendum,
    FundingGrant,
    Incident,
    Program,
)
from app.permissions.constants import Permissions
from app.services.sprint_b_service import SprintBService


@pytest.mark.asyncio
async def test_clinical_note_lifecycle_locking_and_addenda(db_session):
    """Verify Clinical Note creation, locking immutability, and addendum attachment."""
    service = SprintBService(db_session)
    client_id = uuid.uuid4()
    author_id = uuid.uuid4()

    note_data = {
        "client_id": str(client_id),
        "note_type": "LPN_OBSERVATION",
        "subject": "Routine Vital Signs Check",
        "narrative": "Blood pressure 120/80, pulse 72. Client in good spirits.",
        "confidentiality": "CONFIDENTIAL",
    }
    note = await service.create_clinical_note(note_data, author_id=author_id)
    assert note.id is not None
    assert note.status == "DRAFT"

    # Lock note
    locked_note = await service.lock_clinical_note(note.id, user_id=author_id)
    assert locked_note.status == "LOCKED"
    assert locked_note.locked_at is not None

    from fastapi import HTTPException

    # Cannot lock already locked note
    with pytest.raises(HTTPException):
        await service.lock_clinical_note(note.id, user_id=author_id)

    # Attach addendum
    addendum = await service.add_clinical_addendum(
        note_id=note.id,
        narrative="Follow-up check 1 hour post-medication: Normal response.",
        author_id=author_id,
    )
    assert addendum.id is not None
    assert addendum.clinical_note_id == note.id


@pytest.mark.asyncio
async def test_programs_and_grants_crud(db_session):
    """Verify Program capacity tracking and FundingGrant CRUD operations."""
    service = SprintBService(db_session)

    # Program
    prog_data = {
        "name": "Sacred Wolf Mentorship Program",
        "category": "Youth Empowerment",
        "capacity": 25,
        "enrolled_count": 12,
        "budget": 45000.00,
    }
    prog = await service.create_program(prog_data)
    assert prog.id is not None
    assert prog.enrolled_count == 12

    programs = await service.list_programs()
    assert len(programs) >= 1

    # Funding Grant
    grant_data = {
        "grant_name": "Indigenous Youth Wellness Grant",
        "funder_name": "Federal Community Fund",
        "amount": 150000.00,
        "start_date": "2026-01-01",
        "end_date": "2026-12-31",
        "restrictions": "Strictly reserved for community cultural events",
    }
    grant = await service.create_grant(grant_data)
    assert grant.id is not None
    assert float(grant.amount) == 150000.00


@pytest.mark.asyncio
async def test_incidents_and_appointments_crud(db_session):
    """Verify General Incident reporting and Client Appointments CRUD operations."""
    service = SprintBService(db_session)
    client_id = uuid.uuid4()

    # Incident
    inc_data = {
        "title": "Facility Power Outage",
        "incident_type": "Facility / Safety",
        "severity": "MEDIUM",
        "client_id": str(client_id),
        "incident_date": datetime.utcnow().isoformat(),
        "location": "North Regional Shelter",
        "description": "Backup generator kicked in within 10 seconds.",
        "reported_by_name": "LPN Caretaker",
    }
    inc = await service.create_incident(inc_data)
    assert inc.id is not None
    assert inc.severity == "MEDIUM"

    # Appointment
    appt_data = {
        "title": "Pediatric Medical Exam",
        "appointment_type": "Medical Checkup",
        "scheduled_at": datetime.utcnow().isoformat(),
        "duration_minutes": 45,
        "client_id": str(client_id),
        "location": "Meadow Lake Health Center",
    }
    appt = await service.create_appointment(appt_data)
    assert appt.id is not None
    assert appt.duration_minutes == 45


def test_sprint_b_permission_constants():
    """Verify Sprint B capability permission strings."""
    assert Permissions.CLINICAL_NOTE_READ == "clinical.note.read"
    assert Permissions.CLINICAL_NOTE_CREATE == "clinical.note.create"
    assert Permissions.CLINICAL_NOTE_LOCK == "clinical.note.lock"
    assert Permissions.CLINICAL_NOTE_EXPORT == "clinical.note.export"
    assert Permissions.TERMINOLOGY_MANAGE == "terminology.manage"
    assert Permissions.COMMUNICATIONS_APPROVE == "communications.approve"
    assert Permissions.PROGRAM_MANAGE == "program.manage"
    assert Permissions.GRANT_MANAGE == "grant.manage"
    assert Permissions.INCIDENT_MANAGE == "incident.manage"
    assert Permissions.APPOINTMENT_MANAGE == "appointment.manage"
