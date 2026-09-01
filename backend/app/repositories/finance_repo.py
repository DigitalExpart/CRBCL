"""Finance Repository for CRBCL (Phase 10)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.finance import (
    BillingRate,
    BudgetLine,
    FundingSource,
    Invoice,
    InvoiceItem,
    ServiceRequest,
    ServiceRequestApproval,
    ServiceRequestItem,
)
from app.models.placement import PlacementEpisode


class FinanceRepository:
    """Data access layer for Finance, Requests, Rates, Invoices & Ledger."""

    @staticmethod
    async def generate_request_number(session: AsyncSession, request_type: str) -> str:
        """Generate human-readable unique request number (PO-YYYY-NNNNNN or RR-YYYY-NNNNNN)."""
        prefix = "PO" if request_type == "PURCHASE_ORDER" else "RR"
        year = datetime.utcnow().year
        stmt = (
            select(func.count(ServiceRequest.id))
            .where(ServiceRequest.request_type == request_type)
            .where(ServiceRequest.request_number.like(f"{prefix}-{year}-%"))
        )
        result = await session.execute(stmt)
        count = (result.scalar() or 0) + 1
        return f"{prefix}-{year}-{count:06d}"

    @staticmethod
    async def generate_invoice_number(session: AsyncSession) -> str:
        """Generate unique invoice number (INV-YYYY-NNNNNN)."""
        year = datetime.utcnow().year
        stmt = select(func.count(Invoice.id)).where(Invoice.invoice_number.like(f"INV-{year}-%"))
        result = await session.execute(stmt)
        count = (result.scalar() or 0) + 1
        return f"INV-{year}-{count:06d}"

    # ── Funding Sources ──────────────────────────────────────────
    @staticmethod
    async def get_funding_sources(session: AsyncSession, status: str | None = None) -> list[FundingSource]:
        stmt = select(FundingSource).where(FundingSource.deleted_at.is_(None))
        if status:
            stmt = stmt.where(FundingSource.status == status)
        stmt = stmt.order_by(FundingSource.code)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_funding_source_by_id(session: AsyncSession, source_id: uuid.UUID) -> FundingSource | None:
        stmt = (
            select(FundingSource)
            .where(FundingSource.id == source_id, FundingSource.deleted_at.is_(None))
            .options(selectinload(FundingSource.budget_lines))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_funding_source(session: AsyncSession, data: dict) -> FundingSource:
        source = FundingSource(**data)
        session.add(source)
        await session.flush()
        return source

    # ── Budget Lines ─────────────────────────────────────────────
    @staticmethod
    async def get_budget_lines(
        session: AsyncSession,
        fiscal_year: str | None = None,
        is_active: bool | None = None,
    ) -> list[BudgetLine]:
        stmt = (
            select(BudgetLine).where(BudgetLine.deleted_at.is_(None)).options(selectinload(BudgetLine.funding_source))
        )
        if fiscal_year:
            stmt = stmt.where(BudgetLine.fiscal_year == fiscal_year)
        if is_active is not None:
            stmt = stmt.where(BudgetLine.is_active.is_(is_active))
        stmt = stmt.order_by(BudgetLine.code)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_budget_line_by_id(session: AsyncSession, budget_line_id: uuid.UUID) -> BudgetLine | None:
        stmt = (
            select(BudgetLine)
            .where(BudgetLine.id == budget_line_id, BudgetLine.deleted_at.is_(None))
            .options(selectinload(BudgetLine.funding_source))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_budget_line(session: AsyncSession, data: dict) -> BudgetLine:
        budget_line = BudgetLine(**data)
        session.add(budget_line)
        await session.flush()
        return budget_line

    # ── Service Requests (PO & Reimbursement) ────────────────────
    @staticmethod
    async def get_service_requests(
        session: AsyncSession,
        request_type: str | None = None,
        status: str | None = None,
        requestor_id: uuid.UUID | None = None,
        case_id: uuid.UUID | None = None,
        family_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ServiceRequest], int]:
        stmt = (
            select(ServiceRequest)
            .where(ServiceRequest.deleted_at.is_(None))
            .options(
                selectinload(ServiceRequest.items).selectinload(ServiceRequestItem.budget_line),
                selectinload(ServiceRequest.approvals),
                selectinload(ServiceRequest.requestor),
            )
        )
        if request_type:
            stmt = stmt.where(ServiceRequest.request_type == request_type)
        if status:
            stmt = stmt.where(ServiceRequest.status == status)
        if requestor_id:
            stmt = stmt.where(ServiceRequest.requestor_id == requestor_id)
        if case_id:
            stmt = stmt.where(ServiceRequest.case_id == case_id)
        if family_id:
            stmt = stmt.where(ServiceRequest.family_id == family_id)

        # Count total
        count_stmt = select(func.count(ServiceRequest.id)).where(ServiceRequest.deleted_at.is_(None))
        if request_type:
            count_stmt = count_stmt.where(ServiceRequest.request_type == request_type)
        if status:
            count_stmt = count_stmt.where(ServiceRequest.status == status)
        if requestor_id:
            count_stmt = count_stmt.where(ServiceRequest.requestor_id == requestor_id)
        if case_id:
            count_stmt = count_stmt.where(ServiceRequest.case_id == case_id)
        if family_id:
            count_stmt = count_stmt.where(ServiceRequest.family_id == family_id)

        total_res = await session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(ServiceRequest.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all()), total

    @staticmethod
    async def get_service_request_by_id(session: AsyncSession, request_id: uuid.UUID) -> ServiceRequest | None:
        stmt = (
            select(ServiceRequest)
            .where(ServiceRequest.id == request_id, ServiceRequest.deleted_at.is_(None))
            .options(
                selectinload(ServiceRequest.items).selectinload(ServiceRequestItem.budget_line),
                selectinload(ServiceRequest.approvals).selectinload(ServiceRequestApproval.approver),
                selectinload(ServiceRequest.requestor),
                selectinload(ServiceRequest.case),
                selectinload(ServiceRequest.family),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_service_request(
        session: AsyncSession,
        request_data: dict,
        items_data: list[dict],
    ) -> ServiceRequest:
        req = ServiceRequest(**request_data)
        session.add(req)
        await session.flush()

        for idx, item in enumerate(items_data):
            req_item = ServiceRequestItem(
                service_request_id=req.id,
                budget_line_id=item.get("budget_line_id"),
                funding_source_id=item.get("funding_source_id"),
                description=item["description"],
                quantity=Decimal(str(item.get("quantity", "1.00"))),
                unit_price=Decimal(str(item.get("unit_price", "0.00"))),
                line_total=Decimal(str(item.get("line_total", "0.00"))),
                sort_order=item.get("sort_order", idx),
            )
            session.add(req_item)

        await session.flush()
        return req

    # ── Billing Rates ────────────────────────────────────────────
    @staticmethod
    async def get_billing_rates(
        session: AsyncSession,
        home_type: str | None = None,
        active_only: bool = True,
    ) -> list[BillingRate]:
        stmt = select(BillingRate).where(BillingRate.deleted_at.is_(None))
        if home_type:
            stmt = stmt.where(BillingRate.home_type == home_type)
        if active_only:
            stmt = stmt.where(BillingRate.is_active.is_(True))
        stmt = stmt.order_by(BillingRate.home_type, BillingRate.age_min, BillingRate.effective_from.desc())
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_rate_for_date_and_age(
        session: AsyncSession,
        home_type: str,
        age: int,
        service_date: date,
    ) -> BillingRate | None:
        """Find the exact versioned rate matching home_type, age, and effective service date."""
        stmt = (
            select(BillingRate)
            .where(
                BillingRate.deleted_at.is_(None),
                BillingRate.is_active.is_(True),
                BillingRate.home_type == home_type,
                BillingRate.age_min <= age,
                BillingRate.age_max >= age,
                BillingRate.effective_from <= service_date,
                or_(BillingRate.effective_to.is_(None), BillingRate.effective_to >= service_date),
            )
            .order_by(BillingRate.effective_from.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_billing_rate(session: AsyncSession, data: dict) -> BillingRate:
        rate = BillingRate(**data)
        session.add(rate)
        await session.flush()
        return rate

    # ── Invoices & Ledger ────────────────────────────────────────
    @staticmethod
    async def get_invoices(
        session: AsyncSession,
        placement_home_id: uuid.UUID | None = None,
        status: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Invoice], int]:
        stmt = (
            select(Invoice)
            .where(Invoice.deleted_at.is_(None))
            .options(
                selectinload(Invoice.items),
                selectinload(Invoice.placement_home),
            )
        )
        if placement_home_id:
            stmt = stmt.where(Invoice.placement_home_id == placement_home_id)
        if status:
            stmt = stmt.where(Invoice.status == status)
        if start_date:
            stmt = stmt.where(Invoice.billing_period_start >= start_date)
        if end_date:
            stmt = stmt.where(Invoice.billing_period_end <= end_date)

        count_stmt = select(func.count(Invoice.id)).where(Invoice.deleted_at.is_(None))
        if placement_home_id:
            count_stmt = count_stmt.where(Invoice.placement_home_id == placement_home_id)
        if status:
            count_stmt = count_stmt.where(Invoice.status == status)
        if start_date:
            count_stmt = count_stmt.where(Invoice.billing_period_start >= start_date)
        if end_date:
            count_stmt = count_stmt.where(Invoice.billing_period_end <= end_date)

        total_res = await session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(Invoice.billing_period_start.desc(), Invoice.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all()), total

    @staticmethod
    async def get_invoice_by_id(session: AsyncSession, invoice_id: uuid.UUID) -> Invoice | None:
        stmt = (
            select(Invoice)
            .where(Invoice.id == invoice_id, Invoice.deleted_at.is_(None))
            .options(
                selectinload(Invoice.items).selectinload(InvoiceItem.child),
                selectinload(Invoice.items).selectinload(InvoiceItem.placement_episode),
                selectinload(Invoice.placement_home),
                selectinload(Invoice.generator),
                selectinload(Invoice.finalizer),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_overlapping_finalized_invoice(
        session: AsyncSession,
        placement_home_id: uuid.UUID,
        start_date: date,
        end_date: date,
        exclude_invoice_id: uuid.UUID | None = None,
    ) -> Invoice | None:
        """Check if an active/finalized invoice already exists for this home and overlapping period."""
        stmt = select(Invoice).where(
            Invoice.deleted_at.is_(None),
            Invoice.placement_home_id == placement_home_id,
            Invoice.status.in_(["FINALIZED", "PAID"]),
            Invoice.billing_period_start <= end_date,
            Invoice.billing_period_end >= start_date,
        )
        if exclude_invoice_id:
            stmt = stmt.where(Invoice.id != exclude_invoice_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_invoice(session: AsyncSession, invoice_data: dict, items_data: list[dict]) -> Invoice:
        invoice = Invoice(**invoice_data)
        session.add(invoice)
        await session.flush()

        for item in items_data:
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                child_id=item["child_id"],
                child_name=item["child_name"],
                placement_episode_id=item["placement_episode_id"],
                service_start_date=item["service_start_date"],
                service_end_date=item["service_end_date"],
                age_at_service=item["age_at_service"],
                rate_band_label=item.get("rate_band_label", "Standard Per Diem"),
                billable_days=item["billable_days"],
                daily_rate=Decimal(str(item["daily_rate"])),
                line_total=Decimal(str(item["line_total"])),
                is_federally_eligible=item.get("is_federally_eligible", False),
                notes=item.get("notes"),
            )
            session.add(inv_item)

        await session.flush()
        return invoice

    # ── Spending Aggregations ────────────────────────────────────
    @staticmethod
    async def get_spending_by_case(session: AsyncSession, case_id: uuid.UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00")),
            func.count(ServiceRequest.id),
        ).where(
            ServiceRequest.deleted_at.is_(None),
            ServiceRequest.case_id == case_id,
            ServiceRequest.status == "APPROVED",
        )
        res = await session.execute(stmt)
        total_spent, count = res.one()
        return {"case_id": case_id, "approved_spending": total_spent, "approved_request_count": count}

    @staticmethod
    async def get_spending_by_family(session: AsyncSession, family_id: uuid.UUID) -> dict:
        stmt = select(
            func.coalesce(func.sum(ServiceRequest.total_amount), Decimal("0.00")),
            func.count(ServiceRequest.id),
        ).where(
            ServiceRequest.deleted_at.is_(None),
            ServiceRequest.family_id == family_id,
            ServiceRequest.status == "APPROVED",
        )
        res = await session.execute(stmt)
        total_spent, count = res.one()
        return {"family_id": family_id, "approved_spending": total_spent, "approved_request_count": count}

    @staticmethod
    async def get_active_placement_episodes_for_home(
        session: AsyncSession,
        placement_home_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> list[PlacementEpisode]:
        """Fetch all placement episodes overlapping the billing period."""
        stmt = (
            select(PlacementEpisode)
            .where(
                PlacementEpisode.deleted_at.is_(None),
                PlacementEpisode.placement_home_id == placement_home_id,
                PlacementEpisode.start_date <= end_date,
                or_(PlacementEpisode.end_date.is_(None), PlacementEpisode.end_date >= start_date),
            )
            .options(selectinload(PlacementEpisode.child))
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())
