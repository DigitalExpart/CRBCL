"""API Router for Placement Matching Assistive Decision Support (Sprint 3)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement_matching import ChildPlacementProfile, PlacementMatchResponse
from app.services.placement_matching_service import PlacementMatchingService

router = APIRouter(prefix="/placement-matching", tags=["Placement Matching"])


@router.post(
    "/evaluate",
    response_model=PlacementMatchResponse,
    summary="Evaluate eligible Resource Homes for a child",
    description=(
        "Returns explainable matching factors, warnings, and exclusions. "
        "Assistive decision support only; final placement requires manual PlacementEpisode authorization."
    ),
)
async def evaluate_placement_matches(
    profile: ChildPlacementProfile,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PlacementMatchResponse:
    service = PlacementMatchingService(session)
    return await service.evaluate_matches(profile, user)
