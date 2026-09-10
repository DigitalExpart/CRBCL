"""API Router for Resource Unit Strategic Outcomes (Sprint 3)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resource_outcomes import StrategicOutcomesMetrics
from app.services.resource_outcomes_service import ResourceOutcomesService

router = APIRouter(prefix="/resource-outcomes", tags=["Resource Unit Strategic Outcomes"])


@router.get(
    "",
    response_model=StrategicOutcomesMetrics,
    summary="Get authoritative strategic outcomes and retention indicators",
    description="Requires resource_outcomes.read permission.",
)
@router.get(
    "/",
    response_model=StrategicOutcomesMetrics,
    include_in_schema=False,
)
async def get_strategic_outcomes(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> StrategicOutcomesMetrics:
    service = ResourceOutcomesService(session)
    return await service.get_strategic_outcomes(user)
