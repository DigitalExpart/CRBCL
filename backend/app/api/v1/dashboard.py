"""Customizable Dashboard API Router (Phase 11)."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import get_current_user_permissions, require_permission
from app.schemas.reporting_qa import WidgetLayoutInput
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Custom User Dashboards"])


@router.get(
    "/user-layout",
    dependencies=[Depends(require_permission(Permissions.DASHBOARD_CUSTOMIZE))],
)
async def get_user_dashboard_layout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DASHBOARD_CUSTOMIZE)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    """Return user's customized drag/drop widget layout and authorized metric data."""
    return await DashboardService.get_user_dashboard(db, user_id=current_user.id, user_permissions=user_perms)


@router.post(
    "/layout",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_permission(Permissions.DASHBOARD_CUSTOMIZE))],
)
async def save_user_dashboard_layout(
    layout: list[WidgetLayoutInput],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DASHBOARD_CUSTOMIZE)),
):
    """Save updated widget layout ordering and positions for current user."""
    w_data = [item.model_dump() for item in layout]
    return await DashboardService.save_user_layout(db, user_id=current_user.id, layout_data=w_data)
