"""012 — Reporting, Quality Assurance, Audit Tickler, Passports & Custom Dashboards.

Revision ID: 012_reporting_qa
Revises: 011_finance_billing
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "012_reporting_qa"
down_revision: str | None = "011_finance_billing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create saved_reports table ──────────────────────────────
    op.create_table(
        "saved_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("dataset_key", sa.String(length=100), nullable=False),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("visibility", sa.String(length=50), nullable=False, server_default="PRIVATE"),
        sa.Column("configuration", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_saved_reports_owner", "saved_reports", ["owner_user_id"])
    op.create_index("ix_saved_reports_team", "saved_reports", ["team_id"])
    op.create_index("ix_saved_reports_dataset", "saved_reports", ["dataset_key"])

    # ── 2. Create report_runs table ────────────────────────────────
    op.create_table(
        "report_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "saved_report_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("saved_reports.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "run_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="RUNNING"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("export_format", sa.String(length=20), nullable=True),
        sa.Column("parameters_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index("ix_report_runs_saved_report", "report_runs", ["saved_report_id"])
    op.create_index("ix_report_runs_run_by", "report_runs", ["run_by_id"])
    op.create_index("ix_report_runs_started", "report_runs", ["started_at"])

    # ── 3. Create qa_audit_templates table ─────────────────────────
    op.create_table(
        "qa_audit_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cadence", sa.String(length=50), nullable=False, server_default="QUARTERLY"),
        sa.Column("target_case_type", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_qa_audit_templates_code", "qa_audit_templates", ["code"])

    # ── 4. Create qa_audit_template_versions table ──────────────────
    op.create_table(
        "qa_audit_template_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_audit_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "published_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("change_notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_qa_audit_template_versions_template", "qa_audit_template_versions", ["template_id"])

    # ── 5. Create qa_audit_template_items table ────────────────────
    op.create_table(
        "qa_audit_template_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_audit_template_versions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(length=100), nullable=False, server_default="General Documentation"),
        sa.Column("item_text", sa.String(length=500), nullable=False),
        sa.Column("guidance_notes", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="MEDIUM"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_qa_audit_template_items_version", "qa_audit_template_items", ["version_id"])

    # ── 6. Create qa_audits table ──────────────────────────────────
    op.create_table(
        "qa_audits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "case_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cases.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "template_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_audit_template_versions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("review_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        # Audit & Soft Delete
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "deleted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
    )
    op.create_index("ix_qa_audits_case", "qa_audits", ["case_id"])
    op.create_index("ix_qa_audits_reviewer", "qa_audits", ["reviewer_id"])
    op.create_index("ix_qa_audits_status", "qa_audits", ["status"])

    # ── 7. Create qa_audit_results table ───────────────────────────
    op.create_table(
        "qa_audit_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "audit_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_audits.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qa_audit_template_items.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("compliance", sa.String(length=20), nullable=False, server_default="YES"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("finding_severity", sa.String(length=50), nullable=True),
        sa.Column("followup_required", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_qa_audit_results_audit", "qa_audit_results", ["audit_id"])

    # ── 8. Create dashboard_widgets table ──────────────────────────
    op.create_table(
        "dashboard_widgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("widget_key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="OPERATIONAL"),
        sa.Column("required_permission", sa.String(length=100), nullable=True),
        sa.Column("default_width", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("default_height", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_dashboard_widgets_key", "dashboard_widgets", ["widget_key"])

    # ── 9. Create user_dashboard_widgets table ─────────────────────
    op.create_table(
        "user_dashboard_widgets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("widget_key", sa.String(length=100), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("width", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_visible", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("user_id", "widget_key", name="uq_user_dashboard_widget"),
    )
    op.create_index("ix_user_dashboard_widgets_user", "user_dashboard_widgets", ["user_id"])


def downgrade() -> None:
    op.drop_table("user_dashboard_widgets")
    op.drop_table("dashboard_widgets")
    op.drop_table("qa_audit_results")
    op.drop_table("qa_audits")
    op.drop_table("qa_audit_template_items")
    op.drop_table("qa_audit_template_versions")
    op.drop_table("qa_audit_templates")
    op.drop_table("report_runs")
    op.drop_table("saved_reports")
