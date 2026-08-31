"""004 — Core Case Management, Investigations, Case Notes, and Transfer Workflows.

Revision ID: 004_case_management
Revises: 003_intake_referrals
Create Date: 2026-08-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004_case_management"
down_revision: Union[str, None] = "003_intake_referrals"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Case Sequences Table (Atomic Period Concurrency) ─────
    op.create_table(
        "case_sequences",
        sa.Column("period", sa.String(length=6), primary_key=True),  # e.g., '202608'
        sa.Column("last_value", sa.Integer(), nullable=False, server_default="0"),
    )

    # ── 2. Extend Cases Table ───────────────────────────────────
    op.add_column(
        "cases",
        sa.Column("stage", sa.String(length=50), nullable=False, server_default="INVESTIGATION"),
    )
    op.add_column(
        "cases",
        sa.Column("closed_reason", sa.Text(), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("reopened_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("reopened_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "cases",
        sa.Column("reopened_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_cases_stage", "cases", ["stage"])
    op.create_index("ix_cases_case_type", "cases", ["case_type"])

    # ── 3. Case People Table ────────────────────────────────────
    op.create_table(
        "case_people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="other"),
        sa.Column("relationship_to_subject", sa.String(length=100), nullable=True),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_case_people_role", "case_people", ["role"])

    # ── 4. Case Assignments Table ───────────────────────────────
    op.create_table(
        "case_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="caseworker"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_case_assignments_active", "case_assignments", ["is_active"])
    op.create_index("ix_case_assignments_role", "case_assignments", ["role"])

    # ── 5. Case External Workers Table ──────────────────────────
    op.create_table(
        "case_external_workers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # ── 6. Case Sources Table (Other & Collateral Sources) ─────
    op.create_table(
        "case_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="OTHER_SOURCE"),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("providers.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relationship_or_role", sa.String(length=100), nullable=True),
        sa.Column("organization", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_case_sources_category", "case_sources", ["category"])

    # ── 7. Case Links Table ─────────────────────────────────────
    op.create_table(
        "case_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("link_type", sa.String(length=50), nullable=False, server_default="related_family"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("linked_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("source_case_id", "target_case_id", name="uq_case_links_pair"),
        sa.CheckConstraint("source_case_id != target_case_id", name="ck_case_links_no_self_link"),
    )

    # ── 8. Case Restrictions Table ──────────────────────────────
    op.create_table(
        "case_restrictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("restriction_type", sa.String(length=50), nullable=False, server_default="conflict_of_interest"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("removed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("removal_reason", sa.Text(), nullable=True),
    )
    op.create_index("ix_case_restrictions_active", "case_restrictions", ["is_active"])

    # ── 9. Case Transfers Table ─────────────────────────────────
    op.create_table(
        "case_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("source_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("destination_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_case_transfers_status", "case_transfers", ["status"])

    # ── 10. Case Status History Table ───────────────────────────
    op.create_table(
        "case_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("previous_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    # ── 11. Extend Case Notes Table ─────────────────────────────
    op.add_column(
        "case_notes",
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("contact_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("location", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("is_well_child_checkup", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "case_notes",
        sa.Column("appointment_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("next_appointment_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("goal_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "case_notes",
        sa.Column("notify_team", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "case_notes",
        sa.Column("status", sa.String(length=50), nullable=False, server_default="COMPLETED"),
    )
    op.add_column(
        "case_notes",
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_case_notes_status", "case_notes", ["status"])
    op.create_index("ix_case_notes_contact_type", "case_notes", ["contact_type"])

    # ── 12. Case Note People Table ──────────────────────────────
    op.create_table(
        "case_note_people",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── 13. Case Note Attachments Table ─────────────────────────
    op.create_table(
        "case_note_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=100), nullable=True),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── 14. Case Note Addenda Table (Audit Immutability) ────────
    op.create_table(
        "case_note_addenda",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_note_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("case_notes.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("case_note_addenda")
    op.drop_table("case_note_attachments")
    op.drop_table("case_note_people")

    op.drop_index("ix_case_notes_contact_type", table_name="case_notes")
    op.drop_index("ix_case_notes_status", table_name="case_notes")
    op.drop_column("case_notes", "locked_at")
    op.drop_column("case_notes", "status")
    op.drop_column("case_notes", "notify_team")
    op.drop_column("case_notes", "goal_id")
    op.drop_column("case_notes", "next_appointment_at")
    op.drop_column("case_notes", "appointment_status")
    op.drop_column("case_notes", "is_well_child_checkup")
    op.drop_column("case_notes", "location")
    op.drop_column("case_notes", "contact_type")
    op.drop_column("case_notes", "duration_minutes")

    op.drop_table("case_status_history")
    op.drop_index("ix_case_transfers_status", table_name="case_transfers")
    op.drop_table("case_transfers")
    op.drop_index("ix_case_restrictions_active", table_name="case_restrictions")
    op.drop_table("case_restrictions")
    op.drop_table("case_links")
    op.drop_index("ix_case_sources_category", table_name="case_sources")
    op.drop_table("case_sources")
    op.drop_table("case_external_workers")
    op.drop_index("ix_case_assignments_role", table_name="case_assignments")
    op.drop_index("ix_case_assignments_active", table_name="case_assignments")
    op.drop_table("case_assignments")
    op.drop_index("ix_case_people_role", table_name="case_people")
    op.drop_table("case_people")

    op.drop_index("ix_cases_case_type", table_name="cases")
    op.drop_index("ix_cases_stage", table_name="cases")
    op.drop_column("cases", "reopened_reason")
    op.drop_column("cases", "reopened_by")
    op.drop_column("cases", "reopened_at")
    op.drop_column("cases", "closed_reason")
    op.drop_column("cases", "stage")

    op.drop_table("case_sequences")
