"""011 — Finance, Purchase Orders, Reimbursements, Budget Lines, Approvals, Placement Billing Rates, Invoices & Ledger.

Revision ID: 011_finance_billing
Revises: 010_scheduling_notifications
Create Date: 2026-09-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_finance_billing"
down_revision: str | None = "010_scheduling_notifications"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create funding_sources table ─────────────────────────
    op.create_table(
        "funding_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("funder_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("total_allocation", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint("total_allocation >= 0", name="ck_funding_sources_total_allocation_positive"),
    )
    op.create_index("ix_funding_sources_code", "funding_sources", ["code"])
    op.create_index("ix_funding_sources_status", "funding_sources", ["status"])

    # ── 2. Create budget_lines table ────────────────────────────
    op.create_table(
        "budget_lines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(length=50), nullable=False, unique=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "funding_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("funding_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("program_name", sa.String(length=100), nullable=False, server_default="CHILD_AND_FAMILY_WELLNESS"),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("fiscal_year", sa.String(length=20), nullable=False, server_default="2026-2027"),
        sa.Column("allocated_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint("allocated_amount >= 0", name="ck_budget_lines_allocated_amount_positive"),
    )
    op.create_index("ix_budget_lines_code", "budget_lines", ["code"])
    op.create_index("ix_budget_lines_funding_source", "budget_lines", ["funding_source_id"])
    op.create_index("ix_budget_lines_fiscal_year", "budget_lines", ["fiscal_year"])
    op.create_index("ix_budget_lines_is_active", "budget_lines", ["is_active"])

    # ── 3. Create service_requests table (Purchase Orders & Reimbursements) ──
    op.create_table(
        "service_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("request_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column("request_type", sa.String(length=50), nullable=False, server_default="PURCHASE_ORDER"),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "requestor_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "person_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column(
            "family_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("families.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CAD"),
        sa.Column("subtotal", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("tax_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("vendor_name", sa.String(length=255), nullable=True),
        sa.Column("payee_name", sa.String(length=255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("return_reason", sa.Text(), nullable=True),
        sa.Column("denial_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint("subtotal >= 0", name="ck_service_requests_subtotal_positive"),
        sa.CheckConstraint("tax_amount >= 0", name="ck_service_requests_tax_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_service_requests_total_positive"),
    )
    op.create_index("ix_service_requests_request_number", "service_requests", ["request_number"])
    op.create_index("ix_service_requests_request_type", "service_requests", ["request_type"])
    op.create_index("ix_service_requests_status", "service_requests", ["status"])
    op.create_index("ix_service_requests_requestor", "service_requests", ["requestor_id"])
    op.create_index("ix_service_requests_case", "service_requests", ["case_id"])
    op.create_index("ix_service_requests_family", "service_requests", ["family_id"])

    # ── 4. Create service_request_items table ───────────────────
    op.create_table(
        "service_request_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "service_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "budget_line_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("budget_lines.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "funding_source_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("funding_sources.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False, server_default="1.00"),
        sa.Column("unit_price", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("line_total", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("quantity > 0", name="ck_service_request_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_service_request_items_unit_price_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_service_request_items_line_total_positive"),
    )
    op.create_index("ix_service_request_items_request", "service_request_items", ["service_request_id"])
    op.create_index("ix_service_request_items_budget_line", "service_request_items", ["budget_line_id"])

    # ── 5. Create service_request_approvals table ───────────────
    op.create_table(
        "service_request_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "service_request_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("service_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "approver_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("step_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_service_request_approvals_request", "service_request_approvals", ["service_request_id"])
    op.create_index("ix_service_request_approvals_approver", "service_request_approvals", ["approver_id"])

    # ── 6. Create billing_rates table ───────────────────────────
    op.create_table(
        "billing_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("home_type", sa.String(length=50), nullable=False, server_default="FOSTER_HOME"),
        sa.Column("age_min", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("age_max", sa.Integer(), nullable=False, server_default="17"),
        sa.Column("daily_rate", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("monthly_rate", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CAD"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint("age_max >= age_min", name="ck_billing_rates_age_max_gte_min"),
        sa.CheckConstraint("daily_rate >= 0", name="ck_billing_rates_daily_rate_positive"),
    )
    op.create_index("ix_billing_rates_home_type", "billing_rates", ["home_type"])
    op.create_index("ix_billing_rates_effective", "billing_rates", ["effective_from", "effective_to"])
    op.create_index("ix_billing_rates_is_active", "billing_rates", ["is_active"])

    # ── 7. Create invoices table ────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_number", sa.String(length=50), nullable=False, unique=True),
        sa.Column(
            "placement_home_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_homes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("billing_period_start", sa.Date(), nullable=False),
        sa.Column("billing_period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="CAD"),
        sa.Column("subtotal", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("total_amount", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column(
            "generated_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column(
            "finalized_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "voided_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        ),
        sa.Column("voided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
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
        sa.CheckConstraint("billing_period_end >= billing_period_start", name="ck_invoices_period_end_gte_start"),
        sa.CheckConstraint("subtotal >= 0", name="ck_invoices_subtotal_positive"),
        sa.CheckConstraint("total_amount >= 0", name="ck_invoices_total_positive"),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"])
    op.create_index("ix_invoices_placement_home", "invoices", ["placement_home_id"])
    op.create_index("ix_invoices_billing_period", "invoices", ["billing_period_start", "billing_period_end"])
    op.create_index("ix_invoices_status", "invoices", ["status"])

    # ── 8. Create invoice_items table (Immutable Snapshots) ─────
    op.create_table(
        "invoice_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "invoice_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("invoices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "child_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("child_name", sa.String(length=255), nullable=False),
        sa.Column(
            "placement_episode_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("placement_episodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("service_start_date", sa.Date(), nullable=False),
        sa.Column("service_end_date", sa.Date(), nullable=False),
        sa.Column("age_at_service", sa.Integer(), nullable=False),
        sa.Column("rate_band_label", sa.String(length=100), nullable=False, server_default="Standard Per Diem"),
        sa.Column("billable_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("daily_rate", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("line_total", sa.Numeric(precision=14, scale=2), nullable=False, server_default="0.00"),
        sa.Column("is_federally_eligible", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("billable_days >= 0", name="ck_invoice_items_billable_days_positive"),
        sa.CheckConstraint("daily_rate >= 0", name="ck_invoice_items_daily_rate_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_invoice_items_line_total_positive"),
    )
    op.create_index("ix_invoice_items_invoice", "invoice_items", ["invoice_id"])
    op.create_index("ix_invoice_items_child", "invoice_items", ["child_id"])
    op.create_index("ix_invoice_items_placement_episode", "invoice_items", ["placement_episode_id"])


def downgrade() -> None:
    op.drop_table("invoice_items")
    op.drop_table("invoices")
    op.drop_table("billing_rates")
    op.drop_table("service_request_approvals")
    op.drop_table("service_request_items")
    op.drop_table("service_requests")
    op.drop_table("budget_lines")
    op.drop_table("funding_sources")
