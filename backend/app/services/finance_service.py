"""Finance Domain Service for CRBCL (Phase 10)."""

import uuid
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import (
    BudgetLine,
    FundingSource,
    Invoice,
    ServiceRequest,
    ServiceRequestApproval,
)
from app.models.outbox import OutboxEvent
from app.repositories.finance_repo import FinanceRepository

# Authoritative Money Helpers (ADR-022)
TWO_PLACES = Decimal("0.01")


def quantize_money(val: Decimal | str | float | int) -> Decimal:
    """Quantize to 2 decimal places using deterministic ROUND_HALF_UP."""
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


class FinanceService:
    """Service handling financial requests, approvals, budget lines and spending rollups."""

    @staticmethod
    async def create_funding_source(session: AsyncSession, data: dict, user_id: uuid.UUID) -> FundingSource:
        data["total_allocation"] = quantize_money(data.get("total_allocation", Decimal("0.00")))
        data["created_by"] = user_id
        data["updated_by"] = user_id
        return await FinanceRepository.create_funding_source(session, data)

    @staticmethod
    async def get_funding_sources(session: AsyncSession, status: str | None = None) -> list[FundingSource]:
        return await FinanceRepository.get_funding_sources(session, status=status)

    @staticmethod
    async def create_budget_line(session: AsyncSession, data: dict, user_id: uuid.UUID) -> BudgetLine:
        data["allocated_amount"] = quantize_money(data.get("allocated_amount", Decimal("0.00")))
        data["created_by"] = user_id
        data["updated_by"] = user_id
        return await FinanceRepository.create_budget_line(session, data)

    @staticmethod
    async def get_budget_lines(
        session: AsyncSession,
        fiscal_year: str | None = None,
        is_active: bool | None = None,
    ) -> list[BudgetLine]:
        return await FinanceRepository.get_budget_lines(session, fiscal_year=fiscal_year, is_active=is_active)

    # ── Service Requests (Purchase Orders & Reimbursements) ─────
    @staticmethod
    def calculate_request_totals(
        items: list[dict], tax_rate: Decimal = Decimal("0.00")
    ) -> tuple[list[dict], Decimal, Decimal, Decimal]:
        """Authoritatively compute line totals, subtotal, tax, and grand total in Decimal."""
        subtotal = Decimal("0.00")
        computed_items = []

        for idx, item in enumerate(items):
            qty = Decimal(str(item.get("quantity", "1.00")))
            price = quantize_money(item.get("unit_price", "0.00"))
            line_tot = quantize_money(qty * price)
            subtotal += line_tot

            item_dict = dict(item)
            item_dict["quantity"] = qty
            item_dict["unit_price"] = price
            item_dict["line_total"] = line_tot
            item_dict["sort_order"] = item.get("sort_order", idx)
            computed_items.append(item_dict)

        subtotal = quantize_money(subtotal)
        tax = quantize_money(subtotal * tax_rate) if tax_rate > Decimal("0.00") else Decimal("0.00")
        total = quantize_money(subtotal + tax)

        return computed_items, subtotal, tax, total

    @classmethod
    async def create_service_request(
        cls,
        session: AsyncSession,
        payload: dict,
        user_id: uuid.UUID,
    ) -> ServiceRequest:
        """Create a new draft Purchase Order or Reimbursement with authoritative server calculation."""
        items = payload.get("items", [])
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one line item is required")

        req_type = payload.get("request_type", "PURCHASE_ORDER")
        tax_rate = Decimal(str(payload.get("tax_rate", "0.00")))

        computed_items, subtotal, tax_amount, total_amount = cls.calculate_request_totals(items, tax_rate)

        # Reject or overwrite client-supplied totals
        req_number = await FinanceRepository.generate_request_number(session, req_type)

        request_data = {
            "request_number": req_number,
            "request_type": req_type,
            "title": payload["title"],
            "description": payload.get("description"),
            "requestor_id": user_id,
            "team_id": payload.get("team_id"),
            "case_id": payload.get("case_id"),
            "person_id": payload.get("person_id"),
            "family_id": payload.get("family_id"),
            "status": "DRAFT",
            "currency": payload.get("currency", "CAD"),
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "total_amount": total_amount,
            "vendor_name": payload.get("vendor_name"),
            "payee_name": payload.get("payee_name"),
            "notes": payload.get("notes"),
            "created_by": user_id,
            "updated_by": user_id,
        }

        req = await FinanceRepository.create_service_request(session, request_data, computed_items)
        return await FinanceRepository.get_service_request_by_id(session, req.id)

    @classmethod
    async def submit_service_request(
        cls,
        session: AsyncSession,
        request_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ServiceRequest:
        """Submit a draft or returned request for supervisor approval."""
        req = await FinanceRepository.get_service_request_by_id(session, request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

        if req.status not in ["DRAFT", "RETURNED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot submit request in {req.status} status",
            )

        req.status = "PENDING_APPROVAL"
        req.submitted_at = datetime.utcnow()
        req.updated_by = user_id
        req.updated_at = datetime.utcnow()

        # Emit outbox notification
        outbox_event = OutboxEvent(
            aggregate_type="FINANCE_REQUEST",
            aggregate_id=req.id,
            event_type="FINANCE_REQUEST_SUBMITTED",
            payload={
                "request_id": str(req.id),
                "request_number": req.request_number,
                "request_type": req.request_type,
                "title": req.title,
                "total_amount": str(req.total_amount),
                "currency": req.currency,
                "requestor_id": str(req.requestor_id),
            },
        )
        session.add(outbox_event)
        await session.flush()
        await session.refresh(req, ["approvals", "items"])
        return req

    @classmethod
    async def approve_service_request(
        cls,
        session: AsyncSession,
        request_id: uuid.UUID,
        approver_id: uuid.UUID,
        comments: str | None = None,
    ) -> ServiceRequest:
        """Approve a financial request. Strictly enforces Segregation of Duties."""
        req = await FinanceRepository.get_service_request_by_id(session, request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

        if req.status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot approve request in {req.status} status",
            )

        # ── SEGREGATION OF DUTIES (ADR-023) ──
        if req.requestor_id == approver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requester cannot approve their own financial request (Segregation of Duties)",
            )

        req.status = "APPROVED"
        req.approved_at = datetime.utcnow()
        req.approved_by = approver_id
        req.updated_by = approver_id
        req.updated_at = datetime.utcnow()

        approval_step = ServiceRequestApproval(
            service_request_id=req.id,
            approver_id=approver_id,
            step_number=len(req.approvals) + 1,
            status="APPROVED",
            comments=comments,
            decided_at=datetime.utcnow(),
        )
        session.add(approval_step)

        # Emit outbox notification
        outbox_event = OutboxEvent(
            aggregate_type="FINANCE_REQUEST",
            aggregate_id=req.id,
            event_type="FINANCE_REQUEST_APPROVED",
            payload={
                "request_id": str(req.id),
                "request_number": req.request_number,
                "title": req.title,
                "total_amount": str(req.total_amount),
                "approver_id": str(approver_id),
                "requestor_id": str(req.requestor_id),
            },
        )
        session.add(outbox_event)
        await session.flush()
        await session.refresh(req, ["approvals", "items"])
        return req

    @classmethod
    async def return_service_request(
        cls,
        session: AsyncSession,
        request_id: uuid.UUID,
        approver_id: uuid.UUID,
        reason: str,
    ) -> ServiceRequest:
        """Return request to requestor for amendment. Mandatory reason required."""
        if not reason or not reason.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Return reason is required")

        req = await FinanceRepository.get_service_request_by_id(session, request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

        if req.status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot return request in {req.status} status",
            )

        if req.requestor_id == approver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requester cannot review their own financial request",
            )

        req.status = "RETURNED"
        req.return_reason = reason.strip()
        req.updated_by = approver_id
        req.updated_at = datetime.utcnow()

        approval_step = ServiceRequestApproval(
            service_request_id=req.id,
            approver_id=approver_id,
            step_number=len(req.approvals) + 1,
            status="RETURNED",
            comments=reason.strip(),
            decided_at=datetime.utcnow(),
        )
        session.add(approval_step)

        # Emit outbox notification
        outbox_event = OutboxEvent(
            aggregate_type="FINANCE_REQUEST",
            aggregate_id=req.id,
            event_type="FINANCE_REQUEST_RETURNED",
            payload={
                "request_id": str(req.id),
                "request_number": req.request_number,
                "reason": reason.strip(),
                "requestor_id": str(req.requestor_id),
            },
        )
        session.add(outbox_event)
        await session.flush()
        await session.refresh(req, ["approvals", "items"])
        return req

    @classmethod
    async def deny_service_request(
        cls,
        session: AsyncSession,
        request_id: uuid.UUID,
        approver_id: uuid.UUID,
        reason: str,
    ) -> ServiceRequest:
        """Deny request with mandatory explanatory reason."""
        if not reason or not reason.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Denial reason is required")

        req = await FinanceRepository.get_service_request_by_id(session, request_id)
        if not req:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

        if req.status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot deny request in {req.status} status",
            )

        if req.requestor_id == approver_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requester cannot review their own financial request",
            )

        req.status = "DENIED"
        req.denial_reason = reason.strip()
        req.updated_by = approver_id
        req.updated_at = datetime.utcnow()

        approval_step = ServiceRequestApproval(
            service_request_id=req.id,
            approver_id=approver_id,
            step_number=len(req.approvals) + 1,
            status="DENIED",
            comments=reason.strip(),
            decided_at=datetime.utcnow(),
        )
        session.add(approval_step)

        # Emit outbox notification
        outbox_event = OutboxEvent(
            aggregate_type="FINANCE_REQUEST",
            aggregate_id=req.id,
            event_type="FINANCE_REQUEST_DENIED",
            payload={
                "request_id": str(req.id),
                "request_number": req.request_number,
                "reason": reason.strip(),
                "requestor_id": str(req.requestor_id),
            },
        )
        session.add(outbox_event)
        await session.flush()
        await session.refresh(req, ["approvals", "items"])
        return req

    # ── Dashboard & Spending Metrics ─────────────────────────────
    @staticmethod
    async def get_dashboard_metrics(session: AsyncSession) -> dict:
        # Pending requests
        pending_stmt = select(
            func.count(ServiceRequest.id), func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00"))
        ).where(ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "PENDING_APPROVAL")
        pending_res = await session.execute(pending_stmt)
        pending_count, pending_val = pending_res.one()

        # Approved requests
        approved_stmt = select(
            func.count(ServiceRequest.id), func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00"))
        ).where(ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "APPROVED")
        approved_res = await session.execute(approved_stmt)
        approved_count, approved_val = approved_res.one()

        # Placement invoices
        invoice_stmt = select(
            func.count(Invoice.id), func.coalesce(func.sum(Invoice.total_amount), Decimal("0.00"))
        ).where(Invoice.deleted_at.is_(None), Invoice.status.in_(["FINALIZED", "PAID"]))
        inv_res = await session.execute(invoice_stmt)
        inv_count, inv_val = inv_res.one()

        return {
            "pending_requests_count": pending_count,
            "pending_requests_value": pending_val,
            "approved_requests_count": approved_count,
            "approved_requests_value": approved_val,
            "finalized_invoices_count": inv_count,
            "finalized_invoices_value": inv_val,
            "currency": "CAD",
        }
