"""Reporting & Quality Assurance Repository for CRBCL (Phase 11)."""

import uuid
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.reporting_qa import (
    DashboardWidget,
    QAAudit,
    QAAuditResult,
    QAAuditTemplate,
    QAAuditTemplateItem,
    QAAuditTemplateVersion,
    ReportRun,
    SavedReport,
    UserDashboardWidget,
)


class ReportingQARepository:
    """Data access layer for Saved Reports, QA Audits, Checklists & Dashboards."""

    # ── Saved Reports ─────────────────────────────────────────────
    @staticmethod
    async def get_saved_reports(
        session: AsyncSession,
        user_id: uuid.UUID,
        team_id: uuid.UUID | None = None,
    ) -> list[SavedReport]:
        """Fetch saved reports visible to user (owned, shared with team, or authorized shared)."""
        visibility_conditions = [
            SavedReport.owner_user_id == user_id,
            SavedReport.visibility == "AUTHORIZED_SHARED",
        ]
        if team_id:
            visibility_conditions.append(
                (SavedReport.team_id == team_id) & (SavedReport.visibility.in_(["TEAM", "AUTHORIZED_SHARED"]))
            )

        stmt = (
            select(SavedReport)
            .where(SavedReport.deleted_at.is_(None))
            .where(or_(*visibility_conditions))
            .options(selectinload(SavedReport.owner), selectinload(SavedReport.team))
            .order_by(SavedReport.created_at.desc())
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_saved_report_by_id(session: AsyncSession, report_id: uuid.UUID) -> SavedReport | None:
        stmt = (
            select(SavedReport)
            .where(SavedReport.id == report_id, SavedReport.deleted_at.is_(None))
            .options(selectinload(SavedReport.owner), selectinload(SavedReport.team))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_saved_report(session: AsyncSession, data: dict) -> SavedReport:
        report = SavedReport(**data)
        session.add(report)
        await session.flush()
        return report

    @staticmethod
    async def update_saved_report(session: AsyncSession, report: SavedReport, data: dict) -> SavedReport:
        for k, v in data.items():
            if hasattr(report, k) and v is not None:
                setattr(report, k, v)
        report.updated_at = datetime.utcnow()
        await session.flush()
        return report

    @staticmethod
    async def delete_saved_report(session: AsyncSession, report: SavedReport, user_id: uuid.UUID) -> None:
        report.is_deleted = True
        report.deleted_at = datetime.utcnow()
        report.deleted_by = user_id
        await session.flush()

    # ── Report Runs Log ───────────────────────────────────────────
    @staticmethod
    async def create_report_run(session: AsyncSession, data: dict) -> ReportRun:
        run_obj = ReportRun(**data)
        session.add(run_obj)
        await session.flush()
        return run_obj

    @staticmethod
    async def complete_report_run(
        session: AsyncSession,
        run_id: uuid.UUID,
        row_count: int,
        status: str = "SUCCESS",
        error_message: str | None = None,
    ) -> ReportRun | None:
        stmt = select(ReportRun).where(ReportRun.id == run_id)
        res = await session.execute(stmt)
        run_obj = res.scalar_one_or_none()
        if run_obj:
            run_obj.completed_at = datetime.utcnow()
            run_obj.status = status
            run_obj.row_count = row_count
            run_obj.error_message = error_message
            await session.flush()
        return run_obj

    @staticmethod
    async def get_report_runs(
        session: AsyncSession,
        user_id: uuid.UUID | None = None,
        limit: int = 50,
    ) -> list[ReportRun]:
        stmt = select(ReportRun).options(selectinload(ReportRun.saved_report), selectinload(ReportRun.runner))
        if user_id:
            stmt = stmt.where(ReportRun.run_by_id == user_id)
        stmt = stmt.order_by(ReportRun.started_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    # ── QA Audit Templates & Checklist Versions ────────────────────
    @staticmethod
    async def get_qa_audit_templates(session: AsyncSession, active_only: bool = True) -> list[QAAuditTemplate]:
        stmt = select(QAAuditTemplate).where(QAAuditTemplate.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(QAAuditTemplate.is_active.is_(True))
        stmt = stmt.options(selectinload(QAAuditTemplate.versions).selectinload(QAAuditTemplateVersion.items)).order_by(
            QAAuditTemplate.title
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_qa_audit_template_by_id(session: AsyncSession, template_id: uuid.UUID) -> QAAuditTemplate | None:
        stmt = (
            select(QAAuditTemplate)
            .where(QAAuditTemplate.id == template_id, QAAuditTemplate.deleted_at.is_(None))
            .options(selectinload(QAAuditTemplate.versions).selectinload(QAAuditTemplateVersion.items))
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_qa_audit_template(
        session: AsyncSession, template_data: dict, items_data: list[dict], user_id: uuid.UUID
    ) -> QAAuditTemplate:
        template = QAAuditTemplate(**template_data)
        session.add(template)
        await session.flush()

        version_obj = QAAuditTemplateVersion(
            template_id=template.id,
            version_number=1,
            is_current=True,
            published_by=user_id,
            change_notes="Initial version release",
        )
        session.add(version_obj)
        await session.flush()

        for idx, item in enumerate(items_data):
            t_item = QAAuditTemplateItem(
                version_id=version_obj.id,
                section=item.get("section", "General Documentation"),
                item_text=item["item_text"],
                guidance_notes=item.get("guidance_notes"),
                severity=item.get("severity", "MEDIUM"),
                sort_order=item.get("sort_order", idx),
                is_required=item.get("is_required", True),
            )
            session.add(t_item)

        await session.flush()
        return await ReportingQARepository.get_qa_audit_template_by_id(session, template.id)

    # ── QA Audits & Checklists ────────────────────────────────────
    @staticmethod
    async def get_qa_audits(
        session: AsyncSession,
        case_id: uuid.UUID | None = None,
        reviewer_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[QAAudit], int]:
        stmt = (
            select(QAAudit)
            .where(QAAudit.deleted_at.is_(None))
            .options(
                selectinload(QAAudit.case),
                selectinload(QAAudit.reviewer),
                selectinload(QAAudit.template_version).selectinload(QAAuditTemplateVersion.items),
                selectinload(QAAudit.results).selectinload(QAAuditResult.item),
            )
        )
        if case_id:
            stmt = stmt.where(QAAudit.case_id == case_id)
        if reviewer_id:
            stmt = stmt.where(QAAudit.reviewer_id == reviewer_id)
        if status:
            stmt = stmt.where(QAAudit.status == status)

        count_stmt = select(func.count(QAAudit.id)).where(QAAudit.deleted_at.is_(None))
        if case_id:
            count_stmt = count_stmt.where(QAAudit.case_id == case_id)
        if reviewer_id:
            count_stmt = count_stmt.where(QAAudit.reviewer_id == reviewer_id)
        if status:
            count_stmt = count_stmt.where(QAAudit.status == status)

        total_res = await session.execute(count_stmt)
        total = total_res.scalar() or 0

        stmt = stmt.order_by(QAAudit.review_date.desc(), QAAudit.created_at.desc()).limit(limit).offset(offset)
        res = await session.execute(stmt)
        return list(res.scalars().all()), total

    @staticmethod
    async def get_qa_audit_by_id(session: AsyncSession, audit_id: uuid.UUID) -> QAAudit | None:
        stmt = (
            select(QAAudit)
            .where(QAAudit.id == audit_id, QAAudit.deleted_at.is_(None))
            .options(
                selectinload(QAAudit.case),
                selectinload(QAAudit.reviewer),
                selectinload(QAAudit.template_version).selectinload(QAAuditTemplateVersion.items),
                selectinload(QAAudit.results).selectinload(QAAuditResult.item),
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_qa_audit(session: AsyncSession, audit_data: dict, results_data: list[dict]) -> QAAudit:
        audit = QAAudit(**audit_data)
        session.add(audit)
        await session.flush()

        for res in results_data:
            a_res = QAAuditResult(
                audit_id=audit.id,
                item_id=res["item_id"],
                compliance=res.get("compliance", "YES"),
                notes=res.get("notes"),
                finding_severity=res.get("finding_severity"),
                followup_required=res.get("followup_required", False),
            )
            session.add(a_res)

        await session.flush()
        return await ReportingQARepository.get_qa_audit_by_id(session, audit.id)

    # ── Dashboard Widgets & Preferences ─────────────────────────
    @staticmethod
    async def get_dashboard_widgets(session: AsyncSession) -> list[DashboardWidget]:
        stmt = select(DashboardWidget).where(DashboardWidget.is_active.is_(True)).order_by(DashboardWidget.title)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_user_dashboard_layout(session: AsyncSession, user_id: uuid.UUID) -> list[UserDashboardWidget]:
        stmt = (
            select(UserDashboardWidget)
            .where(UserDashboardWidget.user_id == user_id)
            .order_by(UserDashboardWidget.position)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def save_user_dashboard_layout(
        session: AsyncSession, user_id: uuid.UUID, widgets_data: list[dict]
    ) -> list[UserDashboardWidget]:
        # Delete existing user layout & replace atomically
        delete_stmt = select(UserDashboardWidget).where(UserDashboardWidget.user_id == user_id)
        res = await session.execute(delete_stmt)
        for existing in res.scalars().all():
            await session.delete(existing)
        await session.flush()

        new_widgets = []
        for idx, w in enumerate(widgets_data):
            uw = UserDashboardWidget(
                user_id=user_id,
                widget_key=w["widget_key"],
                position=w.get("position", idx),
                width=w.get("width", 1),
                height=w.get("height", 1),
                is_visible=w.get("is_visible", True),
                settings=w.get("settings", {}),
            )
            session.add(uw)
            new_widgets.append(uw)

        await session.flush()
        return new_widgets
