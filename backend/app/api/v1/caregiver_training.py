"""REST API router for Caregiver Training compliance and verification."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.caregiver_training import (
    CaregiverTrainingCreate,
    CaregiverTrainingListResponse,
    CaregiverTrainingResponse,
    CaregiverTrainingUpdate,
    CaregiverTrainingVerify,
    HomeTrainingComplianceSummary,
)
from app.services.caregiver_training_service import CaregiverTrainingService

router = APIRouter(prefix="/caregiver-trainings", tags=["Caregiver Training"])


@router.post("", response_model=CaregiverTrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_caregiver_training(
    payload: CaregiverTrainingCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CaregiverTrainingResponse:
    """Record a training completion for a caregiver Person."""
    service = CaregiverTrainingService(db)
    training = await service.create_training(current_user, payload)
    return CaregiverTrainingResponse.model_validate(training)


@router.get("", response_model=CaregiverTrainingListResponse)
async def list_caregiver_trainings(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    person_id: uuid.UUID | None = Query(None),
    placement_home_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    training_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> CaregiverTrainingListResponse:
    """List caregiver training records with filters and pagination."""
    service = CaregiverTrainingService(db)
    items, total = await service.list_trainings(
        current_user,
        person_id=person_id,
        placement_home_id=placement_home_id,
        status_filter=status_filter,
        training_type=training_type,
        page=page,
        page_size=page_size,
    )
    return CaregiverTrainingListResponse(
        items=[CaregiverTrainingResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/home/{placement_home_id}/compliance", response_model=HomeTrainingComplianceSummary)
async def get_home_training_compliance(
    placement_home_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> HomeTrainingComplianceSummary:
    """Get authoritative training compliance summary for all caregivers in a Resource Home."""
    service = CaregiverTrainingService(db)
    return await service.get_home_training_compliance(current_user, placement_home_id)


@router.get("/{training_id}", response_model=CaregiverTrainingResponse)
async def get_caregiver_training(
    training_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CaregiverTrainingResponse:
    """Retrieve details of a single caregiver training record."""
    service = CaregiverTrainingService(db)
    training = await service.get_training(current_user, training_id)
    return CaregiverTrainingResponse.model_validate(training)


@router.patch("/{training_id}", response_model=CaregiverTrainingResponse)
async def update_caregiver_training(
    training_id: uuid.UUID,
    payload: CaregiverTrainingUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CaregiverTrainingResponse:
    """Update a caregiver training record."""
    service = CaregiverTrainingService(db)
    training = await service.update_training(current_user, training_id, payload)
    return CaregiverTrainingResponse.model_validate(training)


@router.post("/{training_id}/verify", response_model=CaregiverTrainingResponse)
async def verify_caregiver_training(
    training_id: uuid.UUID,
    payload: CaregiverTrainingVerify,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CaregiverTrainingResponse:
    """Supervisory verification of caregiver training completion (Resource Supervisor / Director only)."""
    service = CaregiverTrainingService(db)
    training = await service.verify_training(current_user, training_id, payload)
    return CaregiverTrainingResponse.model_validate(training)


@router.delete("/{training_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_caregiver_training(
    training_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Soft delete a caregiver training record."""
    service = CaregiverTrainingService(db)
    await service.delete_training(current_user, training_id)
