"""FastAPI router for Notification Templates administration."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.notification import (
    NotificationTemplateCreate,
    NotificationTemplateResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notification-templates", tags=["Notification Templates"])


@router.get("", response_model=list[NotificationTemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List configured notification templates (Technical Admin)."""
    perm_service = PermissionService(db)
    has_perm = await perm_service.user_has_permission(current_user.id, Permissions.NOTIFICATION_TEMPLATE_READ)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks notification.template.read permission."
        )

    service = NotificationService(db)
    templates = await service.repo.list_templates()
    return [NotificationTemplateResponse.model_validate(t) for t in templates]


@router.post("", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def upsert_template(
    payload: NotificationTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update a notification template copy definition."""
    perm_service = PermissionService(db)
    has_perm = await perm_service.user_has_permission(current_user.id, Permissions.NOTIFICATION_TEMPLATE_MANAGE)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Lacks notification.template.manage permission.",
        )

    service = NotificationService(db)
    template = await service.repo.upsert_template(
        event_type=payload.event_type,
        channel=payload.channel,
        title_template=payload.title_template,
        body_template=payload.body_template,
        is_active=payload.is_active,
    )
    await db.commit()
    return NotificationTemplateResponse.model_validate(template)
