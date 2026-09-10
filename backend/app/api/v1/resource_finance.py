"""API Router for Resource Finance Integration (Sprint 3)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.resource_finance import ResourceFinanceSummary
from app.services.resource_finance_service import ResourceFinanceService

router = APIRouter(prefix="/resource-finance", tags=["Resource Finance Integration"])


@router.get(
    "/homes/{home_id}",
    response_model=ResourceFinanceSummary,
    summary="Get authorized financial roll-up for a Resource Home",
    description="Requires finance.request.read or finance.invoice.read permission.",
)
async def get_home_finance_summary(
    home_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ResourceFinanceSummary:
    service = ResourceFinanceService(session)
    return await service.get_home_finance_summary(home_id, user)
