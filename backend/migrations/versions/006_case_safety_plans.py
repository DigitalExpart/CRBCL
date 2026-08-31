"""006 — Safety Plans, Case Plans, Goals, Activities, Signatures, and Immutability.

Revision ID: 006_case_safety_plans
Revises: 005_assessment_engine
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_case_safety_plans"
down_revision: str | None = "005_assessment_engine"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Plan Sequences Table (Monthly Atomic Counter) ─────────────
    op.create_table(
        "plan_sequences",
        sa.Column("period", sa.String(length=6), primary_key=True),  # e.g., '202608'
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── 2. Plans (Master File) ───────────────────────────────────────
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "primary_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "family_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("families.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("plan_type", sa.String(length=50), nullable=False),  # SAFETY_PLAN, CASE_PLAN
        sa.Column("plan_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_plans_case_id", "plans", ["case_id"])
    op.create_index("ix_plans_primary_person_id", "plans", ["primary_person_id"])
    op.create_index("ix_plans_family_id", "plans", ["family_id"])
    op.create_index("ix_plans_plan_type", "plans", ["plan_type"])
    op.create_index("ix_plans_status", "plans", ["status"])
    op.create_index("ix_plans_number", "plans", ["plan_number"])
    op.create_index("ix_plans_case_type", "plans", ["case_id", "plan_type"])

    # ── 3. Plan Versions ─────────────────────────────────────────────
    op.create_table(
        "plan_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("meeting_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meeting_location", sa.String(length=255), nullable=True),
        sa.Column("narrative", sa.Text(), nullable=True),
        sa.Column(
            "source_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("document_hash", sa.String(length=64), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "finalized_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "locked_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
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
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("plan_id", "version_number", name="uq_plan_version_number"),
    )
    op.create_index("ix_plan_versions_plan_id", "plan_versions", ["plan_id"])
    op.create_index("ix_plan_versions_status", "plan_versions", ["status"])

    # ── 4. Plan Participants ─────────────────────────────────────────
    op.create_table(
        "plan_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("participant_type", sa.String(length=50), nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "provider_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("providers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relationship", sa.String(length=100), nullable=True),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("attendance_status", sa.String(length=50), nullable=False, server_default="ATTENDED"),
        sa.Column("signature_required", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_participants_version", "plan_participants", ["plan_version_id"])

    # ── 5. Plan Concerns / Harm Statements ───────────────────────────
    op.create_table(
        "plan_concerns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concern_type", sa.String(length=50), nullable=False, server_default="SAFETY_CONCERN"),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_concerns_version_sort", "plan_concerns", ["plan_version_id", "sort_order"])

    # ── 6. Plan Strengths / Protective Factors ───────────────────────
    op.create_table(
        "plan_strengths",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_strengths_version_sort", "plan_strengths", ["plan_version_id", "sort_order"])

    # ── 7. Plan Goals ────────────────────────────────────────────────
    op.create_table(
        "plan_goals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("goal_text", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NOT_STARTED"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "completed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_goals_version_sort", "plan_goals", ["plan_version_id", "sort_order"])
    op.create_index("ix_plan_goals_status", "plan_goals", ["status"])
    op.create_index("ix_plan_goals_target_date", "plan_goals", ["target_date"])

    # ── 8. Plan Activities ───────────────────────────────────────────
    op.create_table(
        "plan_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("activity_text", sa.Text(), nullable=False),
        sa.Column("responsible_type", sa.String(length=50), nullable=False, server_default="WORKER"),
        sa.Column(
            "responsible_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "responsible_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("responsible_name", sa.String(length=255), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="NOT_STARTED"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completion_notes", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_activities_goal_sort", "plan_activities", ["goal_id", "sort_order"])
    op.create_index("ix_plan_activities_status", "plan_activities", ["status"])
    op.create_index("ix_plan_activities_due_date", "plan_activities", ["due_date"])

    # ── 9. Goal Progress Updates ─────────────────────────────────────
    op.create_table(
        "goal_progress_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "goal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column(
            "updated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_goal_progress_goal_created", "goal_progress_updates", ["goal_id", "created_at"])

    # ── 10. Plan Assessments (Assessment Linkage) ────────────────────
    op.create_table(
        "plan_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assessments.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("relationship_type", sa.String(length=50), nullable=False, server_default="INFORMED_BY"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("plan_id", "assessment_id", name="uq_plan_assessment_link"),
    )

    # ── 11. Plan Signatures (Cryptographic Signature Records) ────────
    op.create_table(
        "plan_signatures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "plan_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("signer_type", sa.String(length=50), nullable=False),
        sa.Column(
            "signer_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "signer_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("signer_name", sa.String(length=255), nullable=False),
        sa.Column("signer_role", sa.String(length=100), nullable=False),
        sa.Column("signature_data", sa.Text(), nullable=True),
        sa.Column("signature_image_url", sa.String(length=500), nullable=True),
        sa.Column("signed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("method", sa.String(length=50), nullable=False, server_default="ELECTRONIC_DRAW"),
        sa.Column("document_hash", sa.String(length=64), nullable=False),
        sa.Column("attestation_text", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_plan_signatures_version", "plan_signatures", ["plan_version_id"])


def downgrade() -> None:
    op.drop_table("plan_signatures")
    op.drop_table("plan_assessments")
    op.drop_table("goal_progress_updates")
    op.drop_table("plan_activities")
    op.drop_table("plan_goals")
    op.drop_table("plan_strengths")
    op.drop_table("plan_concerns")
    op.drop_table("plan_participants")
    op.drop_table("plan_versions")
    op.drop_table("plans")
    op.drop_table("plan_sequences")
