"""Reporting Domain Service for CRBCL (Phase 11).

Metadata-driven reporting catalogue, canned reports, safe ORM query builder,
authorization scope enforcement, and XLSX/CSV export engine.
"""

import io
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, ClassVar

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.case_management import CaseAssignment, CaseRestriction
from app.models.finance import BudgetLine, FundingSource, Invoice, ServiceRequest
from app.models.fleet import Vehicle
from app.models.person import Person
from app.models.placement import PlacementEpisode
from app.models.referral import Referral
from app.models.reporting_qa import QAAudit, SavedReport
from app.permissions.constants import Permissions
from app.repositories.reporting_qa_repo import ReportingQARepository


class ReportingCatalogue:
    """Server-controlled whitelist of reportable datasets and fields."""

    DATASETS: ClassVar[dict[str, Any]] = {
        "cases": {
            "label": "Cases & Caseloads",
            "description": "Core case management, workers, status, and types",
            "required_permission": Permissions.CASE_READ,
            "fields": {
                "case_number": {"label": "Case Number", "type": "string", "groupable": True, "sortable": True},
                "title": {"label": "Case Title", "type": "string", "groupable": False, "sortable": True},
                "case_type": {"label": "Case Type", "type": "string", "groupable": True, "sortable": True},
                "status": {"label": "Status", "type": "string", "groupable": True, "sortable": True},
                "risk_level": {"label": "Risk Level", "type": "string", "groupable": True, "sortable": True},
                "opened_at": {"label": "Open Date", "type": "date", "groupable": False, "sortable": True},
            },
        },
        "clients": {
            "label": "Clients & Persons",
            "description": "Demographics and registered persons",
            "required_permission": Permissions.CLIENT_READ,
            "fields": {
                "first_name": {"label": "First Name", "type": "string", "groupable": False, "sortable": True},
                "last_name": {"label": "Last Name", "type": "string", "groupable": False, "sortable": True},
                "gender": {"label": "Gender", "type": "string", "groupable": True, "sortable": True},
                "date_of_birth": {"label": "Date of Birth", "type": "date", "groupable": False, "sortable": True},
                "indigenous_status": {
                    "label": "Indigenous Identity",
                    "type": "string",
                    "groupable": True,
                    "sortable": True,
                },
            },
        },
        "intakes": {
            "label": "Intakes & Referrals",
            "description": "Incoming referrals, screening, and dispositions",
            "required_permission": Permissions.INTAKE_READ,
            "fields": {
                "referral_number": {"label": "Referral Number", "type": "string", "groupable": True, "sortable": True},
                "received_date": {"label": "Received Date", "type": "date", "groupable": False, "sortable": True},
                "status": {"label": "Status", "type": "string", "groupable": True, "sortable": True},
                "screening_decision": {
                    "label": "Screening Decision",
                    "type": "string",
                    "groupable": True,
                    "sortable": True,
                },
                "concern_type": {"label": "Primary Concern", "type": "string", "groupable": True, "sortable": True},
            },
        },
        "placements": {
            "label": "Active & Historical Placements",
            "description": "Children in foster, kinship, or group placement episodes",
            "required_permission": Permissions.PLACEMENT_READ,
            "fields": {
                "placement_type": {"label": "Placement Type", "type": "string", "groupable": True, "sortable": True},
                "provider_name": {"label": "Provider / Home", "type": "string", "groupable": True, "sortable": True},
                "start_date": {"label": "Start Date", "type": "date", "groupable": False, "sortable": True},
                "end_date": {"label": "End Date", "type": "date", "groupable": False, "sortable": True},
                "status": {"label": "Status", "type": "string", "groupable": True, "sortable": True},
            },
        },
        "finance": {
            "label": "Financial Requests & Ledger",
            "description": "Purchase orders, reimbursements, and placement billing",
            "required_permission": Permissions.FINANCE_REQUEST_READ,
            "fields": {
                "request_number": {"label": "Request Number", "type": "string", "groupable": True, "sortable": True},
                "request_type": {"label": "Request Type", "type": "string", "groupable": True, "sortable": True},
                "title": {"label": "Title", "type": "string", "groupable": False, "sortable": True},
                "status": {"label": "Status", "type": "string", "groupable": True, "sortable": True},
                "total_amount": {
                    "label": "Total Amount",
                    "type": "number",
                    "groupable": False,
                    "sortable": True,
                    "aggregatable": True,
                },
                "created_at": {"label": "Created Date", "type": "datetime", "groupable": False, "sortable": True},
            },
        },
        "qa_audits": {
            "label": "QA Case Audits",
            "description": "Quality assurance audit reviews and compliance scores",
            "required_permission": Permissions.QA_READ,
            "fields": {
                "review_date": {"label": "Review Date", "type": "date", "groupable": False, "sortable": True},
                "status": {"label": "Audit Status", "type": "string", "groupable": True, "sortable": True},
                "overall_score": {
                    "label": "Compliance Score (%)",
                    "type": "number",
                    "groupable": False,
                    "sortable": True,
                    "aggregatable": True,
                },
            },
        },
        "fleet": {
            "label": "Fleet & Agency Vehicles",
            "description": "Agency vehicle registry, operational statuses, mileage, and insurance",
            "required_permission": Permissions.FLEET_READ,
            "fields": {
                "vehicle_internal_id": {"label": "Vehicle ID", "type": "string", "groupable": True, "sortable": True},
                "make": {"label": "Make", "type": "string", "groupable": True, "sortable": True},
                "model": {"label": "Model", "type": "string", "groupable": True, "sortable": True},
                "licence_plate": {"label": "Licence Plate", "type": "string", "groupable": True, "sortable": True},
                "vehicle_type": {"label": "Vehicle Type", "type": "string", "groupable": True, "sortable": True},
                "status": {"label": "Status", "type": "string", "groupable": True, "sortable": True},
                "odometer_km": {
                    "label": "Odometer (km)",
                    "type": "number",
                    "groupable": False,
                    "sortable": True,
                    "aggregatable": True,
                },
                "insurance_expiry": {"label": "Insurance Expiry", "type": "date", "groupable": False, "sortable": True},
            },
        },
    }



