"""Resource Unit Sprint 3: Home Monitoring, Complaints & Investigations, and Caregiver Supports.

Revision ID: 022_resource_unit_sprint_3
Revises: 021_resource_unit_sprint_2
Create Date: 2026-09-09 10:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "022_resource_unit_sprint_3"
down_revision = "021_resource_unit_sprint_2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create resource_home_monitorings table ───────────────────────
    op.create_table(
        "resource_home_monitorings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("contact_date", sa.Date(), nullable=False),
        sa.Column("contact_type", sa.String(50), nullable=False, server_default="IN_PERSON"),
        sa.Column("child_interview_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("caregiver_interview_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("safety_review_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("strengths", sa.Text(), nullable=True),
        sa.Column("concerns", sa.Text(), nullable=True),
        sa.Column("follow_up_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("follow_up_details", sa.Text(), nullable=True),
        sa.Column("next_review_date", sa.Date(), nullable=True),
        sa.Column("corrective_action_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("corrective_action_notes", sa.Text(), nullable=True),
        sa.Column(
            "visit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_home_visits.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="COMPLETED"),
        sa.Column("cadence_days", sa.Integer(), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_resource_home_monitorings_home_id", "resource_home_monitorings", ["placement_home_id"]
    )
    op.create_index(
        "ix_resource_home_monitorings_worker_id", "resource_home_monitorings", ["worker_id"]
    )
    op.create_index(
        "ix_resource_home_monitorings_contact_date", "resource_home_monitorings", ["contact_date"]
    )
    op.create_index(
        "ix_resource_home_monitorings_status", "resource_home_monitorings", ["status"]
    )
    op.create_index(
        "ix_resource_home_monitorings_next_review", "resource_home_monitorings", ["next_review_date"]
    )

    # ── 2. Create resource_complaints table ─────────────────────────────
    op.create_table(
        "resource_complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("complaint_number", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("complainant_category", sa.String(50), nullable=False, server_default="ANONYMOUS"),
        sa.Column("complainant_name", sa.String(255), nullable=True),
        sa.Column("complainant_contact", sa.String(255), nullable=True),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("complaint_type", sa.String(100), nullable=False, server_default="CARE_STANDARDS"),
        sa.Column("allegation_summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False, server_default="MEDIUM"),
        sa.Column(
            "assigned_investigator_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(50), nullable=False, server_default="RECEIVED"),
        sa.Column("investigation_activities", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("findings_finalized", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("findings_finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "findings_finalized_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recommendations", sa.Text(), nullable=True),
        sa.Column("corrective_actions", sa.Text(), nullable=True),
        sa.Column("disposition", sa.String(50), nullable=True),
        sa.Column("disposition_notes", sa.Text(), nullable=True),
        sa.Column(
            "disposition_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("disposition_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closure_date", sa.Date(), nullable=True),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_resource_complaints_number", "resource_complaints", ["complaint_number"]
    )
    op.create_index(
        "ix_resource_complaints_home_id", "resource_complaints", ["placement_home_id"]
    )
    op.create_index(
        "ix_resource_complaints_received_date", "resource_complaints", ["received_date"]
    )
    op.create_index(
        "ix_resource_complaints_status", "resource_complaints", ["status"]
    )
    op.create_index(
        "ix_resource_complaints_investigator_id", "resource_complaints", ["assigned_investigator_id"]
    )
    op.create_index(
        "ix_resource_complaints_incident_id", "resource_complaints", ["incident_id"]
    )

    # ── 3. Create caregiver_supports table ──────────────────────────────
    op.create_table(
        "caregiver_supports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("support_number", sa.String(50), nullable=False, unique=True),
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "caregiver_person_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("persons.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("support_type", sa.String(50), nullable=False, server_default="RESPITE"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("requested_date", sa.Date(), nullable=False),
        sa.Column("provided_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="REQUESTED"),
        sa.Column("provider_program_name", sa.String(255), nullable=True),
        sa.Column(
            "worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("frequency_duration", sa.String(100), nullable=True),
        sa.Column("outcome_notes", sa.Text(), nullable=True),
        sa.Column(
            "service_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_requests.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("amount", sa.Numeric(14, 2), nullable=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index(
        "ix_caregiver_supports_number", "caregiver_supports", ["support_number"]
    )
    op.create_index(
        "ix_caregiver_supports_home_id", "caregiver_supports", ["placement_home_id"]
    )
    op.create_index(
        "ix_caregiver_supports_person_id", "caregiver_supports", ["caregiver_person_id"]
    )
    op.create_index(
        "ix_caregiver_supports_status", "caregiver_supports", ["status"]
    )
    op.create_index(
        "ix_caregiver_supports_worker_id", "caregiver_supports", ["worker_id"]
    )
    op.create_index(
        "ix_caregiver_supports_service_req", "caregiver_supports", ["service_request_id"]
    )


def downgrade() -> None:
    op.drop_table("caregiver_supports")
    op.drop_table("resource_complaints")
    op.drop_table("resource_home_monitorings")
