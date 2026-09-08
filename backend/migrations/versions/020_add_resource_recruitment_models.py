"""Add resource recruitment tables.

Revision ID: 020_add_resource_recruitment_models
Revises: 019_resource_team_department
Create Date: 2026-09-08 11:55:00.000000
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "020_add_resource_recruitment_models"
down_revision = "019_resource_team_department"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resource_recruitments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column(
            "resource_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "current_state",
            sa.Enum(
                "INQUIRY",
                "ORIENTATION",
                "APPLICATION",
                "ASSESSMENT",
                "APPROVAL_REVIEW",
                "APPROVED",
                "DECLINED",
                "WITHDRAWN",
                "ON_HOLD",
                name="recruitmentstate",
            ),
            nullable=False,
            server_default="INQUIRY",
        ),
        sa.Column(
            "previous_state",
            sa.Enum(
                "INQUIRY",
                "ORIENTATION",
                "APPLICATION",
                "ASSESSMENT",
                "APPROVAL_REVIEW",
                "APPROVED",
                "DECLINED",
                "WITHDRAWN",
                "ON_HOLD",
                name="recruitmentstate",
            ),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_resource_recruitments_current_state", "resource_recruitments", ["current_state"]
    )
    op.create_index(
        "ix_resource_recruitments_resource_home_id", "resource_recruitments", ["resource_home_id"]
    )

    op.create_table(
        "resource_recruitment_applicants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column(
            "recruitment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resource_recruitments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("PRIMARY_APPLICANT", "SECONDARY_APPLICANT", name="applicantrole"),
            nullable=False,
            server_default="PRIMARY_APPLICANT",
        ),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_resource_recruitment_applicants_recruitment_id",
        "resource_recruitment_applicants",
        ["recruitment_id"],
    )
    op.create_index(
        "ix_resource_recruitment_applicants_person_id",
        "resource_recruitment_applicants",
        ["person_id"],
    )

    op.create_table(
        "resource_recruitment_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False, primary_key=True, default=uuid.uuid4),
        sa.Column(
            "recruitment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resource_recruitments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_state",
            sa.Enum(
                "INQUIRY",
                "ORIENTATION",
                "APPLICATION",
                "ASSESSMENT",
                "APPROVAL_REVIEW",
                "APPROVED",
                "DECLINED",
                "WITHDRAWN",
                "ON_HOLD",
                name="recruitmentstate",
            ),
            nullable=False,
        ),
        sa.Column(
            "to_state",
            sa.Enum(
                "INQUIRY",
                "ORIENTATION",
                "APPLICATION",
                "ASSESSMENT",
                "APPROVAL_REVIEW",
                "APPROVED",
                "DECLINED",
                "WITHDRAWN",
                "ON_HOLD",
                name="recruitmentstate",
            ),
            nullable=False,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            onupdate=sa.text("now()"),
        ),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_resource_recruitment_history_recruitment_id",
        "resource_recruitment_history",
        ["recruitment_id"],
    )
    op.create_index(
        "ix_resource_recruitment_history_changed_at",
        "resource_recruitment_history",
        ["changed_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_resource_recruitment_history_changed_at", table_name="resource_recruitment_history"
    )
    op.drop_index(
        "ix_resource_recruitment_history_recruitment_id", table_name="resource_recruitment_history"
    )
    op.drop_table("resource_recruitment_history")

    op.drop_index(
        "ix_resource_recruitment_applicants_person_id", table_name="resource_recruitment_applicants"
    )
    op.drop_index(
        "ix_resource_recruitment_applicants_recruitment_id",
        table_name="resource_recruitment_applicants",
    )
    op.drop_table("resource_recruitment_applicants")

    op.drop_index(
        "ix_resource_recruitments_resource_home_id", table_name="resource_recruitments"
    )
    op.drop_index(
        "ix_resource_recruitments_current_state", table_name="resource_recruitments"
    )
    op.drop_table("resource_recruitments")

    op.execute("DROP TYPE IF EXISTS applicantrole")
    op.execute("DROP TYPE IF EXISTS recruitmentstate")
