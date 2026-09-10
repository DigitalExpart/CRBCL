"""API Router for Resource Home Monitoring Visits (Sprint 3)."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resource_monitoring import (
    ResourceHomeMonitoringCreate,
    ResourceHomeMonitoringResponse,
)
from app.services.resource_monitoring_service import ResourceMonitoringService

router = APIRouter(prefix="/resource-monitoring", tags=["Resource Home Monitoring"])


@router.post(
    "",
    response_model=ResourceHomeMonitoringResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record an ongoing monitoring visit",
)
@router.post(
    "/",
    response_model=ResourceHomeMonitoringResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
async def create_monitoring_visit(
    payload: ResourceHomeMonitoringCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceHomeMonitoringResponse:
    service = ResourceMonitoringService(session)
    return await service.create_monitoring_visit(payload, user)


@router.get(
    "",
    response_model=dict,
    summary="List monitoring visits with filtering and pagination",
)
@router.get(
    "/",
    response_model=dict,
    include_in_schema=False,
)
async def list_monitoring_visits(
    home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    placement_home_id: uuid.UUID | None = Query(None, description="Filter by Placement Home ID"),
    status: str | None = Query(None, description="Filter by status (SCHEDULED, COMPLETED, CANCELLED)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = ResourceMonitoringService(session)
    items, total = await service.list_monitoring_visits(
        user=user,
        home_id=placement_home_id or home_id,
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


@router.get(
    "/overdue-count",
    response_model=dict,
    summary="Count of active homes with overdue periodic monitoring",
)
async def get_overdue_monitoring_count(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    service = ResourceMonitoringService(session)
    count = await service.get_overdue_monitoring_homes_count()
    return {"overdue_homes_count": count}
