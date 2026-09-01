"""009 — Placement Homes, Facilities, Members, Licensing, Inspections, and Contact Logs.

Revision ID: 009_placement_homes
Revises: 008_placement_episodes
Create Date: 2026-08-31
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_placement_homes"
down_revision: str | None = "008_placement_episodes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create placement_homes table ─────────────────────────
    op.create_table(
        "placement_homes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("home_code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id", ondelete="SET NULL"), nullable=True),
        sa.Column("home_type", sa.String(length=50), nullable=False, server_default="LICENSED_FOSTER"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("licensing_status", sa.String(length=50), nullable=False, server_default="UNLICENSED"),
        sa.Column("total_capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("address_line_1", sa.String(length=255), nullable=True),
        sa.Column("address_line_2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False, server_default="Regina"),
        sa.Column("province", sa.String(length=100), nullable=False, server_default="Saskatchewan"),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("community", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("primary_caregiver_name", sa.String(length=255), nullable=True),
        sa.Column("intake_criteria_notes", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("metadata_", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("total_capacity >= 0", name="ck_placement_homes_capacity_positive"),
    )
    op.create_index("ix_placement_homes_home_code", "placement_homes", ["home_code"])
    op.create_index("ix_placement_homes_name", "placement_homes", ["name"])
    op.create_index("ix_placement_homes_home_type", "placement_homes", ["home_type"])
    op.create_index("ix_placement_homes_status", "placement_homes", ["status"])
    op.create_index("ix_placement_homes_licensing_status", "placement_homes", ["licensing_status"])
    op.create_index("ix_placement_homes_community", "placement_homes", ["community"])
    op.create_index("ix_placement_homes_provider_id", "placement_homes", ["provider_id"])

    # ── 2. Create placement_home_members table ──────────────────
    op.create_table(
        "placement_home_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="PRIMARY_CAREGIVER"),
        sa.Column("start_date", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_placement_home_members_home_id", "placement_home_members", ["placement_home_id"])
    op.create_index("ix_placement_home_members_person_id", "placement_home_members", ["person_id"])
    op.create_index("ix_placement_home_members_is_active", "placement_home_members", ["is_active"])

    # ── 3. Create placement_home_licenses table ──────────────────
    op.create_table(
        "placement_home_licenses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("license_number", sa.String(length=100), nullable=False),
        sa.Column("license_type", sa.String(length=100), nullable=False, server_default="STANDARD_FOSTER"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("application_date", sa.Date(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=False),
        sa.Column("renewal_date", sa.Date(), nullable=True),
        sa.Column("issuing_authority", sa.String(length=255), nullable=False, server_default="Ministry of Social Services / First Nation Authority"),
        sa.Column("max_capacity", sa.Integer(), nullable=True),
        sa.Column("conditions", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.CheckConstraint("expiry_date >= effective_date", name="ck_placement_home_licenses_dates_valid"),
    )
    op.create_index("ix_placement_home_licenses_home_id", "placement_home_licenses", ["placement_home_id"])
    op.create_index("ix_placement_home_licenses_license_number", "placement_home_licenses", ["license_number"])
    op.create_index("ix_placement_home_licenses_status", "placement_home_licenses", ["status"])
    op.create_index("ix_placement_home_licenses_expiry_date", "placement_home_licenses", ["expiry_date"])

    # ── 4. Create placement_home_visits table ────────────────────
    op.create_table(
        "placement_home_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("visit_type", sa.String(length=50), nullable=False, server_default="ROUTINE_INSPECTION"),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("follow_up_due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_placement_home_visits_home_id", "placement_home_visits", ["placement_home_id"])
    op.create_index("ix_placement_home_visits_worker_id", "placement_home_visits", ["worker_id"])
    op.create_index("ix_placement_home_visits_visit_date", "placement_home_visits", ["visit_date"])
    op.create_index("ix_placement_home_visits_follow_up", "placement_home_visits", ["follow_up_due_date"])

    # ── 5. Create placement_home_contact_logs table ─────────────
    op.create_table(
        "placement_home_contact_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contact_type", sa.String(length=50), nullable=False, server_default="PHONE"),
        sa.Column("contact_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("follow_up_action", sa.Text(), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_placement_home_contacts_home_id", "placement_home_contact_logs", ["placement_home_id"])
    op.create_index("ix_placement_home_contacts_worker_id", "placement_home_contact_logs", ["worker_id"])
    op.create_index("ix_placement_home_contacts_date", "placement_home_contact_logs", ["contact_date"])

    # ── 6. Alter placement_episodes (add placement_home_id) ──────
    op.add_column(
        "placement_episodes",
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_placement_episodes_placement_home_id", "placement_episodes", ["placement_home_id"])

    # ── 7. Alter assessments (add placement_home_id) ────────────
    op.add_column(
        "assessments",
        sa.Column("placement_home_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("placement_homes.id", ondelete="CASCADE"), nullable=True),
    )
    op.create_index("ix_assessments_placement_home_id", "assessments", ["placement_home_id"])


def downgrade() -> None:
    op.drop_index("ix_assessments_placement_home_id", table_name="assessments")
    op.drop_column("assessments", "placement_home_id")

    op.drop_index("ix_placement_episodes_placement_home_id", table_name="placement_episodes")
    op.drop_column("placement_episodes", "placement_home_id")

    op.drop_table("placement_home_contact_logs")
    op.drop_table("placement_home_visits")
    op.drop_table("placement_home_licenses")
    op.drop_table("placement_home_members")
    op.drop_table("placement_homes")
