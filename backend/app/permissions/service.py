"""Permission evaluation service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case_management import CaseRestriction
from app.models.role import UserRole
from app.models.team import TeamMembership, UserTeamAccess
from app.models.user import User


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_permissions(self, user_id: uuid.UUID) -> set[str]:
        """Load all active permissions for a user across all active assigned roles."""
        result = await self.db.execute(
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .options(selectinload(UserRole.role).selectinload(UserRole.role.property.mapper.class_.permissions))
        )
        user_roles = result.scalars().all()

        perms = set()
        for ur in user_roles:
            if ur.role and ur.role.is_active:
                for rp in ur.role.permissions:
                    if rp.permission and rp.permission.is_active:
                        perms.add(rp.permission.key)
        return perms

    async def get_user_accessible_team_ids(self, user_id: uuid.UUID) -> set[uuid.UUID] | None:
        """
        Get all team IDs the user has access to.
        Returns:
            - None if user has unrestricted team access (e.g. Executive Director role / Super-scoped)
            - set of team UUIDs otherwise
        """
        # Fetch active team memberships
        memberships_res = await self.db.execute(
            select(TeamMembership.team_id).where(
                TeamMembership.user_id == user_id,
                TeamMembership.is_active == True,  # noqa: E712
            )
        )
        team_ids = set(memberships_res.scalars().all())

        # Fetch additional team data access grants
        access_res = await self.db.execute(
            select(UserTeamAccess.team_id).where(
                UserTeamAccess.user_id == user_id,
                UserTeamAccess.is_active == True,  # noqa: E712
            )
        )
        team_ids.update(access_res.scalars().all())

        return team_ids

    async def user_has_permission(self, user_id: uuid.UUID, permission_key: str) -> bool:
        """Check if user has a specific permission key."""
        perms = await self.get_user_permissions(user_id)
        return permission_key in perms

    async def user_can_access_team(self, user_id: uuid.UUID, team_id: uuid.UUID | None) -> bool:
        """Check if user is authorized to access records scoped to a team."""
        if team_id is None:
            return True

        accessible_teams = await self.get_user_accessible_team_ids(user_id)
        if accessible_teams is None:
            return True
        return team_id in accessible_teams

    async def is_user_restricted_from_case(self, user_id: uuid.UUID, case_id: uuid.UUID) -> bool:
        """Check if user has an active conflict-of-interest / administrative case restriction."""
        stmt = select(CaseRestriction).where(
            CaseRestriction.case_id == case_id,
            CaseRestriction.user_id == user_id,
            CaseRestriction.is_active == True,  # noqa: E712
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none() is not None

    async def check_access(
        self,
        user: User,
        permission_key: str,
        resource_team_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
    ) -> bool:
        """Full 5-stage authorization evaluation foundation."""
        # 1. Authentication check
        if not user or not user.is_active or user.is_deleted:
            return False

        # 2. Role Permission check
        if not await self.user_has_permission(user.id, permission_key):
            return False

        # 3. Team Scope check
        if resource_team_id is not None and not await self.user_can_access_team(user.id, resource_team_id):
            return False

        # 4. Case Restriction Check (ADR-010)
        return not (case_id is not None and await self.is_user_restricted_from_case(user.id, case_id))
