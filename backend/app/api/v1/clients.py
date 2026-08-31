"""Client management endpoints with comprehensive Phase 2 sub-profiles, duplicate detection, and field-level permissions."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.core.database import get_db
from app.models.person import (
    PersonAddress,
)
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.repositories.client_repo import ClientRepository
from app.repositories.medical_repo import MedicalRepository
from app.repositories.person_repo import PersonRepository
from app.repositories.provider_repo import ProviderRepository
from app.repositories.school_repo import SchoolRepository
from app.schemas.client import ClientCreate, ClientResponse, ClientUpdate
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.duplicate_service import DuplicateService
from app.services.merge_service import MergeService
from app.workflows.timeline import TimelineEventType, TimelineService

router = APIRouter(prefix="/clients", tags=["Clients"])


# ── Phase 2 Schemas ──────────────────────────────────────────


class DuplicateCheckRequest(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str | None = None
    treaty_number: str | None = None
    health_card_number: str | None = None
    phone: str | None = None
    email: str | None = None


class MergeRequest(BaseModel):
    source_person_id: uuid.UUID
    target_person_id: uuid.UUID
    reason: str
    notes: str = ""


class AddressCreate(BaseModel):
    address_type: str = "Residential"
    address_line_1: str
    address_line_2: str | None = None
    city: str = "Regina"
    province: str = "Saskatchewan"
    postal_code: str | None = None
    on_reserve: bool = False
    latitude: float | None = None
    longitude: float | None = None
    is_primary: bool = True
    valid_from: date | None = None
    valid_to: date | None = None


class AllergyCreate(BaseModel):
    allergen: str
    reaction: str = ""
    severity: str = "Moderate"
    is_active: bool = True
    notes: str | None = None


class ConditionCreate(BaseModel):
    condition_name: str
    diagnosed_date: date | None = None
    is_chronic: bool = False
    is_active: bool = True
    treatment_plan: str | None = None
    notes: str | None = None


class MedicationCreate(BaseModel):
    medication_name: str
    dosage: str
    frequency: str
    route: str = "Oral"
    prescriber_id: uuid.UUID | None = None
    prescriber_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str = "Active"
    instructions: str | None = None
    notes: str | None = None


class MedicalProfileUpdate(BaseModel):
    dental_notes: str | None = None
    mental_health_notes: str | None = None
    chemical_dependency_history: str | None = None
    general_notes: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None


class ProviderLinkCreate(BaseModel):
    provider_id: uuid.UUID
    role: str = "Primary Care"
    start_date: date | None = None
    end_date: date | None = None
    notes: str = ""


class SchoolEnrollmentCreate(BaseModel):
    school_id: uuid.UUID
    grade_level: str = "Grade 1"
    start_date: date | None = None
    has_iep: bool = False
    iep_details: str | None = None
    school_contact_person: str | None = None
    attendance_concerns: str | None = None
    notes: str | None = None


class StrengthCreate(BaseModel):
    name: str
    notes: str | None = None


class ChallengeCreate(BaseModel):
    name: str
    severity: str = "Moderate"
    is_active: bool = True
    notes: str | None = None


class CulturalProfileUpdate(BaseModel):
    cultural_connections: str | None = None
    ceremonies: str | None = None
    elders_connected: str | None = None
    land_based_activities: str | None = None
    language_goals: str | None = None
    dietary_preferences: str | None = None
    extracurricular_activities: str | None = None
    notes: str | None = None


# ── Client Base Endpoints ────────────────────────────────────


@router.get("", response_model=PaginatedResponse[ClientResponse])
async def list_clients(
    request: Request,
    query: str | None = Query(default=None, description="Search by name, email, phone"),
    status_filter: str | None = Query(default=None, alias="status"),
    risk_level: str | None = Query(default=None),
    team_id: uuid.UUID | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sort: str | None = Query(default=None),
    user: User = Depends(require_permission(Permissions.CLIENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    perm_service = PermissionService(db)
    accessible_team_ids = await perm_service.get_user_accessible_team_ids(user.id)

    repo = ClientRepository(db)
    clients, total = await repo.search(
        query_text=query,
        status=status_filter,
        risk_level=risk_level,
        team_id=team_id,
        accessible_team_ids=accessible_team_ids,
        offset=offset,
        limit=limit,
        sort_by=sort,
    )

    return PaginatedResponse[ClientResponse](
        items=[ClientResponse.model_validate(c) for c in clients],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.post("/duplicate-check")
async def duplicate_check(
    body: DuplicateCheckRequest,
    user: User = Depends(require_permission(Permissions.CLIENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    """Check potential duplicate persons before creating a client."""
    service = DuplicateService(db)
    candidates = await service.check_duplicates(
        first_name=body.first_name,
        last_name=body.last_name,
        date_of_birth=body.date_of_birth,
        treaty_number=body.treaty_number,
        health_card_number=body.health_card_number,
        phone=body.phone,
        email=body.email,
    )
    return {"has_potential_duplicates": len(candidates) > 0, "candidates": candidates}


@router.post("/merge")
async def merge_duplicate_persons(
    body: MergeRequest,
    user: User = Depends(require_permission(Permissions.ADMIN_CONFIGURATION_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Perform controlled person merge with audit logging."""
    service = MergeService(db)
    merge_record = await service.merge_persons(
        source_person_id=body.source_person_id,
        target_person_id=body.target_person_id,
        merged_by=user.id,
        reason=body.reason,
        notes=body.notes,
    )
    await db.commit()
    return {"success": True, "merge_id": str(merge_record.id), "merged_at": merge_record.merged_at}


