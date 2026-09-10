"""API Router for Resource Complaints & Investigations (Sprint 3)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resource_complaint import (
    ResourceComplaintBasicResponse,
    ResourceComplaintCreate,
    ResourceComplaintDisposition,
    ResourceComplaintInvestigationUpdate,
    ResourceComplaintSensitiveResponse,
)
from app.services.resource_complaint_service import ResourceComplaintService

router = APIRouter(prefix="/resource-complaints", tags=["Resource Complaints & Investigations"])


@router.post(
    "",
    response_model=ResourceComplaintBasicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new complaint against a Resource Home",
)
@router.post(
    "/",
    response_model=ResourceComplaintBasicResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_complaint(
    payload: ResourceComplaintCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceComplaintBasicResponse:
    service = ResourceComplaintService(session)
    return await service.create_complaint(payload, user)


@router.get(
    "",
    response_model=dict,
    summary="List complaints (basic redacted view)",
)
@router.get(
    "/",
    response_model=dict,
    include_in_schema=False,
)
async def list_complaints(
    home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    placement_home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    status: str | None = Query(None, description="Filter by status"),
    severity: str | None = Query(None, description="Filter by severity"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = ResourceComplaintService(session)
    items, total = await service.list_complaints(
        user=user,
        home_id=placement_home_id or home_id,
        status=status,
        severity=severity,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [item.model_dump() for item in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{complaint_id}",
    response_model=ResourceComplaintSensitiveResponse,
    summary="Get sensitive complaint details, activities, and findings",
    description="Requires resource_complaint.sensitive.read permission. IT admin denied.",
)
async def get_complaint_detail(
    complaint_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceComplaintSensitiveResponse:
    service = ResourceComplaintService(session)
    return await service.get_complaint_detail(complaint_id, user)


@router.patch(
    "/{complaint_id}/investigation",
    response_model=ResourceComplaintSensitiveResponse,
    summary="Update investigation progress, activity log, and findings",
    description="Requires resource_complaint.manage permission. Finalized findings are immutable.",
)
async def update_investigation(
    complaint_id: uuid.UUID,
    payload: ResourceComplaintInvestigationUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceComplaintSensitiveResponse:
    service = ResourceComplaintService(session)
    return await service.update_investigation(complaint_id, payload, user)


@router.post(
    "/{complaint_id}/disposition",
    response_model=ResourceComplaintSensitiveResponse,
    summary="Conclude investigation and record formal disposition",
    description="Requires resource_complaint.disposition permission (Resource Director).",
)
async def record_disposition(
    complaint_id: uuid.UUID,
    payload: ResourceComplaintDisposition,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceComplaintSensitiveResponse:
    service = ResourceComplaintService(session)
    return await service.record_disposition(complaint_id, payload, user)
