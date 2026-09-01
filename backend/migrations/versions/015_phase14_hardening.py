"""015 — Phase 14 Production Hardening, Legal Hold, Migration Ledger & MFA.

Revision ID: 015_phase14_hardening
Revises: 014_integrations_ai
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import alembic.op as op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "015_phase14_hardening"
down_revision: str | None = "014_integrations_ai"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Legal Hold columns on cases
    op.add_column("cases", sa.Column("is_legal_hold", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("cases", sa.Column("legal_hold_reason", sa.Text(), nullable=True))
    op.add_column(
        "cases",
        sa.Column("legal_hold_by_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("cases", sa.Column("legal_hold_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_cases_is_legal_hold", "cases", ["is_legal_hold"])

    # 2. MFA columns on users
    op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("users", sa.Column("mfa_secret", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("mfa_backup_codes", sa.Text(), nullable=True))

    # 3. Migration Ledger Table
    op.create_table(
        "migration_ledger",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("target_entity_type", sa.String(50), nullable=False),
        sa.Column("target_entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="COMPLETED"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("reconciled_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("source_system", "target_entity_type", "source_id", name="uq_migration_ledger_source"),
    )
    op.create_index("ix_migration_ledger_source", "migration_ledger", ["source_system", "source_id"])


def downgrade() -> None:
    op.drop_index("ix_migration_ledger_source", table_name="migration_ledger")
    op.drop_table("migration_ledger")

    op.drop_column("users", "mfa_backup_codes")
    op.drop_column("users", "mfa_secret")
    op.drop_column("users", "mfa_enabled")

    op.drop_index("ix_cases_is_legal_hold", table_name="cases")
    op.drop_column("cases", "legal_hold_at")
    op.drop_column("cases", "legal_hold_by_id")
    op.drop_column("cases", "legal_hold_reason")
    op.drop_column("cases", "is_legal_hold")
