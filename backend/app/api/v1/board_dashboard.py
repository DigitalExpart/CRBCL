"""Board of Governors Dashboard API Endpoints.

Provides strictly redacted, governance-safe aggregations and action tracking for Board members.
Zero operational child-welfare, client, clinical, or staff personal data is accessible.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.auth.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.board_dashboard import (
    BoardActionItem,
    BoardCriticalDateItem,
    BoardDepartmentUpdateItem,
    BoardFinanceResponse,
    BoardInitiativeItem,
    BoardPerformanceResponse,
    BoardPublishDepartmentUpdateRequest,
    BoardPublishInitiativeRequest,
    BoardRecordDecisionRequest,
    BoardRiskResponse,
    BoardSummaryResponse,
    BoardWorkforceResponse,
)
from app.services.board_dashboard_service import BoardDashboardService

router = APIRouter(prefix="/board", tags=["Board Dashboard"])


@router.get(
    "/summary",
    response_model=BoardSummaryResponse,
    summary="Get Board of Governors Governance Overview Summary",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_summary(
    request: Request,
    reporting_period: str | None = Query(None, description="Optional reporting period e.g. 2026-04"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve top-level governance overview metrics with zero confidential details."""
    service = BoardDashboardService(db)
    summary = await service.get_board_summary(reporting_period=reporting_period)

    # Log governance access
    audit = AuditService(db)
    await audit.log_event(
        action="BOARD_DASHBOARD_VIEW",
        resource_type="board_dashboard",
        resource_id=current_user.id,
        user_id=current_user.id,
        details={"reporting_period": reporting_period},
    )
    await db.commit()

    return summary


@router.get(
    "/actions",
    response_model=list[BoardActionItem],
    summary="Get Governance-Ready Board Actions & Decisions",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_actions(
    status_filter: str | None = Query(None, alias="status", description="Filter by status e.g. SUBMITTED, RESOLVED"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve governance-ready Board Actions and decision resolutions."""
    service = BoardDashboardService(db)
    return await service.get_board_actions(status_filter=status_filter)


@router.get(
    "/initiatives",
    response_model=list[BoardInitiativeItem],
    summary="Get Board-Published Strategic Initiatives",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_initiatives(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve strategic initiatives approved for Board oversight."""
    service = BoardDashboardService(db)
    return await service.get_board_initiatives()


@router.get(
    "/department-updates",
    response_model=list[BoardDepartmentUpdateItem],
    summary="Get Board-Published Department Executive Reports",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_department_updates(
    reporting_period: str | None = Query(None, description="Filter by reporting period e.g. 2026-04"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve periodic department executive updates approved for Board visibility."""
    service = BoardDashboardService(db)
    return await service.get_board_department_updates(reporting_period=reporting_period)


@router.get(
    "/workforce",
    response_model=BoardWorkforceResponse,
    summary="Get High-Level Workforce Summary",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_workforce(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve aggregate workforce statistics with zero personal details."""
    service = BoardDashboardService(db)
    return await service.get_board_workforce()


@router.get(
    "/finance",
    response_model=BoardFinanceResponse,
    summary="Get Approved Organizational Finance Overview",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_finance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve approved aggregate organizational finances with strict Decimal precision."""
    service = BoardDashboardService(db)
    return await service.get_board_finance()


@router.get(
    "/performance",
    response_model=BoardPerformanceResponse,
    summary="Get Organizational Performance Outcomes",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_performance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve aggregate service delivery and operational outcome indicators."""
    service = BoardDashboardService(db)
    return await service.get_board_performance()


@router.get(
    "/risk-compliance",
    response_model=BoardRiskResponse,
    summary="Get Organizational Risk & Compliance Overview",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_risk_compliance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve high-level organizational compliance exceptions and serious incident counts."""
    service = BoardDashboardService(db)
    return await service.get_board_risk_compliance()


@router.get(
    "/critical-dates",
    response_model=list[BoardCriticalDateItem],
    summary="Get Critical Governance Deadlines",
    dependencies=[Depends(require_permission(Permissions.BOARD_DASHBOARD_READ))],
)
async def get_board_critical_dates(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Retrieve governance deadlines (board actions, initiative milestones)."""
    service = BoardDashboardService(db)
    return await service.get_board_critical_dates()


# ── Decision Recording (Restricted) ──────────────────────────────
@router.post(
    "/actions/{action_id}/decision",
    response_model=BoardActionItem,
    summary="Record Formal Board Action Decision",
    dependencies=[Depends(require_permission(Permissions.BOARD_DECISION_RECORD))],
)
async def record_board_decision(
    action_id: uuid.UUID,
    req: BoardRecordDecisionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Record formal Board decision on a BoardAction with immutable audit history."""
    service = BoardDashboardService(db)
    action = await service.record_board_decision(
        action_id=action_id,
        decision=req.decision,
        status=req.status,
        resolution_notes=req.resolution_notes,
        user_id=current_user.id,
    )
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board action not found")

    actions = await service.get_board_actions()
    matching = next((a for a in actions if a.id == action.id), None)
    if not matching:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board action not found after update")
    return matching


# ── Executive Publication Controls (Restricted to Leadership) ──
@router.post(
    "/initiatives/{initiative_id}/publish",
    response_model=dict[str, Any],
    summary="Publish or Unpublish Strategic Initiative to Board",
    dependencies=[Depends(require_permission(Permissions.BOARD_PUBLICATION_MANAGE))],
)
async def publish_initiative_to_board(
    initiative_id: uuid.UUID,
    req: BoardPublishInitiativeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Publish or unpublish a strategic initiative to the Board with executive approval."""
    service = BoardDashboardService(db)
    updated = await service.publish_initiative(
        initiative_id=initiative_id,
        is_visible=req.is_board_visible,
        board_summary=req.board_summary,
        user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Initiative not found")
    return {
        "status": "success",
        "id": str(updated.id),
        "is_board_visible": updated.is_board_visible,
        "approved_for_board_at": updated.approved_for_board_at,
    }


@router.post(
    "/department-updates/{update_id}/publish",
    response_model=dict[str, Any],
    summary="Publish or Unpublish Department Update to Board",
    dependencies=[Depends(require_permission(Permissions.BOARD_PUBLICATION_MANAGE))],
)
async def publish_department_update_to_board(
    update_id: uuid.UUID,
    req: BoardPublishDepartmentUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Publish or unpublish a department executive update to the Board."""
    service = BoardDashboardService(db)
    updated = await service.publish_department_update(
        update_id=update_id,
        is_visible=req.is_board_visible,
        user_id=current_user.id,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department update not found")
    return {
        "status": "success",
        "id": str(updated.id),
        "is_board_visible": updated.is_board_visible,
        "approved_for_board_at": updated.approved_for_board_at,
    }


@router.post(
    "/actions/{action_id}/governance-ready",
    response_model=dict[str, Any],
    summary="Set Governance Readiness for Board Action",
    dependencies=[Depends(require_permission(Permissions.BOARD_PUBLICATION_MANAGE))],
)
async def set_board_action_governance_ready(
    action_id: uuid.UUID,
    is_governance_ready: bool = Query(..., description="Governance readiness flag"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Deliberately mark a Board Action governance-ready or return to draft/internal. Executive only."""
    service = BoardDashboardService(db)
    action = await service.set_action_governance_ready(
        action_id=action_id,
        is_governance_ready=is_governance_ready,
        user_id=current_user.id,
    )
    if not action:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board action not found")
    return {
        "status": "success",
        "id": str(action.id),
        "reference_number": action.reference_number,
        "is_governance_ready": action.is_governance_ready,
    }
