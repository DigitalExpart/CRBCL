"""FastAPI router for In-App Notifications and Delivery tracking."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.notification import (
    NotificationDeliveryResponse,
    NotificationResponse,
    UnreadCountResponse,
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=dict)
async def list_notifications(
    is_read: bool | None = Query(None),
    type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List current user's notifications."""
    service = NotificationService(db)
    items, total = await service.get_user_notifications(
        user_id=current_user.id,
        is_read=is_read,
        notification_type=type,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [NotificationResponse.model_validate(n) for n in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get active unread count for header notification badge."""
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.post("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark single notification as read."""
    service = NotificationService(db)
    n = await service.mark_as_read(notification_id, current_user.id)
    if not n:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    await db.commit()
    return NotificationResponse.model_validate(n)


@router.post("/read-all", response_model=dict)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark all active notifications for current user as read."""
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.id)
    await db.commit()
    return {"marked_read_count": count}


@router.get("/deliveries", response_model=dict)
async def list_deliveries(
    status: str | None = Query(None),
    channel: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Technical Admin delivery logs."""
    perm_service = PermissionService(db)
    has_perm = await perm_service.user_has_permission(current_user.id, Permissions.NOTIFICATION_DELIVERY_READ)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks notification.delivery.read permission."
        )

    service = NotificationService(db)
    items, total = await service.repo.list_deliveries(status=status, channel=channel, page=page, page_size=page_size)
    return {
        "items": [NotificationDeliveryResponse.model_validate(d) for d in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/deliveries/{delivery_id}/retry", response_model=NotificationDeliveryResponse)
async def retry_delivery(
    delivery_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicit command to retry failed delivery."""
    perm_service = PermissionService(db)
    has_perm = await perm_service.user_has_permission(current_user.id, Permissions.NOTIFICATION_DELIVERY_RETRY)
    if not has_perm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Lacks notification.delivery.retry permission."
        )

    service = NotificationService(db)
    delivery = await service.retry_delivery(delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery record not found.")
    await db.commit()
    return NotificationDeliveryResponse.model_validate(delivery)
