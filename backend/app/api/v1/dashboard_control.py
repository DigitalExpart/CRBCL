"""API Router for Master Admin Dashboard Control Centre."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.dashboard_control import (
    DashboardAvailabilityResponse,
    DashboardRegistryItem,
    DashboardRolesUpdateRequest,
    DashboardStatusUpdateRequest,
)
from app.services.dashboard_registry_service import DashboardRegistryService

router = APIRouter(tags=["Dashboard Control Centre"])


@router.get("/admin/dashboards", response_model=list[DashboardRegistryItem])
async def list_dashboard_registry(
    user: User = Depends(require_permission(Permissions.ADMIN_CONFIGURATION_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve full canonical staff dashboard/workspace registry with live enablement and role assignments."""
    service = DashboardRegistryService(db)
    return await service.get_all_workspaces()


@router.patch("/admin/dashboards/{workspace_key}/status", response_model=DashboardRegistryItem)
async def update_dashboard_status(
    workspace_key: str,
    payload: DashboardStatusUpdateRequest,
    request: Request,
    user: User = Depends(require_permission(Permissions.ADMIN_CONFIGURATION_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Enable or disable a dashboard/workspace across the agency."""
    service = DashboardRegistryService(db)
    try:
        updated = await service.update_workspace_status(
            workspace_key=workspace_key,
            is_enabled=payload.is_enabled,
            actor_user_id=user.id,
            reason=payload.reason,
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "WORKSPACE_NOT_FOUND", "message": str(e)}},
        ) from None


@router.patch("/admin/dashboards/{workspace_key}/roles", response_model=DashboardRegistryItem)
async def update_dashboard_roles(
    workspace_key: str,
    payload: DashboardRolesUpdateRequest,
    request: Request,
    user: User = Depends(require_permission(Permissions.ADMIN_ROLES_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Configure which staff roles have permission to access the workspace."""
    service = DashboardRegistryService(db)
    try:
        updated = await service.update_workspace_roles(
            workspace_key=workspace_key,
            role_keys=payload.role_keys,
            actor_user_id=user.id,
            ip_address=request.client.host if request.client else None,
        )
        await db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "INVALID_ROLE_UPDATE", "message": str(e)}},
        ) from None


@router.get("/dashboards/{workspace_key}/availability", response_model=DashboardAvailabilityResponse)
async def check_dashboard_availability(
    workspace_key: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Client check to determine whether a workspace is active or temporarily disabled."""
    service = DashboardRegistryService(db)
    is_enabled = await service.is_workspace_enabled(workspace_key)
    return DashboardAvailabilityResponse(
        workspace_key=workspace_key,
        is_enabled=is_enabled,
        name=workspace_key,
        message=None if is_enabled else "Workspace currently unavailable by administrative policy.",
    )
