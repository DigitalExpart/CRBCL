"""FastAPI router for Notification Preferences."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.notification import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notification-preferences", tags=["Notification Preferences"])


@router.get("", response_model=list[NotificationPreferenceResponse])
async def get_my_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve current user's multi-channel notification preferences."""
    service = NotificationService(db)
    prefs = await service.get_user_preferences(current_user.id)
    return [NotificationPreferenceResponse.model_validate(p) for p in prefs]


@router.patch("", response_model=NotificationPreferenceResponse)
async def update_my_preference(
    payload: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update channel subscription setting for a specific notification category."""
    service = NotificationService(db)
    pref = await service.update_user_preference(
        user_id=current_user.id,
        event_type=payload.event_type,
        in_app_enabled=payload.in_app_enabled,
        email_enabled=payload.email_enabled,
        sms_enabled=payload.sms_enabled,
    )
    await db.commit()
    return NotificationPreferenceResponse.model_validate(pref)
