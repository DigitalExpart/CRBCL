"""003 — Intake, Referrals, Screening, Child Dispositions, and Supervisor Decisions.

Revision ID: 003_intake_referrals
Revises: 002_people_families
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_intake_referrals"
down_revision: str | None = "002_people_families"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Referral Sequences Table ─────────────────────────────
    op.create_table(
        "referral_sequences",
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── 2. Referrals Table ──────────────────────────────────────
    op.create_table(
        "referrals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("referral_number", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("received_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("received_method", sa.String(50), nullable=False, server_default="phone"),
        sa.Column("community", sa.String(200), nullable=True),
        sa.Column("priority", sa.String(20), nullable=False, server_default="Medium"),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("immediate_safety_concerns", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("law_enforcement_involved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("law_enforcement_file_number", sa.String(100), nullable=True),
        sa.Column("law_enforcement_officer_info", sa.String(300), nullable=True),
        sa.Column(
            "assigned_worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("assigned_worker_name", sa.String(300), nullable=True),
        sa.Column(
            "assigned_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("origin_agency", sa.String(200), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_referrals_number", "referrals", ["referral_number"])
    op.create_index("ix_referrals_status", "referrals", ["status"])
    op.create_index("ix_referrals_received_date", "referrals", ["received_date"])
    op.create_index("ix_referrals_assigned_worker_id", "referrals", ["assigned_worker_id"])
    op.create_index("ix_referrals_assigned_team_id", "referrals", ["assigned_team_id"])

    # ── 3. Referral People Table ────────────────────────────────
    op.create_table(
        "referral_people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("relationship_to_child", sa.String(100), nullable=True),
        sa.Column("is_primary_caregiver", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_subject_of_concern", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referral_people_referral_person", "referral_people", ["referral_id", "person_id"])
    op.create_index("ix_referral_people_role", "referral_people", ["role"])

    # ── 4. Referral Reporters Table ─────────────────────────────
    op.create_table(
        "referral_reporters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_mandated_reporter", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("wants_notification", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("reporter_name", sa.String(255), nullable=True),
        sa.Column("organization", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("preferred_contact_method", sa.String(50), nullable=True),
        sa.Column("relationship_to_family", sa.String(100), nullable=True),
        sa.Column("reporter_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referral_reporters_referral_id", "referral_reporters", ["referral_id"])

    # ── 5. Referral Incidents Table ─────────────────────────────
    op.create_table(
        "referral_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("incident_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location_description", sa.Text(), nullable=True),
        sa.Column("community", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("law_enforcement_involved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("police_file_number", sa.String(100), nullable=True),
        sa.Column("officer_info", sa.String(300), nullable=True),
        sa.Column("immediate_danger", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referral_incidents_referral_id", "referral_incidents", ["referral_id"])

    # ── 6. Referral Concerns Table ──────────────────────────────
    op.create_table(
        "referral_concerns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("concern_type", sa.String(100), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="Moderate"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_referral_concerns_referral_id", "referral_concerns", ["referral_id"])
    op.create_index("ix_referral_concerns_type", "referral_concerns", ["concern_type"])

    # ── 7. Child Dispositions Table ─────────────────────────────
    op.create_table(
        "child_dispositions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "destination_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("destination_program", sa.String(200), nullable=True),
        sa.Column("external_agency_name", sa.String(255), nullable=True),
        sa.Column("external_referral_contact", sa.String(255), nullable=True),
        sa.Column(
            "resulting_case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "decided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approval_state", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_child_dispositions_referral_id", "child_dispositions", ["referral_id"])
    op.create_index("ix_child_dispositions_person_id", "child_dispositions", ["person_id"])
    op.create_index("ix_child_dispositions_resulting_case", "child_dispositions", ["resulting_case_id"])

    # ── 8. Intake Decisions Table ───────────────────────────────
    op.create_table(
        "intake_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("overall_recommendation", sa.Text(), nullable=False, server_default=""),
        sa.Column("rationale", sa.Text(), nullable=False, server_default=""),
        sa.Column("supervisor_notes", sa.Text(), nullable=True),
        sa.Column(
            "submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "returned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_intake_decisions_referral_id", "intake_decisions", ["referral_id"])

    # ── 9. Referral Links Table ─────────────────────────────────
    op.create_table(
        "referral_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column(
            "source_referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "target_referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("link_type", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "source_referral_id", "target_referral_id", "link_type", name="uq_referral_links_source_target_type"
        ),
    )
    op.create_index("ix_referral_links_source", "referral_links", ["source_referral_id"])
    op.create_index("ix_referral_links_target", "referral_links", ["target_referral_id"])

    # ── 10. Cases Table Intake Provenance Extension ─────────────
    op.add_column(
        "cases",
        sa.Column(
            "origin_referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "cases",
        sa.Column(
            "origin_disposition_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("child_dispositions.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_cases_origin_referral", "cases", ["origin_referral_id"])


def downgrade() -> None:
    op.drop_index("ix_cases_origin_referral", table_name="cases")
    op.drop_column("cases", "origin_disposition_id")
    op.drop_column("cases", "origin_referral_id")

    op.drop_table("referral_links")
    op.drop_table("intake_decisions")
    op.drop_table("child_dispositions")
    op.drop_table("referral_concerns")
    op.drop_table("referral_incidents")
    op.drop_table("referral_reporters")
    op.drop_table("referral_people")
    op.drop_table("referrals")
    op.drop_table("referral_sequences")
