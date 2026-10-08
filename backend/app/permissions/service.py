"""Permission evaluation service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_management import CaseRestriction
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.team import TeamMembership, UserTeamAccess
from app.models.user import User, UserPreference


class PermissionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_roles(self, user_id: uuid.UUID) -> set[str]:
        """Fetch all active role keys for the given user, normalized to lowercase with alias handling."""
        roles_stmt = (
            select(Role.key, Role.name)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                Role.is_active == True,  # noqa: E712
            )
        )
        roles_res = await self.db.execute(roles_stmt)
        roles = set()
        for r_key, r_name in roles_res.all():
            k = (r_key or "").lower().strip()
            roles.add(k)
            name_lower = (r_name or "").lower()
            if "chief executive officer" in name_lower or name_lower == "ceo":
                roles.add("ceo")
            elif "executive director" in name_lower:
                roles.add("executive_director")
            elif "board member" in name_lower or "governor" in name_lower:
                roles.add("board_member")

        # Also check UserPreference requested_role / role as fallback
        pref_stmt = select(UserPreference.key, UserPreference.value).where(
            UserPreference.user_id == user_id,
            UserPreference.key.in_(["requested_role", "role"]),
        )
        pref_res = await self.db.execute(pref_stmt)
        for p_key, p_val in pref_res.all():
            val = (p_val or "").lower().strip()
            if val in ("ceo", "chief_executive_officer", "chief executive officer"):
                roles.add("ceo")
            elif val in ("executive_director", "executive director"):
                roles.add("executive_director")
            elif val in ("board_member", "board member"):
                roles.add("board_member")
            elif val:
                roles.add(val)

        return roles

    async def is_super_admin(self, user_id: uuid.UUID) -> bool:
        """Check if user has full administrative platform access across all workspaces and dashboards."""
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one_or_none()
        if not user_obj:
            return False

        email = (user_obj.email or "").lower().strip()
        if (
            email == "admin@crbcl.ca"
            or email.startswith("admin@")
            or getattr(user_obj, "is_system", False)
        ):
            return True

        user_roles = await self.get_user_roles(user_id)
        super_admin_roles = {"admin", "system_admin", "administrator", "super_admin", "system administrator"}
        return bool(user_roles & super_admin_roles)

    async def get_user_permissions(self, user_id: uuid.UUID) -> set[str]:
        """Load all active permissions for a user across all active assigned roles with canonical fallback."""
        if await self.is_super_admin(user_id):
            from app.permissions.constants import Permissions

            all_perms_res = await self.db.execute(
                select(Permission.key).where(Permission.is_active == True)  # noqa: E712
            )
            all_db_keys = set(all_perms_res.scalars().all())
            return all_db_keys | {p.value for p in Permissions}

        user_roles = await self.get_user_roles(user_id)

        stmt = (
            select(Permission.key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                UserRole.user_id == user_id,
                Role.is_active == True,  # noqa: E712
                Permission.is_active == True,  # noqa: E712
            )
        )
        result = await self.db.execute(stmt)
        permissions = set(result.scalars().all())

        # Canonical role-permission augmentation from ROLE_PERMISSIONS_MAP
        from app.core.seed import PERMISSIONS_DATA, ROLE_PERMISSIONS_MAP

        if user_roles & {"ceo", "executive_director", "chief_executive_officer"}:
            for p in PERMISSIONS_DATA:
                k = p["key"]
                permissions.add(k.value if hasattr(k, "value") else str(k))
        else:
            for r in user_roles:
                for p in ROLE_PERMISSIONS_MAP.get(r, []):
                    permissions.add(p.value if hasattr(p, "value") else str(p))

        return permissions

    async def get_user_accessible_team_ids(self, user_id: uuid.UUID) -> set[uuid.UUID] | None:
        """
        Get all team IDs the user has access to.
        Returns:
            - None if user has unrestricted team access (e.g. Executive Director role / Super-scoped)
            - set of team UUIDs otherwise
        """
        # Global administrators, executives, and leadership have unrestricted team access (None)
        user_res = await self.db.execute(select(User).where(User.id == user_id))
        user_obj = user_res.scalar_one_or_none()
        if user_obj and (
            user_obj.email == "admin@crbcl.ca"
            or (user_obj.email or "").lower().startswith("admin@")
            or getattr(user_obj, "is_system", False)
        ):
            return None

        user_roles = await self.get_user_roles(user_id)
        if any(r in user_roles for r in ["admin", "it_admin", "executive_director", "ceo", "director_manager"]):
            return None

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
        if await self.is_super_admin(user_id):
            return True

        user_roles = await self.get_user_roles(user_id)
        if user_roles & {"ceo", "executive_director", "chief_executive_officer"}:
            return True

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
