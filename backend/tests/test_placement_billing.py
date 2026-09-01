"""Test placement billing engine, versioned rates, snapshots, immutability, and void lifecycle (ADR-024, ADR-025)."""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.finance import BillingRate
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome


@pytest.mark.asyncio
async def test_placement_billing_rate_versioning_and_invoice_immutability(
    client: AsyncClient,
    db_session: AsyncSession,
    finance_user: dict,
):
    """Test placement billing with temporal rate versioning and finalized invoice immutability."""
    # 1. Setup Placement Home, Person, Case, and Placement Episode
    home = PlacementHome(
        home_code=f"HOME-{uuid.uuid4().hex[:6]}",
        name="Red Bear Healing Lodge Foster Home",
        home_type="FOSTER_HOME",
        status="ACTIVE",
        licensing_status="ACTIVE",
        address_line_1="100 Treaty Road",
        city="Regina",
        province="Saskatchewan",
        postal_code="S4P 3Y2",
        primary_caregiver_name="Elder Mary",
        phone="306-555-0101",
        total_capacity=4,
    )
    db_session.add(home)

    child = Person(
        first_name="Little",
        last_name="Wolf",
        date_of_birth=date(2018, 5, 10),  # Age ~8
        gender="MALE",
    )
    db_session.add(child)
    await db_session.flush()

    case = Case(
        case_number=f"CASE-FIN-{uuid.uuid4().hex[:6]}",
        title="Wolf Family Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.flush()

    # Episode active from Jan 10, 2026 to open-ended
    ep = PlacementEpisode(
        case_id=case.id,
        child_id=child.id,
        placement_home_id=home.id,
        placement_type="FOSTER_HOME",
        provider_name=home.name,
        start_date=date(2026, 1, 10),
        status="ACTIVE",
        per_diem_rate=Decimal("65.00"),
    )
    db_session.add(ep)
    await db_session.flush()

    # 2. Setup Versioned Rates:
    # Rate v1: Jan 1 to Mar 31, 2026 -> $70.00/day
    # Rate v2: Apr 1, 2026 onwards -> $85.00/day
    rate_v1 = BillingRate(
        home_type="FOSTER_HOME",
        age_min=0,
        age_max=17,
        daily_rate=Decimal("70.00"),
        effective_from=date(2026, 1, 1),
        effective_to=date(2026, 3, 31),
        is_active=True,
    )
    rate_v2 = BillingRate(
        home_type="FOSTER_HOME",
        age_min=0,
        age_max=17,
        daily_rate=Decimal("85.00"),
        effective_from=date(2026, 4, 1),
        effective_to=None,
        is_active=True,
    )
    db_session.add_all([rate_v1, rate_v2])
    await db_session.flush()

    # 3. Generate Draft Invoice for January 2026 (Jan 1 - Jan 31)
    # Child placed Jan 10 -> billable days = (31 - 10) + 1 = 22 days.
    # Rate effective in Jan: Rate v1 ($70.00/day).
    # Expected amount = 22 * 70.00 = 1,540.00
    jan_inv_payload = {
        "placement_home_id": str(home.id),
        "billing_period_start": "2026-01-01",
        "billing_period_end": "2026-01-31",
    }
    gen_res = await client.post(
        "/api/v1/finance/invoices/generate",
        json=jan_inv_payload,
        headers=finance_user["headers"],
    )
    assert gen_res.status_code == 201, gen_res.text
    jan_inv = gen_res.json()
    jan_inv_id = jan_inv["id"]

    assert jan_inv["status"] == "DRAFT"
    assert len(jan_inv["items"]) == 1
    item = jan_inv["items"][0]
    assert item["billable_days"] == 22
    assert Decimal(str(item["daily_rate"])) == Decimal("70.00")
    assert Decimal(str(item["line_total"])) == Decimal("1540.00")
    assert Decimal(str(jan_inv["total_amount"])) == Decimal("1540.00")

    # 4. Finalize January Invoice (ADR-025 Immutability Lock)
    finalize_res = await client.post(
        f"/api/v1/finance/invoices/{jan_inv_id}/finalize",
        headers=finance_user["headers"],
    )
    assert finalize_res.status_code == 200
    assert finalize_res.json()["status"] == "FINALIZED"

    # 5. IMMUTABILITY CHECK: Update Rate v1 daily_rate to $999.00 in database
    rate_v1.daily_rate = Decimal("999.00")
    await db_session.flush()

    # Retrieve January finalized invoice -> MUST STILL BE $1540.00 with $70.00 snapshot
    get_res = await client.get(
        f"/api/v1/finance/invoices/{jan_inv_id}",
        headers=finance_user["headers"],
    )
    assert get_res.status_code == 200
    fetched_inv = get_res.json()
    assert Decimal(str(fetched_inv["total_amount"])) == Decimal("1540.00")
    assert Decimal(str(fetched_inv["items"][0]["daily_rate"])) == Decimal("70.00")

    # 6. DUPLICATE INVOICE CHECK: Attempt generating duplicate invoice for overlapping Jan period -> MUST FAIL
    dup_res = await client.post(
        "/api/v1/finance/invoices/generate",
        json=jan_inv_payload,
        headers=finance_user["headers"],
    )
    assert dup_res.status_code == 400
    assert "already exists" in (dup_res.json().get("error", {}).get("message") or dup_res.text)

    # 7. Generate April 2026 Invoice (Apr 1 - Apr 30)
    # Child placed entire month (30 days). Rate effective in Apr: Rate v2 ($85.00/day).
    # Expected amount = 30 * 85.00 = 2,550.00
    apr_inv_payload = {
        "placement_home_id": str(home.id),
        "billing_period_start": "2026-04-01",
        "billing_period_end": "2026-04-30",
    }
    apr_res = await client.post(
        "/api/v1/finance/invoices/generate",
        json=apr_inv_payload,
        headers=finance_user["headers"],
    )
    assert apr_res.status_code == 201
    apr_inv = apr_res.json()
    assert apr_inv["items"][0]["billable_days"] == 30
    assert Decimal(str(apr_inv["items"][0]["daily_rate"])) == Decimal("85.00")
    assert Decimal(str(apr_inv["total_amount"])) == Decimal("2550.00")

    # 8. Void Invoice Workflow (Mandatory reason required)
    void_res = await client.post(
        f"/api/v1/finance/invoices/{apr_inv['id']}/void",
        json={"void_reason": "Administrative correction required before reissue"},
        headers=finance_user["headers"],
    )
    assert void_res.status_code == 200
    void_inv = void_res.json()
    assert void_inv["status"] == "VOID"
    assert void_inv["void_reason"] == "Administrative correction required before reissue"
