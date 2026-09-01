"""Test financial requests, approval workflow, segregation of duties, and audit history (ADR-023)."""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import BudgetLine, FundingSource
from app.models.user import User


@pytest.mark.asyncio
async def test_purchase_order_lifecycle_and_self_approval_protection(
    client: AsyncClient,
    db_session: AsyncSession,
    finance_user: dict,
    supervisor_user: dict,
):
    """Test PO creation, submission, self-approval blockage, and supervisor approval."""
    # 1. Create a Budget Line
    source = FundingSource(
        code=f"FS-TEST-{uuid.uuid4().hex[:6]}",
        name="Children & Youth Prevention Fund",
        funder_name="ISC",
        total_allocation=Decimal("50000.00"),
    )
    db_session.add(source)
    await db_session.flush()

    budget = BudgetLine(
        code=f"BL-TEST-{uuid.uuid4().hex[:6]}",
        name="Client Direct Support",
        funding_source_id=source.id,
        program_name="CHILD_AND_FAMILY_WELLNESS",
        fiscal_year="2026-2027",
        allocated_amount=Decimal("10000.00"),
    )
    db_session.add(budget)
    await db_session.flush()

    # 2. Finance staff creates draft PO
    po_payload = {
        "request_type": "PURCHASE_ORDER",
        "title": "School Supplies & Clothing Support",
        "description": "Essential back-to-school items for children in kinship care",
        "vendor_name": "Northern Stores / Staples",
        "currency": "CAD",
        "tax_rate": "0.05",
        "items": [
            {
                "budget_line_id": str(budget.id),
                "description": "Winter Boots and Outerwear",
                "quantity": "2.00",
                "unit_price": "150.00",
            },
            {
                "budget_line_id": str(budget.id),
                "description": "Backpacks and Learning Supplies",
                "quantity": "2.00",
                "unit_price": "75.00",
            },
        ],
    }
    create_res = await client.post(
        "/api/v1/finance/requests",
        json=po_payload,
        headers=finance_user["headers"],
    )
    assert create_res.status_code == 201, create_res.text
    po_data = create_res.json()
    req_id = po_data["id"]

    assert po_data["request_number"].startswith("PO-")
    assert po_data["status"] == "DRAFT"
    # Subtotal: 2*150 + 2*75 = 300 + 150 = 450.00. Tax: 22.50. Total: 472.50
    assert Decimal(str(po_data["subtotal"])) == Decimal("450.00")
    assert Decimal(str(po_data["tax_amount"])) == Decimal("22.50")
    assert Decimal(str(po_data["total_amount"])) == Decimal("472.50")

    # 3. Finance staff submits PO
    submit_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/submit",
        headers=finance_user["headers"],
    )
    assert submit_res.status_code == 200
    assert submit_res.json()["status"] == "PENDING_APPROVAL"

    # 4. SEGREGATION OF DUTIES: Finance staff (requester with APPROVE permission) attempts to approve own PO -> MUST BE FORBIDDEN (403)
    self_approve_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/approve",
        json={"comments": "I approve my own request"},
        headers=finance_user["headers"],
    )
    assert self_approve_res.status_code == 403
    assert "Requester cannot approve their own financial request" in (
        self_approve_res.json().get("error", {}).get("message") or self_approve_res.text
    )

    # 5. Supervisor approves PO
    sup_approve_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/approve",
        json={"comments": "Approved within team allocation limits."},
        headers=supervisor_user["headers"],
    )
    assert sup_approve_res.status_code == 200
    approved_data = sup_approve_res.json()
    assert approved_data["status"] == "APPROVED"
    assert approved_data["approved_by"] == str(supervisor_user["user"].id)
    assert len(approved_data["approvals"]) == 1
    assert approved_data["approvals"][0]["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_reimbursement_return_edit_resubmit_and_history(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
    supervisor_user: dict,
):
    """Test Reimbursement request return with reason, resubmission, and preservation of full approval history."""
    # 1. Caseworker creates Reimbursement request
    rr_payload = {
        "request_type": "REIMBURSEMENT",
        "title": "Emergency Grocery Receipt Reimbursement",
        "payee_name": "Jane Worker",
        "currency": "CAD",
        "items": [
            {
                "description": "Emergency Groceries for Family",
                "quantity": "1.00",
                "unit_price": "85.40",
            }
        ],
    }
    create_res = await client.post(
        "/api/v1/finance/requests",
        json=rr_payload,
        headers=caseworker_user["headers"],
    )
    assert create_res.status_code == 201
    req_id = create_res.json()["id"]

    # 2. Submit
    await client.post(f"/api/v1/finance/requests/{req_id}/submit", headers=caseworker_user["headers"])

    # 3. Supervisor returns request requiring attached receipt
    return_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/return",
        json={"reason": "Please attach itemized store receipt."},
        headers=supervisor_user["headers"],
    )
    assert return_res.status_code == 200
    ret_data = return_res.json()
    assert ret_data["status"] == "RETURNED"
    assert ret_data["return_reason"] == "Please attach itemized store receipt."

    # 4. Caseworker resubmits
    resubmit_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/submit",
        headers=caseworker_user["headers"],
    )
    assert resubmit_res.status_code == 200
    assert resubmit_res.json()["status"] == "PENDING_APPROVAL"

    # 5. Supervisor approves
    final_res = await client.post(
        f"/api/v1/finance/requests/{req_id}/approve",
        json={"comments": "Receipt verified on file. Approved."},
        headers=supervisor_user["headers"],
    )
    assert final_res.status_code == 200
    final_data = final_res.json()
    assert final_data["status"] == "APPROVED"

    # Full approval audit history must preserve both RETURNED and APPROVED steps (ADR-023)
    assert len(final_data["approvals"]) == 2
    assert final_data["approvals"][0]["status"] == "RETURNED"
    assert final_data["approvals"][0]["comments"] == "Please attach itemized store receipt."
    assert final_data["approvals"][1]["status"] == "APPROVED"
    assert final_data["approvals"][1]["comments"] == "Receipt verified on file. Approved."
