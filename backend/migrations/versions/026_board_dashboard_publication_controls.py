"""Board Dashboard publication and governance approval controls.

Revision ID: 026_board_dashboard_publication_controls
Revises: 025_dept_exec_update_history
Create Date: 2026-09-11 08:30:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "026_board_dashboard_publication_controls"
down_revision = "025_dept_exec_update_history"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Extend executive_initiatives with publication controls ─────
    op.add_column(
        "executive_initiatives",
        sa.Column("is_board_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "ix_executive_initiatives_is_board_visible",
        "executive_initiatives",
        ["is_board_visible"],
    )
    op.add_column(
        "executive_initiatives",
        sa.Column("board_summary", sa.Text(), nullable=True),
    )
    op.add_column(
        "executive_initiatives",
        sa.Column("approved_for_board_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "executive_initiatives",
        sa.Column("approved_for_board_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_exec_init_approved_for_board_by",
        "executive_initiatives",
        "users",
        ["approved_for_board_by_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── 2. Extend department_executive_updates with publication controls ─
    op.add_column(
        "department_executive_updates",
        sa.Column("is_board_visible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index(
        "ix_dept_exec_updates_is_board_visible",
        "department_executive_updates",
        ["is_board_visible"],
    )
    op.add_column(
        "department_executive_updates",
        sa.Column("approved_for_board_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "department_executive_updates",
        sa.Column("approved_for_board_by_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_dept_update_approved_for_board_by",
        "department_executive_updates",
        "users",
        ["approved_for_board_by_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # ── 1. Revert department_executive_updates ────────────────────────
    op.drop_constraint("fk_dept_update_approved_for_board_by", "department_executive_updates", type_="foreignkey")
    op.drop_column("department_executive_updates", "approved_for_board_by_id")
    op.drop_column("department_executive_updates", "approved_for_board_at")
    op.drop_index("ix_dept_exec_updates_is_board_visible", table_name="department_executive_updates")
    op.drop_column("department_executive_updates", "is_board_visible")

    # ── 2. Revert executive_initiatives ───────────────────────────────
    op.drop_constraint("fk_exec_init_approved_for_board_by", "executive_initiatives", type_="foreignkey")
    op.drop_column("executive_initiatives", "approved_for_board_by_id")
    op.drop_column("executive_initiatives", "approved_for_board_at")
    op.drop_column("executive_initiatives", "board_summary")
    op.drop_index("ix_executive_initiatives_is_board_visible", table_name="executive_initiatives")
    op.drop_column("executive_initiatives", "is_board_visible")
