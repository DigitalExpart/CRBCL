"""Test Decimal money precision, rounding, and authoritative server calculation (ADR-022)."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BudgetLine, FundingSource, ServiceRequest
from app.services.finance_service import FinanceService, quantize_money


@pytest.mark.asyncio
async def test_decimal_precision_no_float_artifacts(db_session: AsyncSession):
    """Verify 0.10 + 0.20 == 0.30 in Python Decimal and database storage without float artifacts."""
    val1 = Decimal("0.10")
    val2 = Decimal("0.20")
    expected = Decimal("0.30")

    # In binary float: 0.1 + 0.2 != 0.3 (0.30000000000000004)
    assert val1 + val2 == expected

    # Create FundingSource with precise Decimal allocation
    source = FundingSource(
        code=f"FS-DECIMAL-{uuid.uuid4().hex[:6]}",
        name="Precision Test Grant",
        funder_name="Indigenous Services Canada",
        total_allocation=expected,
    )
    db_session.add(source)
    await db_session.flush()
    await db_session.refresh(source)

    assert source.total_allocation == expected
    assert isinstance(source.total_allocation, Decimal)


@pytest.mark.asyncio
async def test_authoritative_server_line_totals_and_tamper_rejection():
    """Verify backend calculates line totals and grand totals authoritatively, overriding client tampering."""
    items = [
        {
            "description": "Emergency Food Hamper",
            "quantity": "3.00",
            "unit_price": "125.50",
            "line_total": "1.00",
        },  # Tampered
        {
            "description": "Winter Clothing Allowance",
            "quantity": "2.00",
            "unit_price": "250.25",
            "line_total": "9999.00",
        },  # Tampered
    ]

    # Calculate authoritative server totals with 5% tax
    computed_items, subtotal, tax_amount, total_amount = FinanceService.calculate_request_totals(
        items, tax_rate=Decimal("0.05")
    )

    # Line 1: 3 * 125.50 = 376.50
    # Line 2: 2 * 250.25 = 500.50
    # Subtotal: 877.00
    # Tax 5%: 43.85
    # Total: 920.85
    assert computed_items[0]["line_total"] == Decimal("376.50")
    assert computed_items[1]["line_total"] == Decimal("500.50")
    assert subtotal == Decimal("877.00")
    assert tax_amount == Decimal("43.85")
    assert total_amount == Decimal("920.85")
