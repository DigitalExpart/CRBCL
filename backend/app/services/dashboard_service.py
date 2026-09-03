"""Customizable & Role-Aware User Dashboard Service for CRBCL (Phase 11)."""

import uuid
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, ClassVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case import Case
from app.models.case_management import CaseAssignment
from app.models.finance import ServiceRequest
from app.models.placement import PlacementEpisode
from app.models.referral import Referral
from app.models.reporting_qa import DashboardWidget, UserDashboardWidget
from app.permissions.constants import Permissions
from app.repositories.reporting_qa_repo import ReportingQARepository


class DashboardService:
    """Service governing server-registered widgets, drag/drop user layouts, and role-aware metric generation."""

    DEFAULT_WIDGETS: ClassVar[list[dict[str, Any]]] = [
        {
            "widget_key": "active_cases",
            "title": "Active Cases",
            "category": "OPERATIONAL",
            "required_permission": Permissions.CASE_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "children_out_of_home",
            "title": "Children Out of Home",
            "category": "OPERATIONAL",
            "required_permission": Permissions.PLACEMENT_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "new_intakes",
            "title": "New Intakes (30d)",
            "category": "OPERATIONAL",
            "required_permission": Permissions.INTAKE_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "pending_approvals",
            "title": "Pending Approvals",
            "category": "GOVERNANCE",
            "required_permission": Permissions.FINANCE_REQUEST_APPROVE,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "cases_without_recent_notes",
            "title": "Cases Without Notes (30d+)",
            "category": "QA",
            "required_permission": Permissions.QA_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "cases_over_12_months",
            "title": "Long-Term Open Cases (12m+)",
            "category": "QA",
            "required_permission": Permissions.QA_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "audits_due",
            "title": "QA Audits Due",
            "category": "QA",
            "required_permission": Permissions.QA_READ,
            "default_width": 1,
            "default_height": 1,
        },
        {
            "widget_key": "financial_summary",
            "title": "Financial Spend Summary",
            "category": "FINANCE",
            "required_permission": Permissions.FINANCE_REQUEST_READ,
            "default_width": 2,
            "default_height": 1,
        },
        {
            "widget_key": "my_assigned_cases",
            "title": "My Assigned Caseload",
            "category": "MY_WORK",
            "required_permission": Permissions.CASE_READ,
            "default_width": 2,
            "default_height": 2,
        },
    ]

    @classmethod
    async def ensure_standard_widgets(cls, session: AsyncSession) -> list[DashboardWidget]:
        """Ensure standard server widgets are seeded in database."""
        widgets = await ReportingQARepository.get_dashboard_widgets(session)
        if widgets:
            return widgets

        for w_data in cls.DEFAULT_WIDGETS:
            w_obj = DashboardWidget(**w_data)
            session.add(w_obj)

        await session.flush()
        return await ReportingQARepository.get_dashboard_widgets(session)

    @classmethod
    async def get_user_dashboard(cls, session: AsyncSession, user_id: uuid.UUID, user_permissions: set[str]) -> dict:
        """Fetch user dashboard layout and populate widget metrics based on caller permissions."""
        available_widgets = await cls.ensure_standard_widgets(session)
        user_layout = await ReportingQARepository.get_user_dashboard_layout(session, user_id)
        has_saved_layout = len(user_layout) > 0

        # Map user custom positions or fall back to default
        layout_map = {ul.widget_key: ul for ul in user_layout}

        widgets_payload = []
        for idx, w in enumerate(available_widgets):
            # Evaluate permissions: Omits widget payload if user lacks capability
            has_perm = (
                not w.required_permission
                or w.required_permission in user_permissions
                or "admin.configuration.manage" in user_permissions
                or "executive_director" in user_permissions
                or "admin" in user_permissions
            )

            user_pref = layout_map.get(w.widget_key)
            if has_saved_layout:
                is_visible = user_pref.is_visible if user_pref else False
                position = user_pref.position if user_pref else (100 + idx)
            else:
                is_visible = idx < 5
                position = idx

            width = user_pref.width if user_pref else w.default_width
            height = user_pref.height if user_pref else w.default_height

            widgets_payload.append(
                {
                    "widget_key": w.widget_key,
                    "title": w.title,
                    "category": w.category,
                    "position": position,
                    "width": width,
                    "height": height,
                    "is_visible": is_visible,
                    "has_permission": has_perm,
                }
            )

        widgets_payload.sort(key=lambda x: x["position"])

        # Fetch executive metrics
        metrics_data = await cls.fetch_dashboard_widget_data(session, user_id, user_permissions)

        return {"layout": widgets_payload, "metrics": metrics_data}

    @classmethod
    async def fetch_dashboard_widget_data(
        cls, session: AsyncSession, user_id: uuid.UUID, user_permissions: set[str]
    ) -> dict:
        """Fetch real-time metric data for authorized dashboard widgets."""
        data = {}

        # 1. Active Cases
        if Permissions.CASE_READ in user_permissions or "admin.configuration.manage" in user_permissions:
            stmt = select(func.count(Case.id)).where(Case.deleted_at.is_(None), Case.status == "OPEN")
            data["active_cases"] = (await session.execute(stmt)).scalar() or 0

        # 2. Children Out of Home
        if Permissions.PLACEMENT_READ in user_permissions or "admin.configuration.manage" in user_permissions:
            stmt = select(func.count(PlacementEpisode.id)).where(
                PlacementEpisode.deleted_at.is_(None), PlacementEpisode.status == "ACTIVE"
            )
            data["children_out_of_home"] = (await session.execute(stmt)).scalar() or 0

        # 3. New Intakes
        if Permissions.INTAKE_READ in user_permissions or "admin.configuration.manage" in user_permissions:
            thirty_days_ago = date.today() - timedelta(days=30)
            stmt = select(func.count(Referral.id)).where(
                Referral.deleted_at.is_(None), Referral.received_date >= thirty_days_ago
            )

            data["new_intakes"] = (await session.execute(stmt)).scalar() or 0

        # 4. Pending Approvals
        if Permissions.FINANCE_REQUEST_APPROVE in user_permissions or "admin.configuration.manage" in user_permissions:
            stmt = select(func.count(ServiceRequest.id)).where(
                ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "SUBMITTED"
            )
            data["pending_approvals"] = (await session.execute(stmt)).scalar() or 0

        # 5. Financial Spend Summary
        if Permissions.FINANCE_REQUEST_READ in user_permissions or "admin.configuration.manage" in user_permissions:
            stmt = select(func.sum(ServiceRequest.total_amount)).where(
                ServiceRequest.deleted_at.is_(None), ServiceRequest.status == "APPROVED"
            )
            total = (await session.execute(stmt)).scalar() or Decimal("0.00")
            data["financial_summary"] = {"approved_spend": str(total), "currency": "CAD"}

        # 6. My Assigned Cases
        if Permissions.CASE_READ in user_permissions or "admin.configuration.manage" in user_permissions:
            stmt = select(func.count(CaseAssignment.id)).where(
                CaseAssignment.user_id == user_id, CaseAssignment.is_active.is_(True)
            )
            data["my_assigned_cases_count"] = (await session.execute(stmt)).scalar() or 0

        return data

    @classmethod
    async def save_user_layout(
        cls, session: AsyncSession, user_id: uuid.UUID, layout_data: list[dict]
    ) -> list[UserDashboardWidget]:
        """Persist updated user widget preferences & layout positions."""
        return await ReportingQARepository.save_user_dashboard_layout(session, user_id, layout_data)
