"""008 — Active Efforts, Background Checks, In-Home Placements, Removals, Placements, Respite, Discharge, Permanency, Visitation & Court Events.

Revision ID: 008_placement_episodes
Revises: 007_email_verification
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_placement_episodes"
down_revision: str | None = "007_email_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. active_efforts
    op.create_table(
        "active_efforts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("effort_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("service_category", sa.String(length=100), nullable=True),
        sa.Column("provider_name", sa.String(length=255), nullable=True),
        sa.Column("service_date", sa.Date(), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False, server_default="ONGOING"),
        sa.Column("barriers_encountered", sa.Text(), nullable=True),
        sa.Column("remedial_action", sa.Text(), nullable=True),
        sa.Column(
            "worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_active_efforts_case_id", "active_efforts", ["case_id"])
    op.create_index("ix_active_efforts_service_date", "active_efforts", ["service_date"])
    op.create_index("ix_active_efforts_deleted_at", "active_efforts", ["deleted_at"])

    # 2. background_checks
    op.create_table(
        "background_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("subject_type", sa.String(length=50), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_name", sa.String(length=255), nullable=False),
        sa.Column("check_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("completion_date", sa.Date(), nullable=True),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("conducted_by_agency", sa.String(length=255), nullable=True),
        sa.Column("clearance_reference_number", sa.String(length=100), nullable=True),
        sa.Column("risk_assessment_notes", sa.Text(), nullable=True),
        sa.Column("is_eligible_for_placement", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "adjudicated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("adjudicated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_background_checks_subject", "background_checks", ["subject_type", "subject_id"])
    op.create_index("ix_background_checks_status", "background_checks", ["status"])
    op.create_index("ix_background_checks_expiry_date", "background_checks", ["expiry_date"])
    op.create_index("ix_background_checks_deleted_at", "background_checks", ["deleted_at"])

    # 3. in_home_placements
    op.create_table(
        "in_home_placements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "primary_caregiver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("caregiver_relationship", sa.String(length=100), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("supervision_level", sa.String(length=50), nullable=False, server_default="STANDARD"),
        sa.Column("safety_monitoring_frequency", sa.String(length=50), nullable=False, server_default="WEEKLY"),
        sa.Column("support_services_provided", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("closure_reason", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_in_home_placements_case_id", "in_home_placements", ["case_id"])
    op.create_index("ix_in_home_placements_child_id", "in_home_placements", ["child_id"])
    op.create_index("ix_in_home_placements_status", "in_home_placements", ["status"])
    op.create_index("ix_in_home_placements_deleted_at", "in_home_placements", ["deleted_at"])

    # 4. removal_episodes
    op.create_table(
        "removal_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("removal_date", sa.Date(), nullable=False),
        sa.Column("removal_time", sa.Time(), nullable=True),
        sa.Column("removal_type", sa.String(length=50), nullable=False),
        sa.Column("authority_type", sa.String(length=50), nullable=False),
        sa.Column("legal_authority_reference", sa.String(length=255), nullable=True),
        sa.Column("reason_for_removal", sa.Text(), nullable=False),
        sa.Column("immediate_safety_threat", sa.Text(), nullable=True),
        sa.Column("removal_location", sa.String(length=255), nullable=True),
        sa.Column("accompanying_officers", sa.String(length=255), nullable=True),
        sa.Column("child_condition_at_removal", sa.Text(), nullable=True),
        sa.Column("belongings_inventoried", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_removal_episodes_case_id", "removal_episodes", ["case_id"])
    op.create_index("ix_removal_episodes_child_id", "removal_episodes", ["child_id"])
    op.create_index("ix_removal_episodes_removal_date", "removal_episodes", ["removal_date"])
    op.create_index("ix_removal_episodes_deleted_at", "removal_episodes", ["deleted_at"])

    # 5. placement_episodes
    op.create_table(
        "placement_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "removal_episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("removal_episodes.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("placement_type", sa.String(length=50), nullable=False),
        sa.Column("provider_name", sa.String(length=255), nullable=False),
        sa.Column("provider_contact", sa.String(length=255), nullable=True),
        sa.Column("provider_address", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("primary_caregiver_name", sa.String(length=255), nullable=True),
        sa.Column("per_diem_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("cultural_plan_in_place", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("placement_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_placement_episodes_case_id", "placement_episodes", ["case_id"])
    op.create_index("ix_placement_episodes_child_id", "placement_episodes", ["child_id"])
    op.create_index("ix_placement_episodes_removal_id", "placement_episodes", ["removal_episode_id"])
    op.create_index("ix_placement_episodes_status", "placement_episodes", ["status"])
    op.create_index("ix_placement_episodes_deleted_at", "placement_episodes", ["deleted_at"])

    # 6. respite_episodes
    op.create_table(
        "respite_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "placement_episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_episodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("respite_provider_name", sa.String(length=255), nullable=False),
        sa.Column("respite_type", sa.String(length=50), nullable=False, server_default="PLANNED"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_respite_episodes_placement_id", "respite_episodes", ["placement_episode_id"])
    op.create_index("ix_respite_episodes_dates", "respite_episodes", ["start_date", "end_date"])
    op.create_index("ix_respite_episodes_deleted_at", "respite_episodes", ["deleted_at"])

    # 7. discharge_episodes
    op.create_table(
        "discharge_episodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "placement_episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_episodes.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("discharge_date", sa.Date(), nullable=False),
        sa.Column("discharge_type", sa.String(length=50), nullable=False),
        sa.Column("destination_name", sa.String(length=255), nullable=True),
        sa.Column("destination_relationship", sa.String(length=100), nullable=True),
        sa.Column("post_discharge_supervision_plan", sa.Text(), nullable=True),
        sa.Column("discharge_readiness_assessed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_discharge_episodes_placement_id", "discharge_episodes", ["placement_episode_id"])
    op.create_index("ix_discharge_episodes_discharge_date", "discharge_episodes", ["discharge_date"])
    op.create_index("ix_discharge_episodes_deleted_at", "discharge_episodes", ["deleted_at"])

    # 8. permanency_plans
    op.create_table(
        "permanency_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("primary_goal", sa.String(length=50), nullable=False),
        sa.Column("concurrent_goal", sa.String(length=50), nullable=True),
        sa.Column("target_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("cultural_heritage_strategy", sa.Text(), nullable=True),
        sa.Column("sibling_co_placement_strategy", sa.Text(), nullable=True),
        sa.Column("review_frequency_months", sa.Integer(), nullable=False, server_default="6"),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column(
            "established_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_permanency_plans_case_id", "permanency_plans", ["case_id"])
    op.create_index("ix_permanency_plans_child_id", "permanency_plans", ["child_id"])
    op.create_index("ix_permanency_plans_status", "permanency_plans", ["status"])
    op.create_index("ix_permanency_plans_deleted_at", "permanency_plans", ["deleted_at"])

    # 9. visitation_plans
    op.create_table(
        "visitation_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("participant_names", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("frequency", sa.String(length=50), nullable=False, server_default="WEEKLY"),
        sa.Column("duration_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("supervision_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("supervisor_type", sa.String(length=50), nullable=False, server_default="CASE_WORKER"),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_visitation_plans_case_id", "visitation_plans", ["case_id"])
    op.create_index("ix_visitation_plans_child_id", "visitation_plans", ["child_id"])
    op.create_index("ix_visitation_plans_status", "visitation_plans", ["status"])
    op.create_index("ix_visitation_plans_deleted_at", "visitation_plans", ["deleted_at"])

    # 10. court_events
    op.create_table(
        "court_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("hearing_type", sa.String(length=50), nullable=False),
        sa.Column("court_docket_number", sa.String(length=100), nullable=True),
        sa.Column("court_location", sa.String(length=255), nullable=True),
        sa.Column("judge_name", sa.String(length=255), nullable=True),
        sa.Column("hearing_date", sa.Date(), nullable=False),
        sa.Column("hearing_time", sa.Time(), nullable=True),
        sa.Column("outcome_summary", sa.Text(), nullable=True),
        sa.Column("orders_issued", sa.Text(), nullable=True),
        sa.Column("legal_counsel_info", sa.Text(), nullable=True),
        sa.Column("band_representative_present", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("next_court_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_court_events_case_id", "court_events", ["case_id"])
    op.create_index("ix_court_events_child_id", "court_events", ["child_id"])
    op.create_index("ix_court_events_hearing_date", "court_events", ["hearing_date"])
    op.create_index("ix_court_events_status", "court_events", ["status"])
    op.create_index("ix_court_events_deleted_at", "court_events", ["deleted_at"])


def downgrade() -> None:
    op.drop_table("court_events")
    op.drop_table("visitation_plans")
    op.drop_table("permanency_plans")
    op.drop_table("discharge_episodes")
    op.drop_table("respite_episodes")
    op.drop_table("placement_episodes")
    op.drop_table("removal_episodes")
    op.drop_table("in_home_placements")
    op.drop_table("background_checks")
    op.drop_table("active_efforts")
