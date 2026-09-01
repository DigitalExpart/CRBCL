"""Child & Parent Passports API Router (Phase 11)."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import get_current_user_permissions, require_permission
from app.services.passport_service import PassportService

router = APIRouter(prefix="/passports", tags=["Child & Parent Passports"])


@router.get(
    "/child/{child_id}",
    dependencies=[Depends(require_permission(Permissions.REPORT_CHILD_PASSPORT))],
)
async def get_child_passport(
    child_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_CHILD_PASSPORT)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    """Generate permission-aware Child Passport document payload."""
    return await PassportService.generate_child_passport(
        db, child_id=child_id, user_id=current_user.id, user_permissions=user_perms
    )


@router.get(
    "/parent/{parent_id}",
    dependencies=[Depends(require_permission(Permissions.REPORT_PARENT_PASSPORT))],
)
async def get_parent_passport(
    parent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.REPORT_PARENT_PASSPORT)),
    user_perms: set[str] = Depends(get_current_user_permissions),
):
    """Generate Parent Passport summary payload."""
    return await PassportService.generate_parent_passport(
        db, parent_id=parent_id, user_id=current_user.id, user_permissions=user_perms
    )
