"""Lookup list endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.lookup import LookupValueResponse
from app.services.config_service import ConfigService

router = APIRouter(prefix="/lookups", tags=["Lookups"])


@router.get("/{list_key}", response_model=list[LookupValueResponse])
async def get_lookup_values(
    list_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all active values for a lookup list (e.g. case_statuses, risk_levels)."""
    service = ConfigService(db)
    values = await service.get_lookup_values(list_key, active_only=True)
    if not values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "LOOKUP_LIST_NOT_FOUND", "message": f"Lookup list '{list_key}' not found"}},
        )
    return [LookupValueResponse.model_validate(v) for v in values]
