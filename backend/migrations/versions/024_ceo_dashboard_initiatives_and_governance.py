"""CEO Dashboard: Executive Initiatives, Board Actions, and Department Executive Updates.

Revision ID: 024_ceo_dashboard_initiatives_and_governance
Revises: 023_front_desk_foundation
Create Date: 2026-09-10 12:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "024_ceo_dashboard_initiatives_and_governance"
down_revision = "023_front_desk_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create executive_initiatives table ─────────────────────────
    op.create_table(
        "executive_initiatives",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("department", sa.String(100), nullable=True),
        sa.Column(
            "responsible_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="ON_TRACK"),
        sa.Column("priority", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("progress_percentage", sa.Integer(), nullable=True),
        sa.Column("latest_update", sa.Text(), nullable=True),
        sa.Column("reporting_notes", sa.Text(), nullable=True),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # SoftDeleteMixin
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_executive_initiatives_title", "executive_initiatives", ["title"])
    op.create_index("ix_executive_initiatives_department", "executive_initiatives", ["department"])
    op.create_index("ix_executive_initiatives_status", "executive_initiatives", ["status"])
    op.create_index("ix_executive_initiatives_priority", "executive_initiatives", ["priority"])
    op.create_index("ix_executive_initiatives_target_date", "executive_initiatives", ["target_date"])
    op.create_index("ix_executive_initiatives_responsible_owner_id", "executive_initiatives", ["responsible_owner_id"])

    # ── 2. Create executive_initiative_history table ──────────────────
    op.create_table(
        "executive_initiative_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "initiative_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("executive_initiatives.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_status", sa.String(50), nullable=False),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("progress_percentage", sa.Integer(), nullable=True),
        sa.Column("update_note", sa.Text(), nullable=True),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_exec_init_hist_initiative_id", "executive_initiative_history", ["initiative_id"])
    op.create_index("ix_exec_init_hist_changed_at", "executive_initiative_history", ["changed_at"])

    # ── 3. Create board_actions table ─────────────────────────────────
    op.create_table(
        "board_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_number", sa.String(50), nullable=False, unique=True),
        sa.Column("originating_department", sa.String(100), nullable=False),
        sa.Column(
            "linked_initiative_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("executive_initiatives.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("background_summary", sa.Text(), nullable=False),
        sa.Column("requested_action", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column("required_by_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="SUBMITTED"),
        sa.Column(
            "submitted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision", sa.Text(), nullable=True),
        sa.Column("decision_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "decided_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("is_governance_ready", sa.Boolean(), nullable=False, server_default=sa.true()),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # SoftDeleteMixin
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_board_actions_ref_num", "board_actions", ["reference_number"])
    op.create_index("ix_board_actions_originating_dept", "board_actions", ["originating_department"])
    op.create_index("ix_board_actions_linked_initiative", "board_actions", ["linked_initiative_id"])
    op.create_index("ix_board_actions_title", "board_actions", ["title"])
    op.create_index("ix_board_actions_priority", "board_actions", ["priority"])
    op.create_index("ix_board_actions_required_by", "board_actions", ["required_by_date"])
    op.create_index("ix_board_actions_status", "board_actions", ["status"])
    op.create_index("ix_board_actions_submitted_by", "board_actions", ["submitted_by_id"])

    # ── 4. Create board_action_history table ──────────────────────────
    op.create_table(
        "board_action_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "board_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_actions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_status", sa.String(50), nullable=False),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("decision_notes", sa.Text(), nullable=True),
        sa.Column("action_notes", sa.Text(), nullable=True),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_board_action_hist_action_id", "board_action_history", ["board_action_id"])
    op.create_index("ix_board_action_hist_changed_at", "board_action_history", ["changed_at"])

    # ── 5. Create department_executive_updates table ──────────────────
    op.create_table(
        "department_executive_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reporting_period", sa.String(50), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column(
            "submitted_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitted_date", sa.DateTime(timezone=True), nullable=True, server_default=sa.func.now()),
        sa.Column("headline_summary", sa.String(500), nullable=False),
        sa.Column("accomplishments_narrative", sa.Text(), nullable=False, server_default=""),
        sa.Column("risks_issues", sa.Text(), nullable=True),
        sa.Column("support_decision_requested", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="SUBMITTED"),
        sa.Column(
            "linked_initiative_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("executive_initiatives.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "linked_board_action_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("board_actions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # AuditMixin
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        # SoftDeleteMixin
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("reporting_period", "department", "deleted_at", name="uq_dept_exec_update_period_department"),
    )
    op.create_index("ix_dept_exec_updates_period", "department_executive_updates", ["reporting_period"])
    op.create_index("ix_dept_exec_updates_dept", "department_executive_updates", ["department"])
    op.create_index("ix_dept_exec_updates_status", "department_executive_updates", ["status"])
    op.create_index("ix_dept_exec_updates_submitted_by", "department_executive_updates", ["submitted_by_id"])


def downgrade() -> None:
    op.drop_table("department_executive_updates")
    op.drop_table("board_action_history")
    op.drop_table("board_actions")
    op.drop_table("executive_initiative_history")
    op.drop_table("executive_initiatives")
