"""Pydantic schemas for Finance, Purchase Orders, Invoices & Rates (Phase 10)."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Funding Sources ──────────────────────────────────────────
class FundingSourceBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    funder_name: str = Field(..., max_length=255)
    status: str = Field(default="ACTIVE", max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    total_allocation: Decimal = Field(default=Decimal("0.00"), ge=0)
    notes: str | None = None


class FundingSourceCreate(FundingSourceBase):
    pass


class FundingSourceUpdate(BaseModel):
    name: str | None = None
    funder_name: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    total_allocation: Decimal | None = Field(default=None, ge=0)
    notes: str | None = None


class FundingSourceResponse(FundingSourceBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Budget Lines ─────────────────────────────────────────────
class BudgetLineBase(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    funding_source_id: uuid.UUID | None = None
    program_name: str = Field(default="CHILD_AND_FAMILY_WELLNESS", max_length=100)
    team_id: uuid.UUID | None = None
    fiscal_year: str = Field(default="2026-2027", max_length=20)
    allocated_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    is_active: bool = True
    notes: str | None = None


class BudgetLineCreate(BudgetLineBase):
    pass


class BudgetLineUpdate(BaseModel):
    name: str | None = None
    funding_source_id: uuid.UUID | None = None
    program_name: str | None = None
    team_id: uuid.UUID | None = None
    fiscal_year: str | None = None
    allocated_amount: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = None
    notes: str | None = None


class BudgetLineResponse(BudgetLineBase):
    id: uuid.UUID
    funding_source: FundingSourceResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Service Request Items ────────────────────────────────────
class ServiceRequestItemCreate(BaseModel):
    budget_line_id: uuid.UUID | None = None
    funding_source_id: uuid.UUID | None = None
    description: str = Field(..., max_length=500)
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(default=Decimal("0.00"), ge=0)
    line_total: Decimal | None = Field(default=None, ge=0)
    sort_order: int = 0


class ServiceRequestItemResponse(BaseModel):
    id: uuid.UUID
    service_request_id: uuid.UUID
    budget_line_id: uuid.UUID | None = None
    funding_source_id: uuid.UUID | None = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    sort_order: int
    created_at: datetime
    budget_line: BudgetLineResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Service Request Approvals ────────────────────────────────
class ServiceRequestApprovalResponse(BaseModel):
    id: uuid.UUID
    service_request_id: uuid.UUID
    approver_id: uuid.UUID
    step_number: int
    status: str
    comments: str | None = None
    decided_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Service Requests (PO & Reimbursement) ────────────────────
class ServiceRequestCreate(BaseModel):
    request_type: Literal["PURCHASE_ORDER", "REIMBURSEMENT"] = "PURCHASE_ORDER"
    title: str = Field(..., max_length=255)
    description: str | None = None
    team_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    currency: str = Field(default="CAD", max_length=3)
    tax_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    vendor_name: str | None = None
    payee_name: str | None = None
    notes: str | None = None
    items: list[ServiceRequestItemCreate]


class ServiceRequestResponse(BaseModel):
    id: uuid.UUID
    request_number: str
    request_type: str
    title: str
    description: str | None = None
    requestor_id: uuid.UUID
    team_id: uuid.UUID | None = None
    case_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    family_id: uuid.UUID | None = None
    status: str
    currency: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    vendor_name: str | None = None
    payee_name: str | None = None
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: uuid.UUID | None = None
    return_reason: str | None = None
    denial_reason: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    items: list[ServiceRequestItemResponse] = []
    approvals: list[ServiceRequestApprovalResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ServiceRequestApprovalAction(BaseModel):
    comments: str | None = None
    reason: str | None = None


# ── Billing Rates ────────────────────────────────────────────
class BillingRateBase(BaseModel):
    home_type: str = Field(default="FOSTER_HOME", max_length=50)
    age_min: int = Field(default=0, ge=0)
    age_max: int = Field(default=17, ge=0)
    daily_rate: Decimal = Field(default=Decimal("0.00"), ge=0)
    monthly_rate: Decimal | None = Field(default=None, ge=0)
    currency: str = Field(default="CAD", max_length=3)
    effective_from: date
    effective_to: date | None = None
    is_active: bool = True
    notes: str | None = None


class BillingRateCreate(BillingRateBase):
    pass


class BillingRateResponse(BillingRateBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Invoices & Items ─────────────────────────────────────────
class InvoiceItemResponse(BaseModel):
    id: uuid.UUID
    invoice_id: uuid.UUID
    child_id: uuid.UUID
    child_name: str
    placement_episode_id: uuid.UUID
    service_start_date: date
    service_end_date: date
    age_at_service: int
    rate_band_label: str
    billable_days: int
    daily_rate: Decimal
    line_total: Decimal
    is_federally_eligible: bool
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceGenerateRequest(BaseModel):
    placement_home_id: uuid.UUID
    billing_period_start: date
    billing_period_end: date


class InvoiceVoidRequest(BaseModel):
    void_reason: str = Field(..., min_length=3)


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    placement_home_id: uuid.UUID
    billing_period_start: date
    billing_period_end: date
    status: str
    currency: str
    subtotal: Decimal
    total_amount: Decimal
    generated_by: uuid.UUID | None = None
    generated_at: datetime
    finalized_by: uuid.UUID | None = None
    finalized_at: datetime | None = None
    voided_by: uuid.UUID | None = None
    voided_at: datetime | None = None
    void_reason: str | None = None
    notes: str | None = None
    created_at: datetime
    items: list[InvoiceItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ── Dashboard & Spending Metrics ─────────────────────────────
class DashboardMetricsResponse(BaseModel):
    pending_requests_count: int
    pending_requests_value: Decimal
    approved_requests_count: int
    approved_requests_value: Decimal
    finalized_invoices_count: int
    finalized_invoices_value: Decimal
    currency: str = "CAD"


class CaseSpendingResponse(BaseModel):
    case_id: uuid.UUID
    approved_spending: Decimal
    approved_request_count: int


class FamilySpendingResponse(BaseModel):
    family_id: uuid.UUID
    approved_spending: Decimal
    approved_request_count: int
