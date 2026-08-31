"""Team endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.team_repo import TeamRepository
from app.schemas.team import TeamResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=list[TeamResponse])
async def list_teams(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active teams."""
    repo = TeamRepository(db)
    teams = await repo.list_active_teams()
    return [TeamResponse.model_validate(t) for t in teams]


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get team details by ID."""
    repo = TeamRepository(db)
    team = await repo.get(team_id)
    if not team or not team.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "TEAM_NOT_FOUND", "message": "Team not found"}},
        )
    return TeamResponse.model_validate(team)
