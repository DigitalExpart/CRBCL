"""Placement Home Billing Engine and Invoice Calculation Service (Phase 10)."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BillingRate, Invoice
from app.models.outbox import OutboxEvent
from app.repositories.finance_repo import FinanceRepository
from app.services.finance_service import quantize_money


class PlacementBillingService:
    """Service for billing rate calculations, versioning, invoice generation, and ledger auditing."""

    @staticmethod
    def calculate_child_age_on_date(dob: date | None, target_date: date) -> int:
        """Derive child's exact age on a specific service date."""
        if not dob:
            return 10  # default middle child bracket if unspecified
        age = target_date.year - dob.year - ((target_date.month, target_date.day) < (dob.month, dob.day))
        return max(0, age)

    @classmethod
    async def create_billing_rate(
        cls,
        session: AsyncSession,
        payload: dict,
        user_id: uuid.UUID,
    ) -> BillingRate:
        """Create versioned placement per-diem rate schedule with validation."""
        age_min = int(payload.get("age_min", 0))
        age_max = int(payload.get("age_max", 17))
        if age_max < age_min:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="age_max must be >= age_min")

        daily_rate = quantize_money(payload.get("daily_rate", Decimal("0.00")))
        monthly_rate = quantize_money(payload["monthly_rate"]) if payload.get("monthly_rate") else None

        rate_data = {
            "home_type": payload.get("home_type", "FOSTER_HOME"),
            "age_min": age_min,
            "age_max": age_max,
            "daily_rate": daily_rate,
            "monthly_rate": monthly_rate,
            "currency": payload.get("currency", "CAD"),
            "effective_from": payload["effective_from"],
            "effective_to": payload.get("effective_to"),
            "is_active": payload.get("is_active", True),
            "notes": payload.get("notes"),
            "created_by": user_id,
            "updated_by": user_id,
        }

        return await FinanceRepository.create_billing_rate(session, rate_data)

    @classmethod
    async def generate_draft_invoice(
        cls,
        session: AsyncSession,
        placement_home_id: uuid.UUID,
        billing_period_start: date,
        billing_period_end: date,
        user_id: uuid.UUID,
    ) -> Invoice:
        """Authoritatively compute draft monthly placement invoice based on PlacementEpisodes and Rate versions."""
        if billing_period_end < billing_period_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="billing_period_end must be >= billing_period_start",
            )

        # Duplicate billing check (ADR-025)
        existing = await FinanceRepository.get_overlapping_finalized_invoice(
            session, placement_home_id, billing_period_start, billing_period_end
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Overlapping finalized invoice {existing.invoice_number} already exists for this period",
            )

        # Find placement episodes overlapping the period
        episodes = await FinanceRepository.get_active_placement_episodes_for_home(
            session, placement_home_id, billing_period_start, billing_period_end
        )

        items_data = []
        subtotal = Decimal("0.00")

        for ep in episodes:
            eff_start = max(billing_period_start, ep.start_date)
            eff_end = min(billing_period_end, ep.end_date or billing_period_end)

            if eff_end < eff_start:
                continue

            billable_days = (eff_end - eff_start).days + 1
            if billable_days <= 0:
                continue

            child = ep.child
            child_name = f"{child.first_name} {child.last_name}" if child else "Unknown Child"
            dob = child.date_of_birth if child else None
            age_at_service = cls.calculate_child_age_on_date(dob, eff_start)

            # Versioned rate lookup (ADR-024)
            rate_obj = await FinanceRepository.get_rate_for_date_and_age(
                session, ep.placement_type or "FOSTER_HOME", age_at_service, eff_start
            )

            if rate_obj:
                daily_rate = rate_obj.daily_rate
                rate_label = f"{rate_obj.home_type} (Age {rate_obj.age_min}-{rate_obj.age_max})"
            elif ep.per_diem_rate:
                daily_rate = quantize_money(ep.per_diem_rate)
                rate_label = "Episode Agreed Per Diem"
            else:
                daily_rate = Decimal("65.00")  # Standard default per diem
                rate_label = "Standard Baseline Per Diem"

            line_total = quantize_money(Decimal(billable_days) * daily_rate)
            subtotal += line_total

            items_data.append(
                {
                    "child_id": ep.child_id,
                    "child_name": child_name,
                    "placement_episode_id": ep.id,
                    "service_start_date": eff_start,
                    "service_end_date": eff_end,
                    "age_at_service": age_at_service,
                    "rate_band_label": rate_label,
                    "billable_days": billable_days,
                    "daily_rate": daily_rate,
                    "line_total": line_total,
                    "is_federally_eligible": getattr(ep, "is_federally_eligible", False),
                    "notes": f"Placement {ep.placement_type} from {eff_start} to {eff_end}",
                }
            )

        inv_number = await FinanceRepository.generate_invoice_number(session)
        subtotal = quantize_money(subtotal)
        total_amount = subtotal  # Placement per diems typically tax-exempt under child welfare

        invoice_data = {
            "invoice_number": inv_number,
            "placement_home_id": placement_home_id,
            "billing_period_start": billing_period_start,
            "billing_period_end": billing_period_end,
            "status": "DRAFT",
            "currency": "CAD",
            "subtotal": subtotal,
            "total_amount": total_amount,
            "generated_by": user_id,
            "generated_at": datetime.utcnow(),
            "created_by": user_id,
            "updated_by": user_id,
        }

        invoice = await FinanceRepository.create_invoice(session, invoice_data, items_data)
        return await FinanceRepository.get_invoice_by_id(session, invoice.id)

    @classmethod
    async def finalize_invoice(
        cls,
        session: AsyncSession,
        invoice_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Invoice:
        """Lock and finalize invoice. Snapshots calculation and prevents subsequent mutation (ADR-025)."""
        invoice = await FinanceRepository.get_invoice_by_id(session, invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

        if invoice.status not in ["DRAFT", "REVIEWED", "GENERATED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot finalize invoice in {invoice.status} status",
            )

        # Check duplicate finalization check
        existing = await FinanceRepository.get_overlapping_finalized_invoice(
            session,
            invoice.placement_home_id,
            invoice.billing_period_start,
            invoice.billing_period_end,
            exclude_invoice_id=invoice.id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another finalized invoice ({existing.invoice_number}) exists for this period",
            )

        invoice.status = "FINALIZED"
        invoice.finalized_at = datetime.utcnow()
        invoice.finalized_by = user_id
        invoice.updated_by = user_id
        invoice.updated_at = datetime.utcnow()

        outbox_event = OutboxEvent(
            aggregate_type="INVOICE",
            aggregate_id=invoice.id,
            event_type="INVOICE_FINALIZED",
            payload={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "placement_home_id": str(invoice.placement_home_id),
                "total_amount": str(invoice.total_amount),
                "billing_period": f"{invoice.billing_period_start} to {invoice.billing_period_end}",
            },
        )
        session.add(outbox_event)
        await session.flush()
        return await FinanceRepository.get_invoice_by_id(session, invoice.id)

    @classmethod
    async def void_invoice(
        cls,
        session: AsyncSession,
        invoice_id: uuid.UUID,
        user_id: uuid.UUID,
        void_reason: str,
    ) -> Invoice:
        """Void finalized or draft invoice with mandatory reason."""
        if not void_reason or not void_reason.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Void reason is mandatory")

        invoice = await FinanceRepository.get_invoice_by_id(session, invoice_id)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")

        if invoice.status == "VOID":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invoice is already void")

        invoice.status = "VOID"
        invoice.voided_at = datetime.utcnow()
        invoice.voided_by = user_id
        invoice.void_reason = void_reason.strip()
        invoice.updated_by = user_id
        invoice.updated_at = datetime.utcnow()

        outbox_event = OutboxEvent(
            aggregate_type="INVOICE",
            aggregate_id=invoice.id,
            event_type="INVOICE_VOIDED",
            payload={
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "void_reason": void_reason.strip(),
            },
        )
        session.add(outbox_event)
        await session.flush()
        return await FinanceRepository.get_invoice_by_id(session, invoice.id)
