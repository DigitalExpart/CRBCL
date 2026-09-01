"""Quality Assurance Audit, Audit Tickler & QA Dashboard Service for CRBCL (Phase 11)."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import ClassVar

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseAssignment
from app.models.case_note import CaseNote
from app.models.finance import ServiceRequest
from app.models.placement import PlacementEpisode
from app.models.reporting_qa import QAAudit, QAAuditResult, QAAuditTemplate
from app.repositories.reporting_qa_repo import ReportingQARepository


class QAAuditService:
    """Service governing QA templates, versioning, case audit reviews, and audit tickler calculations."""

    CADENCE_DAYS: ClassVar[dict[str, int]] = {
        "MONTHLY": 30,
        "QUARTERLY": 90,
        "SEMI_ANNUAL": 180,
        "ANNUAL": 365,
    }

    # ── 1. Seed & Template Governance ─────────────────────────────
    @classmethod
    async def ensure_default_template(cls, session: AsyncSession, user_id: uuid.UUID) -> QAAuditTemplate:
        """Seed initial standard QA Audit Template if none exists."""
        stmt = select(QAAuditTemplate).where(QAAuditTemplate.code == "QA-STD-CP")
        res = await session.execute(stmt)
        template = res.scalar_one_or_none()
        if template:
            return template

        template_data = {
            "code": "QA-STD-CP",
            "title": "Standard Child Protection Case Audit",
            "description": "Quarterly compliance review checklist for active Child Protection cases.",
            "cadence": "QUARTERLY",
            "target_case_type": "PROTECTION",
            "is_active": True,
        }
        items_data = [
            {
                "section": "Documentation & Notes",
                "item_text": "Case notes are completed and locked within 48 hours of contact?",
                "severity": "HIGH",
                "sort_order": 1,
            },
            {
                "section": "Assessments & Plans",
                "item_text": "Current Safety Plan / Case Plan is active and signed?",
                "severity": "CRITICAL",
                "sort_order": 2,
            },
            {
                "section": "Placements & Visitation",
                "item_text": "Required monthly child and caregiver visitation contacts logged?",
                "severity": "HIGH",
                "sort_order": 3,
            },
            {
                "section": "Background Checks",
                "item_text": "All adult household members have current background checks?",
                "severity": "CRITICAL",
                "sort_order": 4,
            },
        ]
        return await ReportingQARepository.create_qa_audit_template(session, template_data, items_data, user_id)

    # ── 2. Audit Lifecycle & Score Calculation ────────────────────
    @classmethod
    async def create_audit(cls, session: AsyncSession, payload: dict, reviewer_id: uuid.UUID) -> QAAudit:
        """Create a new case QA audit review."""
        results_data = payload.pop("results", [])

        # Calculate initial overall compliance score
        score = cls.calculate_compliance_score(results_data)

        payload["reviewer_id"] = reviewer_id
        payload["created_by"] = reviewer_id
        payload["updated_by"] = reviewer_id
        payload["overall_score"] = score

        if payload.get("status") == "COMPLETED":
            payload["completed_at"] = datetime.utcnow()

        return await ReportingQARepository.create_qa_audit(session, payload, results_data)

    @classmethod
    async def update_audit(
        cls, session: AsyncSession, audit_id: uuid.UUID, payload: dict, user_id: uuid.UUID
    ) -> QAAudit:
        """Update existing QA audit. Completed audits cannot be modified directly."""
        audit = await ReportingQARepository.get_qa_audit_by_id(session, audit_id)
        if not audit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")

        if audit.status == "COMPLETED" and payload.get("status") != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Completed QA audits are immutable and cannot be un-completed.",
            )

        results_data = payload.pop("results", None)
        if results_data is not None:
            # Update individual result answers
            for r_item in results_data:
                res_stmt = select(QAAuditResult).where(
                    QAAuditResult.audit_id == audit_id, QAAuditResult.item_id == r_item["item_id"]
                )
                res_obj = (await session.execute(res_stmt)).scalar_one_or_none()
                if res_obj:
                    res_obj.compliance = r_item.get("compliance", res_obj.compliance)
                    res_obj.notes = r_item.get("notes", res_obj.notes)
                    res_obj.finding_severity = r_item.get("finding_severity", res_obj.finding_severity)

            # Recalculate score
            all_res_stmt = select(QAAuditResult).where(QAAuditResult.audit_id == audit_id)
            all_res = list((await session.execute(all_res_stmt)).scalars().all())
            audit.overall_score = cls.calculate_compliance_score([{"compliance": r.compliance} for r in all_res])

        for k, v in payload.items():
            if hasattr(audit, k) and v is not None:
                setattr(audit, k, v)

        if payload.get("status") == "COMPLETED" and not audit.completed_at:
            audit.completed_at = datetime.utcnow()

        audit.updated_at = datetime.utcnow()
        audit.updated_by = user_id
        await session.flush()
        return audit

    @staticmethod
    def calculate_compliance_score(results_data: list[dict]) -> Decimal:
        """Compute compliance percentage: YES / (YES + NO) * 100."""
        applicable = [r for r in results_data if r.get("compliance") in ["YES", "NO"]]
        if not applicable:
            return Decimal("100.00")
        yes_count = sum(1 for r in applicable if r.get("compliance") == "YES")
        score = (Decimal(yes_count) / Decimal(len(applicable))) * Decimal("100.00")
        return round(score, 2)

    # ── 3. Audit Tickler Engine ────────────────────────────────────
    @classmethod
    async def get_audit_tickler_status(cls, session: AsyncSession) -> dict:
        """Calculate audit tickler due dates and categories across all open cases."""
        stmt = select(Case).where(Case.deleted_at.is_(None), Case.status == "OPEN")
        res = await session.execute(stmt)
        cases = list(res.scalars().all())

        today = date.today()
        ok_cases = []
        due_soon_cases = []
        overdue_cases = []

        for c in cases:
            cadence = "QUARTERLY"
            cadence_days = cls.CADENCE_DAYS[cadence]

            # Find latest completed audit for case
            audit_stmt = (
                select(QAAudit)
                .where(QAAudit.case_id == c.id, QAAudit.status == "COMPLETED", QAAudit.deleted_at.is_(None))
                .order_by(QAAudit.review_date.desc())
            )
            audit_res = await session.execute(audit_stmt)
            latest_audit = audit_res.scalars().first()

            if not latest_audit:
                # Never audited
                due_date = c.created_at.date() + timedelta(days=cadence_days) if c.created_at else today

                overdue_cases.append(
                    {
                        "case_id": str(c.id),
                        "case_number": c.case_number,
                        "title": c.title,
                        "last_audit_date": None,
                        "next_due_date": due_date.isoformat(),
                        "tickler_status": "OVERDUE",
                        "days_overdue": (today - due_date).days if today > due_date else 0,
                    }
                )
            else:
                last_date = latest_audit.review_date
                next_due = last_date + timedelta(days=cadence_days)
                days_until_due = (next_due - today).days

                item_payload = {
                    "case_id": str(c.id),
                    "case_number": c.case_number,
                    "title": c.title,
                    "last_audit_date": last_date.isoformat(),
                    "next_due_date": next_due.isoformat(),
                    "score": str(latest_audit.overall_score) if latest_audit.overall_score else None,
                }

                if days_until_due < 0:
                    item_payload["tickler_status"] = "OVERDUE"
                    item_payload["days_overdue"] = abs(days_until_due)
                    overdue_cases.append(item_payload)
                elif days_until_due <= 14:
                    item_payload["tickler_status"] = "DUE_SOON"
                    item_payload["days_until_due"] = days_until_due
                    due_soon_cases.append(item_payload)
                else:
                    item_payload["tickler_status"] = "OK"
                    ok_cases.append(item_payload)

        return {
            "summary": {
                "ok_count": len(ok_cases),
                "due_soon_count": len(due_soon_cases),
                "overdue_count": len(overdue_cases),
                "total_open_cases": len(cases),
            },
            "due_soon": due_soon_cases,
            "overdue": overdue_cases,
            "ok": ok_cases,
        }

    # ── 4. QA Dashboard Metrics Aggregation ────────────────────────
    @classmethod
    async def get_qa_dashboard_metrics(cls, session: AsyncSession) -> dict:
        """Aggregate Quality Assurance metrics and operational alerts."""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        one_year_ago = datetime.utcnow() - timedelta(days=365)

        # 1. Audit tickler summary
        tickler_data = await cls.get_audit_tickler_status(session)

        # 2. Cases without completed note in 30+ days
        open_cases_stmt = select(Case.id, Case.case_number, Case.title).where(
            Case.deleted_at.is_(None), Case.status == "OPEN"
        )
        open_cases = list((await session.execute(open_cases_stmt)).all())

        cases_without_notes = []
        for cid, cnum, ctitle in open_cases:
            note_stmt = select(func.max(CaseNote.created_at)).where(
                CaseNote.case_id == cid, CaseNote.deleted_at.is_(None), CaseNote.status.in_(["COMPLETED", "LOCKED"])
            )
            latest_note = (await session.execute(note_stmt)).scalar()
            if not latest_note or latest_note < thirty_days_ago:
                cases_without_notes.append({"case_id": str(cid), "case_number": cnum, "title": ctitle})

        # 3. Cases open > 12 months
        long_cases_stmt = select(Case.id, Case.case_number, Case.title, Case.created_at).where(
            Case.deleted_at.is_(None), Case.status == "OPEN", Case.created_at <= one_year_ago
        )

        long_cases = list((await session.execute(long_cases_stmt)).all())

        # 4. Children currently in out-of-home placement
        pl_stmt = select(func.count(PlacementEpisode.id)).where(
            PlacementEpisode.deleted_at.is_(None), PlacementEpisode.status == "ACTIVE"
        )
        out_of_home_count = (await session.execute(pl_stmt)).scalar() or 0

        # 5. Average caseload per worker
        assign_stmt = select(func.count(CaseAssignment.id)).where(CaseAssignment.is_active.is_(True))
        active_assignments = (await session.execute(assign_stmt)).scalar() or 0

        workers_stmt = select(func.count(func.distinct(CaseAssignment.user_id))).where(
            CaseAssignment.is_active.is_(True)
        )
        active_workers = (await session.execute(workers_stmt)).scalar() or 1
        avg_caseload = round(active_assignments / active_workers, 1)

        # 6. Pending approvals (Intakes + Financial Requests)
        pending_requests_stmt = select(func.count(ServiceRequest.id)).where(
            ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "SUBMITTED"
        )
        pending_fin_requests = (await session.execute(pending_requests_stmt)).scalar() or 0

        return {
            "tickler": tickler_data["summary"],
            "cases_without_notes_count": len(cases_without_notes),
            "cases_without_notes": cases_without_notes,
            "cases_over_12_months_count": len(long_cases),
            "children_out_of_home_count": out_of_home_count,
            "average_caseload_per_worker": avg_caseload,
            "pending_approvals_count": pending_fin_requests,
        }
