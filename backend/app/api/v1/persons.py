"""Canonical Person endpoints with comprehensive profile consolidation and duplicate prevention."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_any_permission
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.schemas.person import (
    PersonCreate,
    PersonDuplicateCheckRequest,
    PersonDuplicateCheckResponse,
    PersonProfileResponse,
    PersonResponse,
    PersonSearchResultResponse,
    PersonUpdate,
)
from app.services.person_service import PersonService

router = APIRouter(prefix="/persons", tags=["Persons"])


@router.get("", response_model=PaginatedResponse[PersonSearchResultResponse])
async def list_persons(
    query: str | None = Query(default=None, description="Search by name, aliases, or digits"),
    person_id_number: str | None = Query(default=None, description="Exact or prefix Person ID number"),
    date_of_birth: str | None = Query(default=None, description="YYYY-MM-DD"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_READ, Permissions.CASE_PEOPLE_READ, Permissions.INTAKE_READ
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Search canonical person records by name, numeric Person ID, or date of birth. Returns limited matching fields."""
    service = PersonService(db)
    await service.assert_person_role_authorized(user, "search")
    items, total = await service.person_repo.search_people(
        query_text=query,
        person_id_number=person_id_number,
        date_of_birth=date_of_birth,
        limit=limit,
        offset=offset,
    )
    return PaginatedResponse[PersonSearchResultResponse](
        items=[PersonSearchResultResponse.model_validate(p) for p in items],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.post("", response_model=PersonResponse, status_code=status.HTTP_201_CREATED)
async def create_person(
    payload: PersonCreate,
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_CREATE, Permissions.CASE_PEOPLE_WRITE, Permissions.INTAKE_CREATE
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Create a new canonical Person with automatic 10-digit numeric CRBCL Person ID."""
    service = PersonService(db)
    await service.assert_person_role_authorized(user, "create")
    person = await service.create_person(payload, current_user_id=user.id)
    await db.commit()
    return PersonResponse.model_validate(person)


@router.post("/duplicate-check", response_model=PersonDuplicateCheckResponse)
async def duplicate_check(
    body: PersonDuplicateCheckRequest,
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_READ, Permissions.CASE_PEOPLE_READ, Permissions.INTAKE_READ
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Check for potential duplicate identities using fuzzy scoring and Person ID."""
    service = PersonService(db)
    await service.assert_person_role_authorized(user, "check duplicates against")
    return await service.check_duplicates(body)


@router.get("/{person_id}", response_model=PersonProfileResponse)
async def get_person_profile(
    person_id: uuid.UUID,
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_READ, Permissions.CASE_PEOPLE_READ, Permissions.INTAKE_READ
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve comprehensive canonical Person profile consolidating physical description,
    contacts, addresses, family relationships, cases, referrals, placements,
    background checks, documents, timeline, and permission-checked health data.
    """
    service = PersonService(db)
    return await service.get_comprehensive_profile(person_id, current_user=user)


@router.patch("/{person_id}", response_model=PersonResponse)
async def update_person(
    person_id: uuid.UUID,
    payload: PersonUpdate,
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_UPDATE, Permissions.CASE_PEOPLE_WRITE, Permissions.INTAKE_UPDATE
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Update Person demographics and sub-profiles. Person ID is permanent and immutable."""
    service = PersonService(db)
    person = await service.update_person(person_id, payload, current_user=user)
    await db.commit()
    return PersonResponse.model_validate(person)


@router.post("/{person_id}/photo")
async def upload_person_photo(
    person_id: uuid.UUID,
    file: UploadFile = File(...),
    user: User = Depends(
        require_any_permission(
            Permissions.CLIENT_UPDATE, Permissions.CASE_PEOPLE_WRITE, Permissions.INTAKE_UPDATE
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    """Upload and attach a secure profile photograph to a canonical Person."""
    content = await file.read()
    service = PersonService(db)
    url = await service.upload_photo(
        person_id=person_id,
        filename=file.filename or "profile_photo.jpg",
        content=content,
        content_type=file.content_type or "image/jpeg",
        current_user=user,
    )
    await db.commit()
    return {"photo_url": url}
