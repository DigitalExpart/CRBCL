"""Resource Unit Sprint 2: Caregiver Assessments, Clearances, Training, Licensing & Inspections.

Revision ID: 021_resource_unit_sprint_2
Revises: 020_add_resource_recruitment_models
Create Date: 2026-09-08 21:05:00.000000
"""

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "021_resource_unit_sprint_2"
down_revision = "020_add_resource_recruitment_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Make case_id nullable on assessments for home/caregiver assessments ─
    op.alter_column("assessments", "case_id", nullable=True)

    # ── 2. Extend background_checks for Resource Home clearances ─────────────
    op.add_column(
        "background_checks",
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_background_checks_placement_home_id", "background_checks", ["placement_home_id"])

    op.add_column(
        "background_checks",
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "background_checks",
        sa.Column("renewal_status", sa.String(50), nullable=True),
    )

    # ── 3. Create caregiver_trainings table (caregivers are Persons, not Employees)
    op.create_table(
        "caregiver_trainings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("training_type", sa.String(100), nullable=False),
        sa.Column("course_name", sa.String(255), nullable=True),
        sa.Column("provider_name", sa.String(255), nullable=True),
        sa.Column("completion_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="COMPLETED"),
        sa.Column("renewal_due_date", sa.Date(), nullable=True),
        sa.Column(
            "verified_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_caregiver_trainings_person_id", "caregiver_trainings", ["person_id"])
    op.create_index("ix_caregiver_trainings_placement_home_id", "caregiver_trainings", ["placement_home_id"])
    op.create_index("ix_caregiver_trainings_training_type", "caregiver_trainings", ["training_type"])
    op.create_index("ix_caregiver_trainings_status", "caregiver_trainings", ["status"])
    op.create_index("ix_caregiver_trainings_expiry_date", "caregiver_trainings", ["expiry_date"])
    op.create_index("ix_caregiver_trainings_completion_date", "caregiver_trainings", ["completion_date"])

    # ── 4. Extend placement_home_licenses ───────────────────────────────────────
    op.add_column("placement_home_licenses", sa.Column("placement_restrictions", sa.Text(), nullable=True))
    op.add_column("placement_home_licenses", sa.Column("min_age", sa.Integer(), nullable=True))
    op.add_column("placement_home_licenses", sa.Column("max_age", sa.Integer(), nullable=True))
    op.add_column(
        "placement_home_licenses",
        sa.Column(
            "approved_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "placement_home_licenses",
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ── 5. Extend placement_home_visits for detailed inspections & corrective actions
    op.add_column("placement_home_visits", sa.Column("completed_date", sa.Date(), nullable=True))
    op.add_column("placement_home_visits", sa.Column("findings", sa.Text(), nullable=True))
    op.add_column("placement_home_visits", sa.Column("deficiencies", sa.Text(), nullable=True))
    op.add_column("placement_home_visits", sa.Column("corrective_actions", sa.Text(), nullable=True))
    op.add_column("placement_home_visits", sa.Column("corrective_action_due_date", sa.Date(), nullable=True))
    op.create_index(
        "ix_placement_home_visits_corrective_action_due_date",
        "placement_home_visits",
        ["corrective_action_due_date"],
    )
    op.add_column(
        "placement_home_visits",
        sa.Column("corrective_action_status", sa.String(50), nullable=False, server_default="NONE"),
    )
    op.add_column(
        "placement_home_visits",
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    # 5. Revert placement_home_visits extensions
    op.drop_column("placement_home_visits", "document_id")
    op.drop_column("placement_home_visits", "corrective_action_status")
    op.drop_index(
        "ix_placement_home_visits_corrective_action_due_date",
        table_name="placement_home_visits",
    )
    op.drop_column("placement_home_visits", "corrective_action_due_date")
    op.drop_column("placement_home_visits", "corrective_actions")
    op.drop_column("placement_home_visits", "deficiencies")
    op.drop_column("placement_home_visits", "findings")
    op.drop_column("placement_home_visits", "completed_date")

    # 4. Revert placement_home_licenses extensions
    op.drop_column("placement_home_licenses", "document_id")
    op.drop_column("placement_home_licenses", "approved_by")
    op.drop_column("placement_home_licenses", "max_age")
    op.drop_column("placement_home_licenses", "min_age")
    op.drop_column("placement_home_licenses", "placement_restrictions")

    # 3. Drop caregiver_trainings table
    op.drop_index("ix_caregiver_trainings_completion_date", table_name="caregiver_trainings")
    op.drop_index("ix_caregiver_trainings_expiry_date", table_name="caregiver_trainings")
    op.drop_index("ix_caregiver_trainings_status", table_name="caregiver_trainings")
    op.drop_index("ix_caregiver_trainings_training_type", table_name="caregiver_trainings")
    op.drop_index("ix_caregiver_trainings_placement_home_id", table_name="caregiver_trainings")
    op.drop_index("ix_caregiver_trainings_person_id", table_name="caregiver_trainings")
    op.drop_table("caregiver_trainings")

    # 2. Revert background_checks extensions
    op.drop_column("background_checks", "renewal_status")
    op.drop_column("background_checks", "document_id")
    op.drop_index("ix_background_checks_placement_home_id", table_name="background_checks")
    op.drop_column("background_checks", "placement_home_id")

    # 1. Revert case_id nullable on assessments
    op.alter_column("assessments", "case_id", nullable=False)
