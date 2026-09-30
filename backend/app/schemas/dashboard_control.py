"""Pydantic schemas for the Master Admin Dashboard Control Centre."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DashboardRegistryItem(BaseModel):
    """Canonical registry entry for a controllable workspace/dashboard."""

    key: str = Field(..., description="Stable unique identifier for the workspace")
    name: str = Field(..., description="Human-readable display name")
    category: str = Field(..., description="Operational department or functional domain")
    route: str = Field(..., description="Primary web frontend route")
    workspace_type: str = Field(..., description="Workspace classification (dashboard, workspace, administrative, governance)")
    is_enabled: bool = Field(True, description="Organization-wide availability state")
    primary_permission_key: str | None = Field(None, description="Authoritative RBAC permission required for access")
    security_classification: str = Field(..., description="Confidentiality classification level")
    has_protected_data: bool = Field(False, description="Whether workspace contains protected case, client, health, HR or board data")
    status: str = Field("IMPLEMENTED", description="Implementation status in codebase")
    description: str = Field("", description="Operational purpose of the workspace")
    authorized_roles: list[str] = Field(default_factory=list, description="Roles currently possessing the required capability")
    authorized_users_count: int = Field(0, description="Count of active users with access")


class DashboardStatusUpdateRequest(BaseModel):
    """Request to toggle organization-wide workspace availability."""

    is_enabled: bool = Field(..., description="New enabled state")
    reason: str | None = Field(None, description="Optional administrative rationale for the change")


class DashboardRolesUpdateRequest(BaseModel):
    """Request to update role assignments for a workspace capability."""

    role_keys: list[str] = Field(..., description="List of role keys granted access")


class DashboardAvailabilityResponse(BaseModel):
    """Safe availability status returned to client applications."""

    workspace_key: str
    is_enabled: bool
    name: str
    message: str | None = None