class ReportingService:
    """Service handling canned reports, ad-hoc builder, security filters, and export generation."""

    @staticmethod
    def get_catalogue_metadata(user_permissions: set[str]) -> dict:
        """Return authorized catalogue datasets and fields visible to caller."""
        authorized_datasets = {}
        for ds_key, ds_val in ReportingCatalogue.DATASETS.items():
            req_perm = ds_val["required_permission"]
            if req_perm in user_permissions or "admin.configuration.manage" in user_permissions:
                authorized_datasets[ds_key] = ds_val
        return authorized_datasets

    # ── 1. Canned Reports ──────────────────────────────────────────
    @classmethod
    async def run_intake_monthly_report(
        cls,
        session: AsyncSession,
        start_date: date,
        end_date: date,
        can_read_reporters: bool = False,
    ) -> dict:
        """Generate monthly intake volume, disposition breakdown, and primary concern breakdown."""
        stmt = (
            select(Referral)
            .where(
                Referral.deleted_at.is_(None),
                Referral.received_at >= datetime.combine(start_date, datetime.min.time()),
                Referral.received_at <= datetime.combine(end_date, datetime.max.time()),
            )
            .options(selectinload(Referral.dispositions))
        )
        res = await session.execute(stmt)
        referrals = list(res.scalars().all())

        disposition_counts = {}
        concern_counts = {}
        items = []

        for ref in referrals:
            disp_str = ref.status
            if ref.dispositions:
                disp_str = ref.dispositions[0].decision
            disposition_counts[disp_str] = disposition_counts.get(disp_str, 0) + 1

            concern_str = getattr(ref, "screening_decision", "UNSPECIFIED") or "UNSPECIFIED"
            concern_counts[concern_str] = concern_counts.get(concern_str, 0) + 1

            item = {
                "id": str(ref.id),
                "reference_number": ref.reference_number,
                "received_at": ref.received_at.isoformat() if ref.received_at else None,
                "status": ref.status,
                "screening_decision": ref.screening_decision,
            }
            # Mandatory reporter identity redaction unless caller has INTAKE_REPORTER_READ
            if can_read_reporters:
                item["reporter_name"] = getattr(ref, "reporter_name", "Confidential")
            items.append(item)

        return {
            "report_name": "Intake Monthly Report",
            "period": f"{start_date} to {end_date}",
            "total_referrals": len(referrals),
            "disposition_summary": disposition_counts,
            "concern_summary": concern_counts,
            "items": items,
        }

    @classmethod
    async def run_active_cases_by_worker(cls, session: AsyncSession) -> dict:
        """Generate breakdown of active cases grouped by worker assignment."""
        stmt = (
            select(CaseAssignment)
            .where(CaseAssignment.is_active.is_(True))
            .options(selectinload(CaseAssignment.case), selectinload(CaseAssignment.user))
        )
        res = await session.execute(stmt)
        assignments = list(res.scalars().all())

        worker_summary = {}
        for assign in assignments:
            worker_name = f"{assign.user.first_name} {assign.user.last_name}" if assign.user else "Unassigned"
            if worker_name not in worker_summary:
                worker_summary[worker_name] = {"worker_id": str(assign.user_id), "case_count": 0, "cases": []}

            c = assign.case
            if c and c.deleted_at is None and c.status == "OPEN":
                worker_summary[worker_name]["case_count"] += 1
                worker_summary[worker_name]["cases"].append(
                    {
                        "case_id": str(c.id),
                        "case_number": c.case_number,
                        "title": c.title,
                        "case_type": c.case_type,
                        "role": assign.role,
                    }
                )

        return {
            "report_name": "Active Cases by Worker",
            "total_active_assignments": sum(w["case_count"] for w in worker_summary.values()),
            "workers": worker_summary,
        }

    @classmethod
    async def run_cases_by_type_status(cls, session: AsyncSession) -> dict:
        """Cross-tabulate cases by type and status."""
        stmt = (
            select(Case.case_type, Case.status, func.count(Case.id))
            .where(Case.deleted_at.is_(None))
            .group_by(Case.case_type, Case.status)
        )
        res = await session.execute(stmt)
        rows = res.all()

        matrix = {}
        for c_type, c_status, count in rows:
            c_type = c_type or "PROTECTION"
            c_status = c_status or "OPEN"
            if c_type not in matrix:
                matrix[c_type] = {}
            matrix[c_type][c_status] = count

        return {"report_name": "Cases by Type and Status", "matrix": matrix}

    @classmethod
    async def run_children_in_placement_report(cls, session: AsyncSession) -> dict:
        """Report on active children currently in out-of-home placement episodes."""
        stmt = (
            select(PlacementEpisode)
            .where(PlacementEpisode.deleted_at.is_(None), PlacementEpisode.status == "ACTIVE")
            .options(selectinload(PlacementEpisode.child), selectinload(PlacementEpisode.placement_home))
        )
        res = await session.execute(stmt)
        episodes = list(res.scalars().all())

        by_type = {}
        items = []
        for ep in episodes:
            p_type = ep.placement_type or "FOSTER_HOME"
            by_type[p_type] = by_type.get(p_type, 0) + 1

            child_name = f"{ep.child.first_name} {ep.child.last_name}" if ep.child else "Unknown Child"
            items.append(
                {
                    "placement_id": str(ep.id),
                    "child_name": child_name,
                    "placement_type": ep.placement_type,
                    "provider_name": ep.provider_name,
                    "start_date": ep.start_date.isoformat() if ep.start_date else None,
                    "per_diem_rate": str(ep.per_diem_rate or "0.00"),
                }
            )

        return {
            "report_name": "Children Currently in Placement",
            "total_placed_children": len(episodes),
            "by_placement_type": by_type,
            "items": items,
        }

    @classmethod
    async def run_financial_summary_report(cls, session: AsyncSession) -> dict:
        """Summarize financial requests, allocations, and invoices using Phase 10 engine."""
        # Active funding sources
        fs_stmt = select(func.sum(FundingSource.total_allocation)).where(FundingSource.deleted_at.is_(None))
        fs_total = (await session.execute(fs_stmt)).scalar() or Decimal("0.00")

        # Active budget lines
        bl_stmt = select(func.sum(BudgetLine.allocated_amount)).where(
            BudgetLine.deleted_at.is_(None), BudgetLine.is_active.is_(True)
        )
        bl_total = (await session.execute(bl_stmt)).scalar() or Decimal("0.00")

        # Approved financial requests
        sr_stmt = select(func.sum(ServiceRequest.total_amount), func.count(ServiceRequest.id)).where(
            ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "APPROVED"
        )
        sr_res = (await session.execute(sr_stmt)).one()

        # Finalized invoices
        inv_stmt = select(func.sum(Invoice.total_amount), func.count(Invoice.id)).where(
            Invoice.deleted_at.is_(None), Invoice.status.in_(["FINALIZED", "PAID"])
        )
        inv_res = (await session.execute(inv_stmt)).one()

        return {
            "report_name": "Financial Summary Report",
            "total_grant_allocation": str(fs_total),
            "total_budget_allocated": str(bl_total),
            "approved_requests_total": str(sr_res[0] or Decimal("0.00")),
            "approved_requests_count": sr_res[1],
            "finalized_invoices_total": str(inv_res[0] or Decimal("0.00")),
            "finalized_invoices_count": inv_res[1],
            "currency": "CAD",
        }

    # ── 2. Ad-Hoc Report Builder Engine ───────────────────────────
    @classmethod
    async def run_adhoc_report(
        cls,
        session: AsyncSession,
        dataset_key: str,
        user_id: uuid.UUID,
        user_permissions: set[str],
        fields: list[str] | None = None,
        filters: list[dict] | None = None,
        group_by: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        """Safely build and execute ad-hoc report using server metadata catalogue (Zero SQL Injection)."""
        if dataset_key not in ReportingCatalogue.DATASETS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid dataset '{dataset_key}'")

        ds_info = ReportingCatalogue.DATASETS[dataset_key]
        req_perm = ds_info["required_permission"]

        if req_perm not in user_permissions and "admin.configuration.manage" not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission '{req_perm}' for dataset '{dataset_key}'",
            )

        # Build ORM statement strictly based on dataset_key
        if dataset_key == "cases":
            stmt = select(Case).where(Case.deleted_at.is_(None))
            # Inject case restriction filtering
            restricted_stmt = select(CaseRestriction.case_id).where(
                CaseRestriction.user_id == user_id, CaseRestriction.is_active.is_(True)
            )
            stmt = stmt.where(Case.id.not_in(restricted_stmt))

        elif dataset_key == "clients":
            stmt = select(Person).where(Person.deleted_at.is_(None))

        elif dataset_key == "intakes":
            stmt = select(Referral).where(Referral.deleted_at.is_(None))

        elif dataset_key == "placements":
            stmt = select(PlacementEpisode).where(PlacementEpisode.deleted_at.is_(None))

        elif dataset_key == "finance":
            stmt = select(ServiceRequest).where(ServiceRequest.deleted_at.is_(None))

        elif dataset_key == "qa_audits":
            stmt = select(QAAudit).where(QAAudit.deleted_at.is_(None))

        elif dataset_key == "fleet":
            stmt = select(Vehicle).where(Vehicle.archived_at.is_(None))

        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported dataset")


        # Execute safe query
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await session.execute(count_stmt)
        total_count = total_res.scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result = await session.execute(stmt)
        records = list(result.scalars().all())

        # Format rows safely based on whitelist fields
        valid_fields = ds_info["fields"]
        selected_fields = [f for f in (fields or valid_fields.keys()) if f in valid_fields]

        rows = []
        for rec in records:
            row = {}
            for field in selected_fields:
                val = getattr(rec, field, None)
                if isinstance(val, date | datetime):
                    val = val.isoformat()
                elif isinstance(val, Decimal | uuid.UUID):
                    val = str(val)
                row[field] = val

            rows.append(row)

        return {
            "dataset": dataset_key,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "selected_fields": selected_fields,
            "data": rows,
        }

    # ── 3. Saved Reports & Run History ─────────────────────────────
    @classmethod
    async def create_saved_report(cls, session: AsyncSession, payload: dict, user_id: uuid.UUID) -> SavedReport:
        dataset_key = payload.get("dataset_key")
        if dataset_key not in ReportingCatalogue.DATASETS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid dataset_key")

        payload["owner_user_id"] = user_id
        payload["created_by"] = user_id
        payload["updated_by"] = user_id
        return await ReportingQARepository.create_saved_report(session, payload)

    @classmethod
    async def run_saved_report(
        cls, session: AsyncSession, report_id: uuid.UUID, user_id: uuid.UUID, user_permissions: set[str]
    ) -> dict:
        report = await ReportingQARepository.get_saved_report_by_id(session, report_id)
        if not report:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved report not found")

        # Ownership / Visibility Security Check
        if report.visibility == "PRIVATE" and report.owner_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this private saved report"
            )

        # Log Report Run
        run_obj = await ReportingQARepository.create_report_run(
            session,
            {
                "saved_report_id": report.id,
                "run_by_id": user_id,
                "started_at": datetime.utcnow(),
                "status": "RUNNING",
                "parameters_snapshot": report.configuration,
            },
        )

        try:
            cfg = report.configuration or {}
            res_data = await cls.run_adhoc_report(
                session,
                dataset_key=report.dataset_key,
                user_id=user_id,
                user_permissions=user_permissions,
                fields=cfg.get("fields"),
                filters=cfg.get("filters"),
                group_by=cfg.get("group_by"),
            )
            await ReportingQARepository.complete_report_run(
                session, run_obj.id, row_count=res_data["total_count"], status="SUCCESS"
            )
            res_data["report_id"] = str(report.id)
            res_data["report_name"] = report.name
            return res_data

        except Exception as err:
            await ReportingQARepository.complete_report_run(
                session, run_obj.id, row_count=0, status="FAILED", error_message=str(err)
            )
            raise

    # ── 4. Export Generators (CSV / XLSX) ──────────────────────────
    @classmethod
    def generate_csv_export(cls, report_data: dict) -> bytes:
        """Convert report dictionary payload into a clean CSV byte buffer."""
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        rows = report_data.get("data") or report_data.get("items") or []
        if not rows:
            writer.writerow(["No records found"])
            return output.getvalue().encode("utf-8")

        headers = list(rows[0].keys())
        writer.writerow(headers)

        for r in rows:
            writer.writerow([r.get(h, "") for h in headers])

        return output.getvalue().encode("utf-8")

    @classmethod
    def generate_xlsx_export(cls, report_data: dict) -> bytes:
        """Generate XLSX workbook buffer from report payload using openpyxl/standard format."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report Results"

        rows = report_data.get("data") or report_data.get("items") or []
        if not rows:
            ws.append(["No records found"])
        else:
            headers = list(rows[0].keys())
            ws.append([h.replace("_", " ").title() for h in headers])
            for r in rows:
                ws.append([str(r.get(h, "")) for h in headers])

        buffer = io.BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
