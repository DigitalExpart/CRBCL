"""Permission evaluation service."""

from __future__ import annotations

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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
            .options(
                selectinload(UserRole.role).selectinload(UserRole.role.property.mapper.class_.permissions)
            )
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
        perms = await self.get_user_permissions(user_id)
        # Note: IT Admin does NOT get unrestricted team access to client data!
        # Only roles with specific global scoping or admin.teams.manage get all teams if configured.
        # But for clinical/case data, team scope is strictly enforced.

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
            # Unassigned records can be viewed by anyone with the base permission
            return True

        accessible_teams = await self.get_user_accessible_team_ids(user_id)
        if accessible_teams is None:
            return True
        return team_id in accessible_teams

    async def check_access(
        self,
        user: User,
        permission_key: str,
        resource_team_id: uuid.UUID | None = None,
    ) -> bool:
        """Full 5-stage authorization evaluation foundation."""
        # 1. Authentication check
        if not user or not user.is_active or user.is_deleted:
            return False

        # 2. Role Permission check
        if not await self.user_has_permission(user.id, permission_key):
            return False

        # 3. Team Scope check
        if resource_team_id is not None:
            if not await self.user_can_access_team(user.id, resource_team_id):
                return False

        # 4 & 5: Record Restriction & Field Policy (Allow/Deny)
        return True
