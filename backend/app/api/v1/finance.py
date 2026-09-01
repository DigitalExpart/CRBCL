"""Finance, Purchase Orders, Reimbursements, Billing Rates, Invoices & Ledger Router (Phase 10)."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.finance_repo import FinanceRepository
from app.schemas.finance import (
    BillingRateCreate,
    BillingRateResponse,
    BudgetLineCreate,
    BudgetLineResponse,
    CaseSpendingResponse,
    DashboardMetricsResponse,
    FamilySpendingResponse,
    FundingSourceCreate,
    FundingSourceResponse,
    InvoiceGenerateRequest,
    InvoiceResponse,
    InvoiceVoidRequest,
    ServiceRequestApprovalAction,
    ServiceRequestCreate,
    ServiceRequestResponse,
)
from app.services.finance_service import FinanceService
from app.services.placement_billing_service import PlacementBillingService

router = APIRouter(prefix="/finance", tags=["Finance & Billing"])


# ── 1. Funding Sources ──────────────────────────────────────────
@router.get(
    "/funding-sources",
    response_model=list[FundingSourceResponse],
    dependencies=[Depends(require_permission(Permissions.FINANCE_BUDGET_READ))],
)
async def list_funding_sources(
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService.get_funding_sources(db, status=status)


@router.post(
    "/funding-sources",
    response_model=FundingSourceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.FINANCE_BUDGET_MANAGE))],
)
async def create_funding_source(
    payload: FundingSourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_BUDGET_MANAGE)),
):
    return await FinanceService.create_funding_source(db, payload.model_dump(), current_user.id)


# ── 2. Budget Lines ─────────────────────────────────────────────
@router.get(
    "/budget-lines",
    response_model=list[BudgetLineResponse],
    dependencies=[Depends(require_permission(Permissions.FINANCE_BUDGET_READ))],
)
async def list_budget_lines(
    fiscal_year: str | None = None,
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService.get_budget_lines(db, fiscal_year=fiscal_year, is_active=is_active)


@router.post(
    "/budget-lines",
    response_model=BudgetLineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.FINANCE_BUDGET_MANAGE))],
)
async def create_budget_line(
    payload: BudgetLineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_BUDGET_MANAGE)),
):
    return await FinanceService.create_budget_line(db, payload.model_dump(), current_user.id)


# ── 3. Service Requests (PO & Reimbursement) ────────────────────
@router.get(
    "/requests",
    response_model=list[ServiceRequestResponse],
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def list_service_requests(
    request_type: str | None = None,
    status: str | None = None,
    requestor_id: uuid.UUID | None = None,
    case_id: uuid.UUID | None = None,
    family_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    requests, _ = await FinanceRepository.get_service_requests(
        db,
        request_type=request_type,
        status=status,
        requestor_id=requestor_id,
        case_id=case_id,
        family_id=family_id,
        limit=limit,
        offset=offset,
    )
    return requests


@router.post(
    "/requests",
    response_model=ServiceRequestResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_CREATE))],
)
async def create_service_request(
    payload: ServiceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_REQUEST_CREATE)),
):
    return await FinanceService.create_service_request(db, payload.model_dump(), current_user.id)


@router.get(
    "/requests/{request_id}",
    response_model=ServiceRequestResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def get_service_request_detail(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    req = await FinanceRepository.get_service_request_by_id(db, request_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    return req


@router.post(
    "/requests/{request_id}/submit",
    response_model=ServiceRequestResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_SUBMIT))],
)
async def submit_service_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_REQUEST_SUBMIT)),
):
    return await FinanceService.submit_service_request(db, request_id, current_user.id)


@router.post(
    "/requests/{request_id}/approve",
    response_model=ServiceRequestResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_APPROVE))],
)
async def approve_service_request(
    request_id: uuid.UUID,
    action: ServiceRequestApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_REQUEST_APPROVE)),
):
    return await FinanceService.approve_service_request(db, request_id, current_user.id, comments=action.comments)


@router.post(
    "/requests/{request_id}/return",
    response_model=ServiceRequestResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_RETURN))],
)
async def return_service_request(
    request_id: uuid.UUID,
    action: ServiceRequestApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_REQUEST_RETURN)),
):
    reason = action.reason or action.comments or ""
    return await FinanceService.return_service_request(db, request_id, current_user.id, reason=reason)


@router.post(
    "/requests/{request_id}/deny",
    response_model=ServiceRequestResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_DENY))],
)
async def deny_service_request(
    request_id: uuid.UUID,
    action: ServiceRequestApprovalAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_REQUEST_DENY)),
):
    reason = action.reason or action.comments or ""
    return await FinanceService.deny_service_request(db, request_id, current_user.id, reason=reason)


# ── 4. Placement Billing Rates ──────────────────────────────
@router.get(
    "/rates",
    response_model=list[BillingRateResponse],
    dependencies=[Depends(require_permission(Permissions.FINANCE_RATE_READ))],
)
async def list_billing_rates(
    home_type: str | None = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
):
    return await FinanceRepository.get_billing_rates(db, home_type=home_type, active_only=active_only)


@router.post(
    "/rates",
    response_model=BillingRateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.FINANCE_RATE_MANAGE))],
)
async def create_billing_rate(
    payload: BillingRateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_RATE_MANAGE)),
):
    return await PlacementBillingService.create_billing_rate(db, payload.model_dump(), current_user.id)


# ── 5. Invoices & Billing Ledger ────────────────────────────
@router.get(
    "/invoices",
    response_model=list[InvoiceResponse],
    dependencies=[Depends(require_permission(Permissions.FINANCE_INVOICE_READ))],
)
async def list_invoices(
    placement_home_id: uuid.UUID | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    invoices, _ = await FinanceRepository.get_invoices(
        db,
        placement_home_id=placement_home_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return invoices


@router.post(
    "/invoices/generate",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.FINANCE_INVOICE_GENERATE))],
)
async def generate_draft_invoice(
    payload: InvoiceGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_INVOICE_GENERATE)),
):
    return await PlacementBillingService.generate_draft_invoice(
        db,
        placement_home_id=payload.placement_home_id,
        billing_period_start=payload.billing_period_start,
        billing_period_end=payload.billing_period_end,
        user_id=current_user.id,
    )


@router.get(
    "/invoices/{invoice_id}",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_INVOICE_READ))],
)
async def get_invoice_detail(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    inv = await FinanceRepository.get_invoice_by_id(db, invoice_id)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return inv


@router.post(
    "/invoices/{invoice_id}/finalize",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_INVOICE_FINALIZE))],
)
async def finalize_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_INVOICE_FINALIZE)),
):
    return await PlacementBillingService.finalize_invoice(db, invoice_id, current_user.id)


@router.post(
    "/invoices/{invoice_id}/void",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_INVOICE_VOID))],
)
async def void_invoice(
    invoice_id: uuid.UUID,
    payload: InvoiceVoidRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.FINANCE_INVOICE_VOID)),
):
    return await PlacementBillingService.void_invoice(db, invoice_id, current_user.id, void_reason=payload.void_reason)


# ── 6. Spending Metrics & Dashboard ─────────────────────────
@router.get(
    "/dashboard-metrics",
    response_model=DashboardMetricsResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
):
    return await FinanceService.get_dashboard_metrics(db)


@router.get(
    "/spending/cases/{case_id}",
    response_model=CaseSpendingResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def get_case_spending(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await FinanceRepository.get_spending_by_case(db, case_id)


@router.get(
    "/spending/families/{family_id}",
    response_model=FamilySpendingResponse,
    dependencies=[Depends(require_permission(Permissions.FINANCE_REQUEST_READ))],
)
async def get_family_spending(
    family_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    return await FinanceRepository.get_spending_by_family(db, family_id)
