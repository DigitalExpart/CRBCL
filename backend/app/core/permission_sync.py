"""System-wide idempotent permission and role synchronization."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.database import async_session_factory as AsyncSessionLocal
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User

logger = logging.getLogger("crbcl.permissions.sync")


async def sync_system_permissions() -> None:
    """Ensure that all critical roles, permissions, and role mappings exist in the database."""
    try:
        from app.core.seed import PERMISSIONS_DATA, ROLE_PERMISSIONS_MAP, ROLES_DATA

        async with AsyncSessionLocal() as db:
            # 1. Sync permissions
            existing_perms_res = await db.execute(select(Permission))
            existing_perms = {p.key: p for p in existing_perms_res.scalars().all()}

            new_perms_count = 0
            for p_data in PERMISSIONS_DATA:
                key_val = p_data["key"].value if hasattr(p_data["key"], "value") else str(p_data["key"])
                if key_val not in existing_perms:
                    new_perm = Permission(
                        key=key_val,
                        name=p_data["name"],
                        category=p_data.get("category", "general"),
                        is_active=True,
                    )
                    db.add(new_perm)
                    existing_perms[key_val] = new_perm
                    new_perms_count += 1

            if new_perms_count > 0:
                await db.flush()
                logger.info("Synchronized %d new permissions into database.", new_perms_count)

            # 2. Sync roles
            existing_roles_res = await db.execute(select(Role))
            existing_roles = {r.key.lower(): r for r in existing_roles_res.scalars().all()}

            new_roles_count = 0
            for r_data in ROLES_DATA:
                k = r_data["key"].lower()
                if k not in existing_roles:
                    new_role = Role(
                        key=r_data["key"],
                        name=r_data["name"],
                        description=r_data.get("description", ""),
                        is_system=r_data.get("is_system", True),
                        is_active=True,
                    )
                    db.add(new_role)
                    existing_roles[k] = new_role
                    new_roles_count += 1

            if new_roles_count > 0:
                await db.flush()
                logger.info("Synchronized %d new roles into database.", new_roles_count)

            # 3. Sync critical role permissions (especially ceo, executive_director, board_member)
            role_models = {r.key: r for r in existing_roles.values()}
            new_rp_count = 0

            for role_key, perm_keys in ROLE_PERMISSIONS_MAP.items():
                if role_key not in role_models:
                    continue
                role_obj = role_models[role_key]

                # Fetch existing role permissions for this role
                current_rps_res = await db.execute(
                    select(RolePermission.permission_id).where(RolePermission.role_id == role_obj.id)
                )
                current_perm_ids = set(current_rps_res.scalars().all())

                for pk in perm_keys:
                    val = pk.value if hasattr(pk, "value") else str(pk)
                    if val in existing_perms:
                        perm_obj = existing_perms[val]
                        if perm_obj.id not in current_perm_ids:
                            db.add(RolePermission(role_id=role_obj.id, permission_id=perm_obj.id))
                            current_perm_ids.add(perm_obj.id)
                            new_rp_count += 1

            # 4. Ensure any user identified as CEO (e.g. username/display 'geek') has ceo role assigned
            ceo_role = role_models.get("ceo")
            if ceo_role:
                users_res = await db.execute(
                    select(User).where(
                        (User.email.ilike("%geek%"))
                        | (User.display_name.ilike("%geek%"))
                        | (User.full_name.ilike("%Chief Executive%"))
                    )
                )
                matching_users = users_res.scalars().all()
                for u in matching_users:
                    ur_check = await db.execute(
                        select(UserRole).where(UserRole.user_id == u.id, UserRole.role_id == ceo_role.id)
                    )
                    if not ur_check.scalar_one_or_none():
                        db.add(UserRole(user_id=u.id, role_id=ceo_role.id))
                        logger.info("Assigned CEO role to user %s (%s).", u.email, u.full_name)

            await db.commit()
            if new_rp_count > 0:
                logger.info("Synchronized %d role permission grants into database.", new_rp_count)

    except Exception as exc:
        logger.warning("Permission sync encountered non-fatal error during startup: %s", exc)
