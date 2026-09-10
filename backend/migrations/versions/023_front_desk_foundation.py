"""Front Desk Foundation: Public Google Form Ingestion Queue, Routing History, and Downstream Conversion Linkages.

Revision ID: 023_front_desk_foundation
Revises: 022_resource_unit_sprint_3
Create Date: 2026-09-10 04:00:00.000000
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "023_front_desk_foundation"
down_revision = "022_resource_unit_sprint_3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Create front_desk_sequences table ───────────────────────
    op.create_table(
        "front_desk_sequences",
        sa.Column("year", sa.Integer(), primary_key=True),
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── 2. Create front_desk_submissions table ─────────────────────
    op.create_table(
        "front_desk_submissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_number", sa.String(50), nullable=False, unique=True),
        sa.Column("external_response_id", sa.String(255), nullable=True, unique=True),
        sa.Column("source", sa.String(50), nullable=False, server_default="google_form"),
        sa.Column("status", sa.String(50), nullable=False, server_default="RECEIVED"),
        sa.Column("urgency", sa.String(50), nullable=False, server_default="Medium"),
        sa.Column("destination_department", sa.String(100), nullable=True),
        sa.Column(
            "destination_team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("submitter_name", sa.String(200), nullable=True),
        sa.Column("submitter_email", sa.String(200), nullable=True),
        sa.Column("submitter_phone", sa.String(50), nullable=True),
        sa.Column("submitter_relationship", sa.String(100), nullable=True),
        sa.Column("inquiry_type", sa.String(100), nullable=False, server_default="general_inquiry"),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("payload_raw", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "front_desk_worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("front_desk_notes", sa.Text(), nullable=True),
        sa.Column(
            "department_worker_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("department_notes", sa.Text(), nullable=True),
        sa.Column(
            "resulting_referral_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("referrals.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_front_desk_submissions_status", "front_desk_submissions", ["status"])
    op.create_index("ix_front_desk_submissions_external_response_id", "front_desk_submissions", ["external_response_id"])
    op.create_index("ix_front_desk_submissions_destination_department", "front_desk_submissions", ["destination_department"])
    op.create_index("ix_front_desk_submissions_destination_team_id", "front_desk_submissions", ["destination_team_id"])
    op.create_index("ix_front_desk_submissions_received_at", "front_desk_submissions", ["received_at"])
    op.create_index("ix_front_desk_submissions_front_desk_worker_id", "front_desk_submissions", ["front_desk_worker_id"])
    op.create_index("ix_front_desk_submissions_department_worker_id", "front_desk_submissions", ["department_worker_id"])
    op.create_index("ix_front_desk_submissions_resulting_referral_id", "front_desk_submissions", ["resulting_referral_id"])

    # ── 3. Create front_desk_routing_history table ─────────────────
    op.create_table(
        "front_desk_routing_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("front_desk_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("previous_status", sa.String(50), nullable=False),
        sa.Column("new_status", sa.String(50), nullable=False),
        sa.Column("previous_destination", sa.String(100), nullable=True),
        sa.Column("new_destination", sa.String(100), nullable=True),
        sa.Column(
            "changed_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reason_note", sa.Text(), nullable=True),
    )

    op.create_index("ix_front_desk_routing_history_submission_id", "front_desk_routing_history", ["submission_id"])
    op.create_index("ix_front_desk_routing_history_changed_at", "front_desk_routing_history", ["changed_at"])

    # ── 4. Create public_intake_conversion_links table ─────────────
    op.create_table(
        "public_intake_conversion_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("front_desk_submissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("downstream_entity_type", sa.String(100), nullable=False),
        sa.Column("downstream_entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("downstream_entity_reference", sa.String(100), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_index("ix_public_intake_conversion_links_submission_id", "public_intake_conversion_links", ["submission_id"])
    op.create_index("ix_public_intake_conversion_links_downstream_entity", "public_intake_conversion_links", ["downstream_entity_type", "downstream_entity_id"])


def downgrade() -> None:
    op.drop_index("ix_public_intake_conversion_links_downstream_entity", table_name="public_intake_conversion_links")
    op.drop_index("ix_public_intake_conversion_links_submission_id", table_name="public_intake_conversion_links")
    op.drop_table("public_intake_conversion_links")

    op.drop_index("ix_front_desk_routing_history_changed_at", table_name="front_desk_routing_history")
    op.drop_index("ix_front_desk_routing_history_submission_id", table_name="front_desk_routing_history")
    op.drop_table("front_desk_routing_history")

    op.drop_index("ix_front_desk_submissions_resulting_referral_id", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_department_worker_id", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_front_desk_worker_id", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_received_at", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_destination_team_id", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_destination_department", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_external_response_id", table_name="front_desk_submissions")
    op.drop_index("ix_front_desk_submissions_status", table_name="front_desk_submissions")
    op.drop_table("front_desk_submissions")

    op.drop_table("front_desk_sequences")