@router.get("/{client_id}")
async def get_client(
    client_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_permission(Permissions.CLIENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(db)
    client = await repo.get(client_id)
    if not client or client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CLIENT_NOT_FOUND", "message": "Client not found"}},
        )

    perm_service = PermissionService(db)
    can_access = await perm_service.user_can_access_team(user.id, client.assigned_team_id)
    if not can_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "TEAM_ACCESS_DENIED",
                    "message": "Access to this client is restricted to their assigned team",
                }
            },
        )

    # Log sensitive read access event
    audit_service = AuditService(db)
    await audit_service.log_access(
        event_type="CLIENT_PROFILE_VIEWED",
        user_id=user.id,
        entity_type="client",
        entity_id=client.id,
        description=f"Viewed profile of client {client.first_name} {client.last_name}",
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()

    # Load canonical person if linked
    person_data = None
    if client.person_id:
        person_repo = PersonRepository(db)
        person_model = await person_repo.get_full(client.person_id)
        if person_model:
            person_data = {
                "id": str(person_model.id),
                "first_name": person_model.first_name,
                "middle_name": person_model.middle_name,
                "last_name": person_model.last_name,
                "preferred_name": person_model.preferred_name,
                "aliases": person_model.aliases,
                "date_of_birth": str(person_model.date_of_birth) if person_model.date_of_birth else None,
                "gender": person_model.gender,
                "photo_url": person_model.photo_url,
                "place_of_birth": person_model.place_of_birth,
                "preferred_language": person_model.preferred_language,
                "languages_spoken": person_model.languages_spoken,
                "treaty_number": person_model.treaty_number,
                "band_nation": person_model.band_nation,
                "indigenous_identity": person_model.indigenous_identity,
                "health_card_number": person_model.health_card_number,
                "phone": person_model.phone,
                "email": person_model.email,
                "emergency_contact_name": person_model.emergency_contact_name,
                "emergency_contact_phone": person_model.emergency_contact_phone,
                "source_of_income": person_model.source_of_income,
                "employment_status": person_model.employment_status,
                "employer": person_model.employer,
                "addresses": [
                    {
                        "id": str(a.id),
                        "address_type": a.address_type,
                        "address_line_1": a.address_line_1,
                        "city": a.city,
                        "province": a.province,
                        "postal_code": a.postal_code,
                        "on_reserve": a.on_reserve,
                        "latitude": a.latitude,
                        "longitude": a.longitude,
                        "is_primary": a.is_primary,
                    }
                    for a in person_model.addresses
                ],
                "physical_description": {
                    "eye_colour": person_model.physical_description.eye_colour,
                    "hair_colour": person_model.physical_description.hair_colour,
                    "height_cm": person_model.physical_description.height_cm,
                    "weight_kg": person_model.physical_description.weight_kg,
                    "tattoos": person_model.physical_description.tattoos,
                    "piercings": person_model.physical_description.piercings,
                    "scars": person_model.physical_description.scars,
                    "glasses": person_model.physical_description.glasses,
                }
                if person_model.physical_description
                else None,
                "cultural_profile": {
                    "cultural_connections": person_model.cultural_profile.cultural_connections,
                    "ceremonies": person_model.cultural_profile.ceremonies,
                    "elders_connected": person_model.cultural_profile.elders_connected,
                    "land_based_activities": person_model.cultural_profile.land_based_activities,
                    "language_goals": person_model.cultural_profile.language_goals,
                }
                if person_model.cultural_profile
                else None,
            }

    data = ClientResponse.model_validate(client).model_dump()
    data["person"] = person_data
    return data


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    request: Request,
    user: User = Depends(require_permission(Permissions.CLIENT_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(db)
    person_repo = PersonRepository(db)

    # 1. Create Canonical Person record
    person = await person_repo.create(
        first_name=payload.first_name,
        last_name=payload.last_name,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        phone=payload.phone,
        email=payload.email,
        indigenous_identity=payload.indigenous_identity,
        band_nation=payload.band_nation,
        created_by=user.id,
        updated_by=user.id,
    )

    # 2. If address provided, create primary address entry
    if payload.address:
        addr = PersonAddress(
            person_id=person.id,
            address_line_1=payload.address,
            city=payload.city or "Regina",
            province=payload.province or "Saskatchewan",
            is_primary=True,
        )
        db.add(addr)

    # 3. Create Client record linked to person
    client_data = payload.model_dump()
    client_data["person_id"] = person.id
    client_data["created_by"] = user.id
    client_data["updated_by"] = user.id

    client = await repo.create(**client_data)

    # 4. Audit & Timeline
    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="CLIENT_CREATED",
        user_id=user.id,
        entity_type="client",
        entity_id=client.id,
        after_data=payload.model_dump(mode="json"),
        ip_address=request.client.host if request.client else None,
    )

    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=TimelineEventType.CLIENT_CREATED,
        title=f"Client Profile Created: {client.first_name} {client.last_name}",
        description=f"Initial registration status: {client.status}, Risk Level: {client.risk_level}",
        entity_type="client",
        entity_id=client.id,
        client_id=client.id,
        created_by=user.id,
    )

    await db.commit()
    return ClientResponse.model_validate(client)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: uuid.UUID,
    payload: ClientUpdate,
    request: Request,
    user: User = Depends(require_permission(Permissions.CLIENT_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ClientRepository(db)
    client = await repo.get(client_id)
    if not client or client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "CLIENT_NOT_FOUND", "message": "Client not found"}},
        )

    perm_service = PermissionService(db)
    if not await perm_service.user_can_access_team(user.id, client.assigned_team_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "TEAM_ACCESS_DENIED", "message": "Unauthorized to update this client"}},
        )

    before_data = ClientResponse.model_validate(client).model_dump(mode="json")
    update_data = payload.model_dump(exclude_unset=True)
    update_data["updated_by"] = user.id

    updated_client = await repo.update(client, **update_data)

    # Sync demographic changes to canonical Person if linked
    if client.person_id:
        person_repo = PersonRepository(db)
        person = await person_repo.get(client.person_id)
        if person:
            person_fields = [
                "first_name",
                "last_name",
                "date_of_birth",
                "gender",
                "phone",
                "email",
                "indigenous_identity",
                "band_nation",
            ]
            for field in person_fields:
                if field in update_data and update_data[field] is not None:
                    setattr(person, field, update_data[field])

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="CLIENT_UPDATED",
        user_id=user.id,
        entity_type="client",
        entity_id=client.id,
        before_data=before_data,
        after_data=update_data,
        ip_address=request.client.host if request.client else None,
    )

    timeline_service = TimelineService(db)
    await timeline_service.record_event(
        event_type=TimelineEventType.CLIENT_UPDATED,
        title=f"Client Profile Updated: {client.first_name} {client.last_name}",
        description="Fields updated: " + ", ".join(update_data.keys()),
        entity_type="client",
        entity_id=client.id,
        client_id=client.id,
        created_by=user.id,
    )

    await db.commit()
    return ClientResponse.model_validate(updated_client)


