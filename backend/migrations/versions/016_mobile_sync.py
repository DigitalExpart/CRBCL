"""016 — Mobile Device Registration, Sync Status & Revocation.

Revision ID: 016_mobile_sync
Revises: 015_phase14_hardening
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import alembic.op as op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "016_mobile_sync"
down_revision: str | None = "015_phase14_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "mobile_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.String(100), nullable=False, unique=True),
        sa.Column("device_name", sa.String(100), nullable=False, server_default="Caseworker Handheld"),
        sa.Column("os_type", sa.String(20), nullable=False, server_default="Android"),
        sa.Column("app_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("device_status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_mobile_devices_device_id", "mobile_devices", ["device_id"])
    op.create_index("ix_mobile_devices_user_id", "mobile_devices", ["user_id"])
    op.create_index("ix_mobile_devices_device_status", "mobile_devices", ["device_status"])
    op.create_index("ix_mobile_devices_user_status", "mobile_devices", ["user_id", "device_status"])


def downgrade() -> None:
    op.drop_index("ix_mobile_devices_user_status", table_name="mobile_devices")
    op.drop_index("ix_mobile_devices_device_status", table_name="mobile_devices")
    op.drop_index("ix_mobile_devices_user_id", table_name="mobile_devices")
    op.drop_index("ix_mobile_devices_device_id", table_name="mobile_devices")
    op.drop_table("mobile_devices")
