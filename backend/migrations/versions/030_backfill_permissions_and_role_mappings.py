"""Backfill permissions and role mappings for CEO, Board, and staff roles.

Revision ID: 030_backfill_permissions_and_role_mappings
Revises: 029_office_coordinator_and_control_centre
Create Date: 2026-10-07 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "030_backfill_permissions_and_role_mappings"
down_revision: str | None = "029_office_coordinator_and_control_centre"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Backfill all permissions
    from app.core.seed import PERMISSIONS_DATA, ROLE_PERMISSIONS_MAP, ROLES_DATA

    for p in PERMISSIONS_DATA:
        key_val = p["key"].value if hasattr(p["key"], "value") else str(p["key"])
        name_val = p.get("name", key_val).replace("'", "''")
        cat_val = p.get("category", "general").replace("'", "''")

        conn.execute(
            sa.text(
                f"""
                INSERT INTO permissions (id, key, name, description, category, is_active, created_at, updated_at)
                VALUES (gen_random_uuid(), '{key_val}', '{name_val}', '', '{cat_val}', true, now(), now())
                ON CONFLICT (key) DO NOTHING
                """
            )
        )

    # 2. Backfill all roles
    for r in ROLES_DATA:
        key_val = r["key"].replace("'", "''")
        name_val = r["name"].replace("'", "''")
        desc_val = r.get("description", "").replace("'", "''")
        is_sys = "true" if r.get("is_system", True) else "false"

        conn.execute(
            sa.text(
                f"""
                INSERT INTO roles (id, key, name, description, is_active, is_system, created_at, updated_at)
                VALUES (gen_random_uuid(), '{key_val}', '{name_val}', '{desc_val}', true, {is_sys}, now(), now())
                ON CONFLICT (key) DO NOTHING
                """
            )
        )

    # 3. Backfill role-permission mappings
    for role_key, perm_keys in ROLE_PERMISSIONS_MAP.items():
        clean_role_key = role_key.replace("'", "''")
        for pk in perm_keys:
            val = pk.value if hasattr(pk, "value") else str(pk)
            clean_perm_key = val.replace("'", "''")

            conn.execute(
                sa.text(
                    f"""
                    INSERT INTO role_permissions (id, role_id, permission_id, created_at)
                    SELECT gen_random_uuid(), r.id, p.id, now()
                    FROM roles r, permissions p
                    WHERE r.key = '{clean_role_key}' AND p.key = '{clean_perm_key}'
                    AND NOT EXISTS (
                        SELECT 1 FROM role_permissions rp
                        WHERE rp.role_id = r.id AND rp.permission_id = p.id
                    )
                    """
                )
            )

    # 4. Ensure CEO user assignment (e.g. user 'geek')
    conn.execute(
        sa.text(
            """
            INSERT INTO user_roles (id, user_id, role_id, assigned_at)
            SELECT gen_random_uuid(), u.id, r.id, now()
            FROM users u, roles r
            WHERE r.key = 'ceo'
            AND (u.email ILIKE '%geek%' OR u.display_name ILIKE '%geek%' OR u.full_name ILIKE '%Chief Executive%')
            AND NOT EXISTS (
                SELECT 1 FROM user_roles ur
                WHERE ur.user_id = u.id AND ur.role_id = r.id
            )
            """
        )
    )


def downgrade() -> None:
    pass
