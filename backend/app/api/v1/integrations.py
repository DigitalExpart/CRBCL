"""API Router for Admin Integration Registry & Health Inspection."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.integrations.registry import (
    get_all_integrations_health,
    update_integration_status,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


class ToggleIntegrationRequest(BaseModel):
    is_enabled: bool
    is_approved: bool
    status: str  # NOT_CONFIGURED, CONFIGURED, DISABLED, PILOT, APPROVED, ERROR


@router.get("/health", response_model=list[dict[str, Any]])
def get_integrations_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve health and configuration status matrix for all integrated external providers.

    Excludes secret values and connection keys.
    """
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.INTEGRATION_READ not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to view administrative integrations health.",
        )
    return get_all_integrations_health(db)


@router.post("/{provider_key}/toggle", response_model=dict[str, Any])
def toggle_integration(
    provider_key: str,
    payload: ToggleIntegrationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Toggle integration approval status or enablement state."""
    user_perms = {p.permission for r in current_user.roles for p in r.permissions}
    if Permissions.INTEGRATION_MANAGE not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks required permissions to manage enterprise integrations.",
        )
    try:
        updated = update_integration_status(
            db=db,
            provider_key=provider_key,
            is_enabled=payload.is_enabled,
            is_approved=payload.is_approved,
            status=payload.status,
        )
        return {
            "status": "SUCCESS",
            "provider_key": updated.provider_key,
            "is_enabled": updated.is_enabled,
            "is_approved": updated.is_approved,
            "current_status": updated.status,
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
