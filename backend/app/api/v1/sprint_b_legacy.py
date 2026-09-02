"""FastAPI router for Programs, Funding Grants, Incidents, and Appointments."""

from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.services.sprint_b_service import SprintBService

router = APIRouter(tags=["Sprint B Legacy Modules"])


# 1. Programs Schemas
class ProgramCreate(BaseModel):
    name: str = Field(..., max_length=200)
    category: str = Field("Cultural Programs")
    status: str = Field("ACTIVE")
    description: str | None = None
    capacity: int = Field(20)
    enrolled_count: int = Field(0)
    location: str | None = None
    coordinator_name: str | None = None
    budget: float = Field(0.0)


# 2. Grant Schemas
class GrantCreate(BaseModel):
    grant_name: str = Field(..., max_length=200)
    funder_name: str = Field(..., max_length=200)
    amount: float = Field(...)
    status: str = Field("ACTIVE")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str | None = Field(None, description="YYYY-MM-DD")
    restrictions: str | None = None
    notes: str | None = None


# 3. Incident Schemas
class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=255)
    incident_type: str = Field("Critical Incident")
    severity: str = Field("MEDIUM")
    status: str = Field("OPEN")
    client_id: str | None = None
    case_id: str | None = None
    incident_date: str = Field(..., description="ISO Datetime string")
    location: str = Field(...)
    description: str = Field(...)
    actions_taken: str | None = None
    reported_by_name: str = Field(...)
    witnesses: str | None = None


# 4. Appointment Schemas
class AppointmentCreate(BaseModel):
    title: str = Field(..., max_length=255)
    appointment_type: str = Field("General")
    scheduled_at: str = Field(..., description="ISO Datetime string")
    duration_minutes: int = Field(60)
    location: str | None = None
    client_id: str | None = None
    case_id: str | None = None
    status: str = Field("SCHEDULED")
    notes: str | None = None


# ==========================================
# 1. PROGRAM ENDPOINTS
# ==========================================


@router.post("/programs", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_program(
    req: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.PROGRAM_MANAGE)),
):
    service = SprintBService(db)
    prog = await service.create_program(req.model_dump())
    return {"status": "SUCCESS", "id": str(prog.id), "name": prog.name}


@router.get("/programs", response_model=list[dict[str, Any]])
async def list_programs(
    db: AsyncSession = Depends(get_db),
):
    service = SprintBService(db)
    programs = await service.list_programs()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "category": p.category,
            "status": p.status,
            "description": p.description,
            "capacity": p.capacity,
            "enrolled_count": p.enrolled_count,
            "location": p.location,
            "coordinator_name": p.coordinator_name,
            "budget": float(p.budget),
        }
        for p in programs
    ]


# ==========================================
# 2. FUNDING GRANT ENDPOINTS
# ==========================================


@router.post("/grants", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_grant(
    req: GrantCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.GRANT_MANAGE)),
):
    service = SprintBService(db)
    grant = await service.create_grant(req.model_dump())
    return {"status": "SUCCESS", "id": str(grant.id), "grant_name": grant.grant_name}


@router.get("/grants", response_model=list[dict[str, Any]])
async def list_grants(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.GRANT_MANAGE)),
):
    service = SprintBService(db)
    grants = await service.list_grants()
    return [
        {
            "id": str(g.id),
            "grant_name": g.grant_name,
            "funder_name": g.funder_name,
            "amount": float(g.amount),
            "status": g.status,
            "start_date": g.start_date.isoformat(),
            "end_date": g.end_date.isoformat() if g.end_date else None,
            "restrictions": g.restrictions,
        }
        for g in grants
    ]


# ==========================================
# 3. INCIDENT ENDPOINTS
# ==========================================


@router.post("/incidents", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_incident(
    req: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.INCIDENT_MANAGE)),
):
    service = SprintBService(db)
    inc = await service.create_incident(req.model_dump())
    return {"status": "SUCCESS", "id": str(inc.id), "title": inc.title, "severity": inc.severity}


@router.get("/incidents", response_model=list[dict[str, Any]])
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.INCIDENT_MANAGE)),
):
    service = SprintBService(db)
    incidents = await service.list_incidents()
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "incident_type": i.incident_type,
            "severity": i.severity,
            "status": i.status,
            "client_id": str(i.client_id) if i.client_id else None,
            "case_id": str(i.case_id) if i.case_id else None,
            "incident_date": i.incident_date.isoformat(),
            "location": i.location,
            "description": i.description,
            "reported_by_name": i.reported_by_name,
        }
        for i in incidents
    ]


# ==========================================
# 4. APPOINTMENT ENDPOINTS
# ==========================================


@router.post("/appointments", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_appointment(
    req: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.APPOINTMENT_MANAGE)),
):
    service = SprintBService(db)
    appt = await service.create_appointment(req.model_dump())
    return {"status": "SUCCESS", "id": str(appt.id), "title": appt.title}


@router.get("/appointments", response_model=list[dict[str, Any]])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
):
    service = SprintBService(db)
    appointments = await service.list_appointments()
    return [
        {
            "id": str(a.id),
            "title": a.title,
            "appointment_type": a.appointment_type,
            "scheduled_at": a.scheduled_at.isoformat(),
            "duration_minutes": a.duration_minutes,
            "location": a.location,
            "client_id": str(a.client_id) if a.client_id else None,
            "case_id": str(a.case_id) if a.case_id else None,
            "status": a.status,
        }
        for a in appointments
    ]