# ── Sub-Resource Routes (Medical, Medications, Providers, Schools, etc.) ──


@router.get("/{client_id}/medical")
async def get_client_medical(
    client_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CLIENT_MEDICAL_READ)),
    db: AsyncSession = Depends(get_db),
):
    med_repo = MedicalRepository(db)
    profile = await med_repo.get_or_create_profile(client_id)
    allergies = await med_repo.list_allergies(client_id)
    conditions = await med_repo.list_conditions(client_id)
    medications = await med_repo.list_medications(client_id)

    return {
        "profile": profile,
        "allergies": allergies,
        "conditions": conditions,
        "medications": medications,
    }


@router.patch("/{client_id}/medical")
async def update_client_medical_profile(
    client_id: uuid.UUID,
    payload: MedicalProfileUpdate,
    user: User = Depends(require_permission(Permissions.CLIENT_MEDICAL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    med_repo = MedicalRepository(db)
    profile = await med_repo.update_profile(client_id, **payload.model_dump(exclude_unset=True))
    await db.commit()
    return profile


@router.post("/{client_id}/allergies", status_code=status.HTTP_201_CREATED)
async def add_client_allergy(
    client_id: uuid.UUID,
    payload: AllergyCreate,
    user: User = Depends(require_permission(Permissions.CLIENT_MEDICAL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    med_repo = MedicalRepository(db)
    allergy = await med_repo.add_allergy(client_id, **payload.model_dump())
    await db.commit()
    return allergy


@router.post("/{client_id}/conditions", status_code=status.HTTP_201_CREATED)
async def add_client_condition(
    client_id: uuid.UUID,
    payload: ConditionCreate,
    user: User = Depends(require_permission(Permissions.CLIENT_MEDICAL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    med_repo = MedicalRepository(db)
    condition = await med_repo.add_condition(client_id, **payload.model_dump())
    await db.commit()
    return condition


@router.post("/{client_id}/medications", status_code=status.HTTP_201_CREATED)
async def add_client_medication(
    client_id: uuid.UUID,
    payload: MedicationCreate,
    user: User = Depends(require_permission(Permissions.CLIENT_MEDICAL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    med_repo = MedicalRepository(db)
    medication = await med_repo.add_medication(client_id, **payload.model_dump())

    timeline = TimelineService(db)
    await timeline.record_event(
        event_type="MEDICATION_STARTED",
        title=f"Medication Prescribed: {medication.medication_name}",
        description=f"Dosage: {medication.dosage}, Frequency: {medication.frequency}",
        entity_type="client",
        entity_id=client_id,
        client_id=client_id,
        created_by=user.id,
    )

    await db.commit()
    return medication


@router.get("/{client_id}/providers")
async def get_client_providers(
    client_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.PROVIDER_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    links = await repo.list_client_providers(client_id)
    return links


@router.post("/{client_id}/providers", status_code=status.HTTP_201_CREATED)
async def link_client_provider(
    client_id: uuid.UUID,
    payload: ProviderLinkCreate,
    user: User = Depends(require_permission(Permissions.PROVIDER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = ProviderRepository(db)
    link = await repo.link_client_provider(
        client_id=client_id,
        provider_id=payload.provider_id,
        role=payload.role,
        notes=payload.notes,
    )
    await db.commit()
    return link


@router.get("/{client_id}/schools")
async def get_client_schools(
    client_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CLIENT_SCHOOL_READ)),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolRepository(db)
    enrolments = await repo.list_client_enrolments(client_id)
    return enrolments


@router.post("/{client_id}/schools", status_code=status.HTTP_201_CREATED)
async def enroll_client_school(
    client_id: uuid.UUID,
    payload: SchoolEnrollmentCreate,
    user: User = Depends(require_permission(Permissions.CLIENT_SCHOOL_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    repo = SchoolRepository(db)
    enrolment = await repo.enroll_client(
        client_id=client_id,
        school_id=payload.school_id,
        grade_level=payload.grade_level,
        start_date=payload.start_date,
        has_iep=payload.has_iep,
        iep_details=payload.iep_details,
        school_contact_person=payload.school_contact_person,
        attendance_concerns=payload.attendance_concerns,
        notes=payload.notes,
    )
    await db.commit()
    return enrolment


@router.get("/{client_id}/timeline")
async def get_client_timeline(
    client_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.TIMELINE_READ)),
    db: AsyncSession = Depends(get_db),
):
    timeline_service = TimelineService(db)
    events = await timeline_service.get_timeline_for_entity("client", client_id)
    return events
