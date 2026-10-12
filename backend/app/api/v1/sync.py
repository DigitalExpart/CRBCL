"""Mobile Sync API Router for Device Management, Delta Synchronization & Outbox Push."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.services.sync_service import (
    get_sync_pull_delta,
    process_sync_push,
    register_mobile_device,
    revoke_mobile_device,
    validate_device_status,
)

router = APIRouter()


class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str = "Caseworker Handheld"
    os_type: str = "Android"
    app_version: str = "1.0.0"


class SyncPullRequest(BaseModel):
    last_synced_at: datetime | None = None
    previously_cached_case_ids: list[str] | None = None


class PushItem(BaseModel):
    client_mutation_id: str
    entity_type: str  # CASE_NOTE, SAFETY_PLAN_UPDATE
    payload: dict[str, Any]
    expected_version: int | None = None


class SyncPushRequest(BaseModel):
    items: list[PushItem]


def _extract_user_roles_and_perms(user: User) -> tuple[set[str], set[str]]:
    roles: set[str] = set()
    perms: set[str] = set()
    for ur in getattr(user, "roles", []):
        r = getattr(ur, "role", ur)
        if hasattr(r, "key") and r.key:
            roles.add(str(r.key).lower())
        if hasattr(r, "name") and r.name:
            roles.add(str(r.name).lower())
        if hasattr(r, "permissions"):
            for rp in r.permissions:
                p = getattr(rp, "permission", rp)
                if hasattr(p, "key") and p.key:
                    perms.add(str(p.key))
                elif hasattr(rp, "permission") and isinstance(rp.permission, str):
                    perms.add(rp.permission)
                elif isinstance(p, str):
                    perms.add(p)
    return roles, perms


@router.post("/devices/register", response_model=dict[str, Any])
async def register_device(
    req: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register or update a mobile device for a caseworker."""
    device = await register_mobile_device(
        db=db,
        user_id=current_user.id,
        device_id=req.device_id,
        device_name=req.device_name,
        os_type=req.os_type,
        app_version=req.app_version,
    )
    return {"status": "REGISTERED", "device_id": device.device_id, "device_status": device.device_status}


@router.post("/devices/{device_id}/revoke", response_model=dict[str, Any])
async def revoke_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Administrative revocation of a mobile device."""
    _, user_perms = _extract_user_roles_and_perms(current_user)
    if Permissions.ADMIN_USERS_MANAGE not in user_perms and Permissions.ADMIN_CONFIGURATION_MANAGE not in user_perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User lacks administrative permissions to revoke mobile devices.",
        )
    try:
        device = await revoke_mobile_device(db=db, device_id=device_id)
        return {"status": "REVOKED", "device_id": device.device_id}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/config", response_model=dict[str, Any])
async def get_sync_config(
    current_user: User = Depends(get_current_user),
):
    """Retrieve synchronization configuration, feature flag status, and user eligibility."""
    from app.core import get_settings

    settings = get_settings()
    user_roles, _ = _extract_user_roles_and_perms(current_user)
    is_admin_or_supervisor = bool({"admin", "it_admin", "supervisor", "executive_director", "ceo"} & user_roles)
    is_eligible = settings.crbcl_offline_web_enabled or is_admin_or_supervisor
    return {
        "offline_web_enabled": settings.crbcl_offline_web_enabled,
        "user_eligible": is_eligible,
        "server_time": datetime.utcnow().isoformat(),
    }


@router.post("/pull", response_model=dict[str, Any])
async def sync_pull(
    req: SyncPullRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
    x_client_type: str | None = Header(None, alias="X-Client-Type"),
):
    """Pull updated delta for assigned cases, clients, and notes since last_synced_at."""
    user_roles, user_perms = _extract_user_roles_and_perms(current_user)
    if x_client_type == "web" or (x_device_id and x_device_id.startswith("WEB-")):
        from app.core import get_settings

        settings = get_settings()
        is_admin_or_supervisor = bool({"admin", "it_admin", "supervisor", "executive_director", "ceo"} & user_roles)
        if not (settings.crbcl_offline_web_enabled or is_admin_or_supervisor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OFFLINE_WEB_DISABLED: Web offline workspace synchronization is currently disabled by administrator policy.",
            )

    await validate_device_status(db, current_user.id, x_device_id)
    return await get_sync_pull_delta(
        db=db,
        user_id=current_user.id,
        user_permissions=user_perms,
        last_synced_at=req.last_synced_at,
        previously_cached_case_ids=req.previously_cached_case_ids,
    )


@router.post("/push", response_model=dict[str, Any])
async def sync_push(
    req: SyncPushRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_device_id: str | None = Header(None, alias="X-Device-ID"),
    x_client_type: str | None = Header(None, alias="X-Client-Type"),
):
    """Process offline outbox queue items pushed from mobile field device or web offline workspace."""
    user_roles, user_perms = _extract_user_roles_and_perms(current_user)
    if x_client_type == "web" or (x_device_id and x_device_id.startswith("WEB-")):
        from app.core import get_settings

        settings = get_settings()
        is_admin_or_supervisor = bool({"admin", "it_admin", "supervisor", "executive_director", "ceo"} & user_roles)
        if not (settings.crbcl_offline_web_enabled or is_admin_or_supervisor):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="OFFLINE_WEB_DISABLED: Web offline workspace synchronization is currently disabled by administrator policy.",
            )

    await validate_device_status(db, current_user.id, x_device_id)
    items_dicts = [item.model_dump() for item in req.items]
    return await process_sync_push(
        db=db,
        user_id=current_user.id,
        user_permissions=user_perms,
        push_items=items_dicts,
    )
