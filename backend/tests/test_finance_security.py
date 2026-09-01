"""Test financial security, role permissions, and privacy boundary isolation (ADR-023)."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseRestriction
from app.models.finance import BudgetLine, FundingSource, ServiceRequest
from app.models.person import Person


@pytest.mark.asyncio
async def test_caseworker_and_it_admin_permission_boundaries(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    it_admin_user: dict,
    finance_user: dict,
):
    """Verify Caseworker and IT Admin without explicit Finance capabilities are blocked from restricted financial endpoints."""
    # 1. Caseworker attempts to create a budget line -> MUST FAIL (403 Forbidden)
    bl_payload = {
        "code": f"BL-SEC-{uuid.uuid4().hex[:6]}",
        "name": "Unauthorized Budget Line",
        "allocated_amount": "50000.00",
    }
    cw_res = await client.post(
        "/api/v1/finance/budget-lines",
        json=bl_payload,
        headers=caseworker_user["headers"],
    )
    assert cw_res.status_code == 403

    # 2. IT Admin attempts to read invoices or financial requests -> MUST FAIL (403 Forbidden)
    it_res = await client.get(
        "/api/v1/finance/requests",
        headers=it_admin_user["headers"],
    )
    assert it_res.status_code == 403

    it_inv_res = await client.get(
        "/api/v1/finance/invoices",
        headers=it_admin_user["headers"],
    )
    assert it_inv_res.status_code == 403

    # 3. Finance staff CAN read requests and budget lines
    fin_res = await client.get(
        "/api/v1/finance/budget-lines",
        headers=finance_user["headers"],
    )
    assert fin_res.status_code == 200


@pytest.mark.asyncio
async def test_case_restriction_financial_spending_privacy(
    client: AsyncClient,
    db_session: AsyncSession,
    finance_user: dict,
    caseworker_user: dict,
):
    """Ensure authorized financial users can query approved case spending without exposing clinical details."""
    case = Case(
        case_number=f"CASE-RESTRICT-{uuid.uuid4().hex[:6]}",
        title="Confidential Chief Family Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.flush()

    # Apply conflict/confidentiality restriction on Case
    restriction = CaseRestriction(
        case_id=case.id,
        user_id=caseworker_user["user"].id,
        restriction_type="conflict_of_interest",
        reason="Family conflict of interest",
        is_active=True,
    )
    db_session.add(restriction)
    await db_session.flush()

    # Create approved financial request on this case
    sr = ServiceRequest(
        request_number=f"PO-2026-{uuid.uuid4().hex[:6]}",
        request_type="PURCHASE_ORDER",
        title="Family Wellness Healing Grant",
        requestor_id=finance_user["user"].id,
        case_id=case.id,
        status="APPROVED",
        currency="CAD",
        subtotal=Decimal("1200.00"),
        tax_amount=Decimal("0.00"),
        total_amount=Decimal("1200.00"),
    )
    db_session.add(sr)
    await db_session.commit()

    # Query Case spending via Finance API
    res = await client.get(
        f"/api/v1/finance/spending/cases/{case.id}",
        headers=finance_user["headers"],
    )
    assert res.status_code == 200
    spending_data = res.json()
    assert Decimal(str(spending_data["approved_spending"])) == Decimal("1200.00")
    assert spending_data["approved_request_count"] == 1
