"""Resource Finance Integration Service (Sprint 3).

Reuses existing Finance infrastructure (Invoices, ServiceRequests, BillingRates)
without creating duplicate general ledgers, POs, or reimbursement systems.
Enforces strict finance permission checks so Resource users cannot access
financial details unless explicitly granted finance read authority.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BillingRate, Invoice, ServiceRequest
from app.models.placement_home import PlacementHome
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.resource_finance import ResourceFinanceSummary


class ResourceFinanceService:
    """Service providing authorized finance roll-up for Resource Homes."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm = PermissionService(session)

    async def _require_finance_access(self, user_id: uuid.UUID) -> None:
        """Enforce that caller has at least one finance read permission."""
        has_inv = await self.perm.user_has_permission(user_id, Permissions.FINANCE_INVOICE_READ)
        has_req = await self.perm.user_has_permission(user_id, Permissions.FINANCE_REQUEST_READ)
        if not (has_inv or has_req):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to access financial information for Resource Homes.",
            )

    async def get_home_finance_summary(
        self, home_id: uuid.UUID, user: User
    ) -> ResourceFinanceSummary:
        """Fetch authorized financial summary for a Resource Home."""
        await self._require_finance_access(user.id)

        home = await self.session.get(PlacementHome, home_id)
        if not home or home.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement Home with ID '{home_id}' not found.",
            )

        today = date.today()
        current_year = today.year
        current_month = today.month
        fiscal_year = f"{current_year}-{current_year + 1}" if current_month >= 4 else f"{current_year - 1}-{current_year}"

        # 1. Active billing rate for this home type
        rate_stmt = (
            select(BillingRate)
            .where(
                BillingRate.home_type == home.home_type,
                BillingRate.is_active.is_(True),
                BillingRate.deleted_at.is_(None),
                BillingRate.effective_from <= today,
                (BillingRate.effective_to.is_(None) | (BillingRate.effective_to >= today)),
            )
            .order_by(desc(BillingRate.effective_from))
            .limit(1)
        )
        rate_res = await self.session.execute(rate_stmt)
        active_rate_obj = rate_res.scalars().first()
        active_rate = active_rate_obj.daily_rate if active_rate_obj else None
        rate_band_label = f"Standard {home.home_type.replace('_', ' ').title()} Rate" if active_rate else None

        # 2. Invoices summary
        inv_stmt = (
            select(Invoice)
            .where(Invoice.placement_home_id == home_id, Invoice.deleted_at.is_(None))
            .order_by(desc(Invoice.billing_period_start))
            .limit(10)
        )
        inv_res = await self.session.execute(inv_stmt)
        invoices = list(inv_res.scalars().all())

        monthly_invoiced_total = Decimal("0.00")
        ytd_invoiced_total = Decimal("0.00")
        recent_invoices: list[dict[str, Any]] = []

        for inv in invoices:
            recent_invoices.append({
                "id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "billing_period_start": str(inv.billing_period_start),
                "billing_period_end": str(inv.billing_period_end),
                "status": inv.status,
                "total_amount": float(inv.total_amount),
            })
            if inv.status in ["FINALIZED", "PAID"]:
                ytd_invoiced_total += inv.total_amount
                if inv.billing_period_start.year == current_year and inv.billing_period_start.month == current_month:
                    monthly_invoiced_total += inv.total_amount

        # 3. Service Requests linked to this placement home
        # Note: ServiceRequest can be linked via CaregiverSupport or by matching home ID
        from app.models.caregiver_support import CaregiverSupport

        sr_stmt = (
            select(ServiceRequest)
            .join(CaregiverSupport, CaregiverSupport.service_request_id == ServiceRequest.id)
            .where(
                CaregiverSupport.placement_home_id == home_id,
                ServiceRequest.deleted_at.is_(None),
            )
            .order_by(desc(ServiceRequest.created_at))
            .limit(10)
        )
        sr_res = await self.session.execute(sr_stmt)
        service_requests = list(sr_res.scalars().all())

        pending_count = 0
        pending_total = Decimal("0.00")
        approved_count = 0
        approved_total = Decimal("0.00")
        recent_sr: list[dict[str, Any]] = []

        for sr in service_requests:
            recent_sr.append({
                "id": str(sr.id),
                "request_number": sr.request_number,
                "request_type": sr.request_type,
                "title": sr.title,
                "status": sr.status,
                "total_amount": float(sr.total_amount),
            })
            if sr.status in ["DRAFT", "SUBMITTED", "PENDING_APPROVAL"]:
                pending_count += 1
                pending_total += sr.total_amount
            elif sr.status == "APPROVED":
                approved_count += 1
                approved_total += sr.total_amount

        return ResourceFinanceSummary(
            placement_home_id=home.id,
            home_name=home.name,
            home_code=home.home_code,
            current_fiscal_year=fiscal_year,
            active_rate=active_rate,
            rate_band_label=rate_band_label,
            monthly_invoiced_total=monthly_invoiced_total,
            year_to_date_invoiced_total=ytd_invoiced_total,
            pending_service_requests_count=pending_count,
            pending_service_requests_total=pending_total,
            approved_service_requests_count=approved_count,
            approved_service_requests_total=approved_total,
            recent_invoices=recent_invoices,
            recent_service_requests=recent_sr,
        )
