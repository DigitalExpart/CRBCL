"""API Router for Caregiver and Resource Home Supports (Sprint 3)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.caregiver_support import (
    CaregiverSupportCreate,
    CaregiverSupportResponse,
    CaregiverSupportUpdate,
)
from app.services.caregiver_support_service import CaregiverSupportService

router = APIRouter(prefix="/caregiver-supports", tags=["Caregiver Supports"])


@router.post(
    "",
    response_model=CaregiverSupportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request or log caregiver support",
)
@router.post(
    "/",
    response_model=CaregiverSupportResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_support(
    payload: CaregiverSupportCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CaregiverSupportResponse:
    service = CaregiverSupportService(session)
    return await service.create_support(payload, user)


@router.get(
    "",
    response_model=dict,
    summary="List caregiver supports with filtering and pagination",
)
@router.get(
    "/",
    response_model=dict,
    include_in_schema=False,
)
async def list_supports(
    home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    placement_home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    support_type: str | None = Query(None, description="Filter by support type"),
    status: str | None = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = CaregiverSupportService(session)
    items, total = await service.list_supports(
        user=user,
        home_id=placement_home_id or home_id,
        support_type=support_type,
        status=status,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.patch(
    "/{support_id}",
    response_model=CaregiverSupportResponse,
    summary="Update caregiver support delivery status or notes",
)
async def update_support(
    support_id: uuid.UUID,
    payload: CaregiverSupportUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> CaregiverSupportResponse:
    service = CaregiverSupportService(session)
    return await service.update_support(support_id, payload, user)
