"""Add Client approval workflow, approval history, and duplicate client protection.

Revision ID: 028_client_approval_workflow
Revises: 027_person_numeric_id
Create Date: 2026-09-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "028_client_approval_workflow"
down_revision: str | None = "027_person_numeric_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Add approval lifecycle columns to clients ──────────────
    op.add_column(
        "clients",
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="APPROVED"),
    )
    op.add_column(
        "clients",
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("submission_notes", sa.Text(), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "clients",
        sa.Column("decision_reason", sa.Text(), nullable=True),
    )

    op.create_index("ix_clients_approval_status", "clients", ["approval_status"])
    op.create_foreign_key(
        "fk_clients_submitted_by",
        "clients",
        "users",
        ["submitted_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_clients_decided_by",
        "clients",
        "users",
        ["decided_by"],
        ["id"],
        ondelete="SET NULL",
    )

    # Partial unique index to protect against duplicate active/pending client contexts per person
    op.create_index(
        "uq_clients_person_active_pending",
        "clients",
        ["person_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL AND approval_status IN ('PENDING_APPROVAL', 'APPROVED')"),
        sqlite_where=sa.text("deleted_at IS NULL AND approval_status IN ('PENDING_APPROVAL', 'APPROVED')"),
    )

    # ── 2. Create client_approvals history table ──────────────────
    op.create_table(
        "client_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("from_status", sa.String(50), nullable=True),
        sa.Column("to_status", sa.String(50), nullable=False),
        sa.Column(
            "actor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("client_approvals")
    op.drop_index("uq_clients_person_active_pending", table_name="clients")
    op.drop_constraint("fk_clients_decided_by", "clients", type_="foreignkey")
    op.drop_constraint("fk_clients_submitted_by", "clients", type_="foreignkey")
    op.drop_index("ix_clients_approval_status", table_name="clients")
    op.drop_column("clients", "decision_reason")
    op.drop_column("clients", "decided_at")
    op.drop_column("clients", "decided_by")
    op.drop_column("clients", "submission_notes")
    op.drop_column("clients", "submitted_at")
    op.drop_column("clients", "submitted_by")
    op.drop_column("clients", "approval_status")
