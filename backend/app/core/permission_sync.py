"""System-wide idempotent permission and role synchronization."""

from __future__ import annotations

import logging

from sqlalchemy import select

from app.auth.security import hash_password
from app.core.database import async_session_factory as AsyncSessionLocal
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.user import User, UserPreference

logger = logging.getLogger("crbcl.permissions.sync")

BASELINE_STAFF_DATA = [
    {
        "email": "admin@crbcl.ca",
        "full_name": "System Administrator",
        "display_name": "System Administrator",
        "department": "Information Technology",
        "roles": ["it_admin", "executive_director", "ceo"],
        "default_pin": "123456",
        "password": "admin123456",
    },
    {
        "email": "s.standingready@crbcl.org",
        "full_name": "Sarah Standingready",
        "display_name": "Sarah Standingready",
        "department": "Direct Client Care",
        "roles": ["caseworker"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "m.osoup@crbcl.org",
        "full_name": "Michael O’Soup",
        "display_name": "Michael O’Soup",
        "department": "Child Welfare Intake",
        "roles": ["caseworker"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "j.severight@crbcl.org",
        "full_name": "Jessica Severight",
        "display_name": "Jessica Severight",
        "department": "Operations & Facilities",
        "roles": ["office_coordinator"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "d.brass@crbcl.org",
        "full_name": "David Brass",
        "display_name": "David Brass",
        "department": "Elders & Ceremonies",
        "roles": ["cultural_worker"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "a.whitehawk@crbcl.org",
        "full_name": "Amanda Whitehawk",
        "display_name": "Amanda Whitehawk",
        "department": "Intake & Reception",
        "roles": ["front_desk"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "d.keshane@crbcl.org",
        "full_name": "Darren Keshane",
        "display_name": "Darren Keshane",
        "department": "Finance & Administration",
        "roles": ["finance_staff"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "k.strongquill@crbcl.org",
        "full_name": "Kendra Strongquill",
        "display_name": "Kendra Strongquill",
        "department": "Direct Client Care",
        "roles": ["caseworker"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
    {
        "email": "r.musqua@crbcl.org",
        "full_name": "Robert Musqua",
        "display_name": "Robert Musqua",
        "department": "Community Housing",
        "roles": ["caseworker"],
        "default_pin": "123456",
        "password": "CRBCLStaff2025!",
    },
]


async def sync_system_permissions() -> None:
    """Ensure that all critical roles, permissions, role mappings, and baseline staff exist in the database."""
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

            # 5. Synchronize baseline staff roster and 6-digit PINs
            for staff in BASELINE_STAFF_DATA:
                norm_email = staff["email"].strip().lower()
                user_res = await db.execute(select(User).where(User.email_normalized == norm_email))
                user_obj = user_res.scalar_one_or_none()

                if not user_obj:
                    user_obj = User(
                        email=staff["email"].strip(),
                        email_normalized=norm_email,
                        full_name=staff["full_name"],
                        display_name=staff["display_name"],
                        department=staff["department"],
                        password_hash=hash_password(staff["password"]),
                        is_active=staff.get("is_active", True),
                        is_verified=staff.get("is_verified", True),
                    )
                    db.add(user_obj)
                    await db.flush()
                    logger.info("Seeded baseline staff: %s (%s)", staff["full_name"], staff["email"])

                # Ensure roles
                for rkey in staff.get("roles", []):
                    role_obj = role_models.get(rkey)
                    if role_obj:
                        ur_res = await db.execute(
                            select(UserRole).where(UserRole.user_id == user_obj.id, UserRole.role_id == role_obj.id)
                        )
                        if not ur_res.scalar_one_or_none():
                            db.add(UserRole(user_id=user_obj.id, role_id=role_obj.id))

                # Ensure 6-digit PIN hash exists and admin PIN is synchronized
                pin_pref_res = await db.execute(
                    select(UserPreference).where(
                        UserPreference.user_id == user_obj.id,
                        UserPreference.key == "quick_pin_hash",
                    )
                )
                pref_obj = pin_pref_res.scalars().first()
                if not pref_obj:
                    db.add(
                        UserPreference(
                            user_id=user_obj.id,
                            key="quick_pin_hash",
                            value=hash_password(staff.get("default_pin", "123456")),
                        )
                    )
                elif staff.get("email") == "admin@crbcl.ca":
                    pref_obj.value = hash_password(staff.get("default_pin", "123456"))

                # Ensure active and clear lockout / failed attempts
                user_obj.is_active = True
                user_obj.locked_until = None
                user_obj.failed_login_count = 0

                # Ensure team access preference exists
                team_pref_res = await db.execute(
                    select(UserPreference).where(
                        UserPreference.user_id == user_obj.id,
                        UserPreference.key == "team_access",
                    )
                )
                if not team_pref_res.scalars().first():
                    db.add(
                        UserPreference(
                            user_id=user_obj.id,
                            key="team_access",
                            value='["all"]',
                        )
                    )

            await db.commit()
            if new_rp_count > 0:
                logger.info("Synchronized %d role permission grants into database.", new_rp_count)

    except Exception as exc:
        logger.warning("Permission sync encountered non-fatal error during startup: %s", exc)
