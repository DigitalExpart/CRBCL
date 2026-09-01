"""Tests for Reporting Catalogue, Canned Reports, Ad-Hoc ORM Builder & Exports (Phase 11)."""

import uuid
from datetime import date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.finance import ServiceRequest
from app.models.referral import Referral


@pytest.mark.asyncio
async def test_reporting_catalogue_and_canned_reports(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Verify reporting catalogue endpoint and canned report outputs."""
    # 1. Catalogue metadata endpoint
    res = await client.get("/api/v1/reports/catalogue", headers=caseworker_user["headers"])
    assert res.status_code == 200
    catalogue = res.json()
    assert "cases" in catalogue
    assert "case_number" in catalogue["cases"]["fields"]

    # 2. Canned report: Active Cases by Worker
    res_cw = await client.get("/api/v1/reports/canned/active-cases-worker", headers=caseworker_user["headers"])
    assert res_cw.status_code == 200
    data_cw = res_cw.json()
    assert "workers" in data_cw

    # 3. Canned report: Cases by Type and Status
    res_matrix = await client.get("/api/v1/reports/canned/cases-type-status", headers=caseworker_user["headers"])
    assert res_matrix.status_code == 200
    assert "matrix" in res_matrix.json()


@pytest.mark.asyncio
async def test_adhoc_report_builder_and_exports(
    client: AsyncClient,
    db_session: AsyncSession,
    caseworker_user: dict,
):
    """Verify safe metadata ad-hoc query execution and XLSX export."""
    # Create sample case
    case = Case(
        case_number=f"CASE-RPT-{uuid.uuid4().hex[:6]}",
        title="Reporting Audit Case",
        status="OPEN",
        case_type="PROTECTION",
    )
    db_session.add(case)
    await db_session.commit()

    # Ad-hoc query
    adhoc_payload = {
        "dataset_key": "cases",
        "fields": ["case_number", "title", "status", "case_type"],
        "limit": 50,
    }
    res = await client.post("/api/v1/reports/adhoc", json=adhoc_payload, headers=caseworker_user["headers"])
    assert res.status_code == 200
    adhoc_data = res.json()
    assert adhoc_data["dataset"] == "cases"
    assert adhoc_data["total_count"] >= 1

    # Invalid dataset key must fail gracefully (HTTP 400)
    res_bad = await client.post(
        "/api/v1/reports/adhoc", json={"dataset_key": "raw_sql_inject"}, headers=caseworker_user["headers"]
    )
    assert res_bad.status_code == 400

    # Export report to XLSX
    export_payload = {
        "dataset_key": "cases",
        "export_format": "XLSX",
        "fields": ["case_number", "title"],
    }
    res_exp = await client.post("/api/v1/reports/export", json=export_payload, headers=caseworker_user["headers"])
    assert res_exp.status_code == 200
    assert res_exp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(res_exp.content) > 0
