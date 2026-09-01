"""Finance and Placement Billing models (Phase 10)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin


class FundingSource(Base, AuditMixin, SoftDeleteMixin):
    """Funding source/granting agency allocation entity."""

    __tablename__ = "funding_sources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    funder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE", index=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_allocation: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    budget_lines = relationship("BudgetLine", back_populates="funding_source")

    __table_args__ = (CheckConstraint("total_allocation >= 0", name="ck_funding_sources_total_allocation_positive"),)


class BudgetLine(Base, AuditMixin, SoftDeleteMixin):
    """Budget line allocation for programs and teams."""

    __tablename__ = "budget_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    funding_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funding_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    program_name: Mapped[str] = mapped_column(String(100), nullable=False, default="CHILD_AND_FAMILY_WELLNESS")
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    fiscal_year: Mapped[str] = mapped_column(String(20), nullable=False, default="2026-2027", index=True)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    funding_source = relationship("FundingSource", back_populates="budget_lines")
    team = relationship("Team", foreign_keys=[team_id])

    __table_args__ = (CheckConstraint("allocated_amount >= 0", name="ck_budget_lines_allocated_amount_positive"),)


class ServiceRequest(Base, AuditMixin, SoftDeleteMixin):
    """Financial service request (Purchase Order or Staff Reimbursement)."""

    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    request_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PURCHASE_ORDER", index=True
    )  # PURCHASE_ORDER, REIMBURSEMENT
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requestor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    case_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    family_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("families.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFT", index=True
    )  # DRAFT, SUBMITTED, PENDING_APPROVAL, APPROVED, RETURNED, DENIED, CANCELLED
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payee_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    denial_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    requestor = relationship("User", foreign_keys=[requestor_id])
    approver = relationship("User", foreign_keys=[approved_by])
    team = relationship("Team", foreign_keys=[team_id])
    case = relationship("Case", foreign_keys=[case_id])
    person = relationship("Person", foreign_keys=[person_id])
    family = relationship("Family", foreign_keys=[family_id])

    items = relationship(
        "ServiceRequestItem", back_populates="service_request", cascade="all, delete-orphan", lazy="selectin"
    )
    approvals = relationship(
        "ServiceRequestApproval", back_populates="service_request", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint("subtotal >= 0", name="ck_service_requests_subtotal_positive"),
        CheckConstraint("tax_amount >= 0", name="ck_service_requests_tax_positive"),
        CheckConstraint("total_amount >= 0", name="ck_service_requests_total_positive"),
    )


class ServiceRequestItem(Base):
    """Line item on a purchase order or reimbursement request."""

    __tablename__ = "service_request_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    budget_line_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("budget_lines.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    funding_source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("funding_sources.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("1.00"))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    service_request = relationship("ServiceRequest", back_populates="items")
    budget_line = relationship("BudgetLine")
    funding_source = relationship("FundingSource")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_service_request_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_service_request_items_unit_price_positive"),
        CheckConstraint("line_total >= 0", name="ck_service_request_items_line_total_positive"),
    )


class ServiceRequestApproval(Base):
    """Immutable audit trail step for financial reviews and decisions."""

    __tablename__ = "service_request_approvals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("service_requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    step_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="PENDING"
    )  # PENDING, APPROVED, RETURNED, DENIED
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    service_request = relationship("ServiceRequest", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])


class BillingRate(Base, AuditMixin, SoftDeleteMixin):
    """Placement per-diem and care rates with temporal versioning."""

    __tablename__ = "billing_rates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    home_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="FOSTER_HOME", index=True
    )  # FOSTER_HOME, KINSHIP, CUSTOMARY_CARE, GROUP_HOME, SPECIALIZED
    age_min: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    age_max: Mapped[int] = mapped_column(Integer, nullable=False, default=17)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    monthly_rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("age_max >= age_min", name="ck_billing_rates_age_max_gte_min"),
        CheckConstraint("daily_rate >= 0", name="ck_billing_rates_daily_rate_positive"),
    )


class Invoice(Base, AuditMixin, SoftDeleteMixin):
    """Placement home monthly billing invoice."""

    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    placement_home_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_homes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    billing_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    billing_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFT", index=True
    )  # DRAFT, GENERATED, REVIEWED, FINALIZED, PAID, VOID
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="CAD")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voided_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    voided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    placement_home = relationship("PlacementHome")
    generator = relationship("User", foreign_keys=[generated_by])
    finalizer = relationship("User", foreign_keys=[finalized_by])
    voider = relationship("User", foreign_keys=[voided_by])

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        CheckConstraint("billing_period_end >= billing_period_start", name="ck_invoices_period_end_gte_start"),
        CheckConstraint("subtotal >= 0", name="ck_invoices_subtotal_positive"),
        CheckConstraint("total_amount >= 0", name="ck_invoices_total_positive"),
    )


class InvoiceItem(Base):
    """Immutable calculation snapshot item on an invoice."""

    __tablename__ = "invoice_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    child_name: Mapped[str] = mapped_column(String(255), nullable=False)
    placement_episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("placement_episodes.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    service_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    service_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    age_at_service: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_band_label: Mapped[str] = mapped_column(String(100), nullable=False, default="Standard Per Diem")
    billable_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    daily_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    is_federally_eligible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    child = relationship("Person", foreign_keys=[child_id])
    placement_episode = relationship("PlacementEpisode", foreign_keys=[placement_episode_id])

    __table_args__ = (
        CheckConstraint("billable_days >= 0", name="ck_invoice_items_billable_days_positive"),
        CheckConstraint("daily_rate >= 0", name="ck_invoice_items_daily_rate_positive"),
        CheckConstraint("line_total >= 0", name="ck_invoice_items_line_total_positive"),
    )
