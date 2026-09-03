from typing import Any

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.dependencies import get_current_user_permissions
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Custom User Dashboards"])


@router.get("/user-layout")
async def get_user_dashboard_layout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    """Return user's customized drag/drop widget layout and authorized metric data."""
    return await DashboardService.get_user_dashboard(db, user_id=current_user.id, user_permissions=user_perms)


@router.post("/layout", status_code=status.HTTP_200_OK)
async def save_user_dashboard_layout(
    payload: Any = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save updated widget layout ordering and positions for current user."""
    items = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        items = payload.get("widgets") or payload.get("layout") or []

    w_data = []
    for item in items:
        if isinstance(item, dict):
            w_data.append(
                {
                    "widget_key": item.get("widget_key"),
                    "position": item.get("position", item.get("position_index", 0)),
                    "width": item.get("width", 1),
                    "height": item.get("height", 1),
                    "is_visible": item.get("is_visible", True),
                    "settings": item.get("settings", {}),
                }
            )
        elif hasattr(item, "model_dump"):
            w_data.append(item.model_dump())

    res = await DashboardService.save_user_layout(db, user_id=current_user.id, layout_data=w_data)
    await db.commit()
    return res
