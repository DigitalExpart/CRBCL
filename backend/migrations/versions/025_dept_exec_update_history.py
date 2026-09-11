"""Department Executive Update History table for narrative audit trail.

Revision ID: 025_dept_exec_update_history
Revises: 024_ceo_dashboard_initiatives_and_governance
Create Date: 2026-09-11 04:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "025_dept_exec_update_history"
down_revision = "024_ceo_dashboard_initiatives_and_governance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "department_executive_update_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "update_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("department_executive_updates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("reporting_period", sa.String(50), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("previous_headline_summary", sa.String(500), nullable=True),
        sa.Column("previous_accomplishments_narrative", sa.Text(), nullable=True),
        sa.Column("previous_risks_issues", sa.Text(), nullable=True),
        sa.Column("previous_status", sa.String(50), nullable=False),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_dept_exec_update_hist_update_id",
        "department_executive_update_history",
        ["update_id"],
    )
    op.create_index(
        "ix_dept_exec_update_hist_changed_at",
        "department_executive_update_history",
        ["changed_at"],
    )


def downgrade() -> None:
    op.drop_table("department_executive_update_history")
