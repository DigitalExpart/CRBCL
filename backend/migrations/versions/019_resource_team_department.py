"""019_resource_team_department

Revision ID: 019_resource_team_department
Revises: 018_native_feature_completion
Create Date: 2026-09-08 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019_resource_team_department"
down_revision: str | None = "018_native_feature_completion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add department column to users table
    op.add_column(
        "users",
        sa.Column("department", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_users_department", "users", ["department"])


def downgrade() -> None:
    op.drop_index("ix_users_department", table_name="users")
    op.drop_column("users", "department")
