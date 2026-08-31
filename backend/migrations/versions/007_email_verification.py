"""007 — Email Verification Codes and OTP Authentication.

Revision ID: 007_email_verification
Revises: 006_case_safety_plans
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_email_verification"
down_revision: str | None = "006_case_safety_plans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "email_verification_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_email_verification_lookup", "email_verification_codes", ["email", "is_used", "expires_at"])
    op.create_index("ix_email_verification_email", "email_verification_codes", ["email"])


def downgrade() -> None:
    op.drop_index("ix_email_verification_email", table_name="email_verification_codes")
    op.drop_index("ix_email_verification_lookup", table_name="email_verification_codes")
    op.drop_table("email_verification_codes")
