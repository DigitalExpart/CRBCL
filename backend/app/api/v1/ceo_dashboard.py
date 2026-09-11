"""API Router for CRBCL CEO Dashboard, Strategic Initiatives, Board Actions, and Department Updates."""

from __future__ import annotations

import uuid
from datetime import UTC, date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.board_action import BoardAction, BoardActionHistory
from app.models.department_update import DepartmentExecutiveUpdate
from app.models.executive_initiative import (
    ExecutiveInitiative,
    ExecutiveInitiativeHistory,
)
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.schemas.ceo_dashboard import (
    BoardActionCreate,
    BoardActionDecisionRequest,
    BoardActionHistoryResponse,
    BoardActionResponse,
    BoardActionUpdate,
    CeoDashboardFullResponse,
    DepartmentExecutiveUpdateCreate,
    DepartmentExecutiveUpdateResponse,
    ExecutiveInitiativeCreate,
    ExecutiveInitiativeHistoryResponse,
    ExecutiveInitiativeResponse,
    ExecutiveInitiativeUpdate,
)
from app.services.ceo_dashboard_service import CeoDashboardService


def _history_sort_key(x: Any) -> tuple[float, str]:
    dt = getattr(x, "changed_at", None)
    if dt is None:
        ts = 0.0
    elif dt.tzinfo is not None:
        ts = dt.timestamp()
    else:
        ts = dt.replace(tzinfo=UTC).timestamp()
    return (ts, str(getattr(x, "id", "")))

router = APIRouter(prefix="/ceo-dashboard", tags=["CEO Dashboard"])


async def _assert_department_scope(
    db: AsyncSession,
    current_user: User,
    claimed_department: str | None,
) -> None:
    """Enforce that write operations are scoped to the user's own department.

    Users holding EXECUTIVE_DASHBOARD_READ (CEO / Executive Director) may act
    on any department.  All other users must match the department they claim in
    the request body to the department recorded on their own User account.  If
    `current_user.department` is None the account is not department-scoped and
    the request is allowed through (e.g. system/admin accounts).

    Raises HTTPException 403 if the scope check fails.
    """
    if claimed_department is None:
        return
    # CEO / ExecDir bypass — they hold the top-level executive read permission
    perm_service = PermissionService(db)
    if await perm_service.user_has_permission(current_user.id, Permissions.EXECUTIVE_DASHBOARD_READ):
        return
    # Non-executive: enforce own-department scope
    if current_user.department is None:
        # No department set on account — allow through (admin/system user)
        return
    if current_user.department != claimed_department:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"You may only manage records for your own department "
                f"({current_user.department!r}), not {claimed_department!r}."
            ),
        )


# ── Full Dashboard ────────────────────────────────────────────────────────────


@router.get(
    "",
    response_model=CeoDashboardFullResponse,
    summary="Get full CEO Organization-Wide Dashboard",
)
async def get_ceo_dashboard(
    reporting_period: str | None = Query(None, description="e.g. 2026-04 or 2026-Q1"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.EXECUTIVE_DASHBOARD_READ)),
) -> CeoDashboardFullResponse:
    """Retrieve live organization-wide executive command centre metrics."""
    return await CeoDashboardService.get_full_dashboard(db, reporting_period=reporting_period)


# ── Strategic Initiatives ─────────────────────────────────────────────────────


@router.get(
    "/initiatives",
    response_model=list[ExecutiveInitiativeResponse],
    summary="List strategic organizational initiatives",
)
async def list_initiatives(
    department: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.EXECUTIVE_INITIATIVE_READ)),
) -> list[ExecutiveInitiativeResponse]:
    query = (
        select(ExecutiveInitiative)
        .where(ExecutiveInitiative.deleted_at.is_(None))
        .options(
            selectinload(ExecutiveInitiative.responsible_owner),
            selectinload(ExecutiveInitiative.history).selectinload(ExecutiveInitiativeHistory.changed_by),
        )
        .order_by(ExecutiveInitiative.priority.desc(), ExecutiveInitiative.target_date.asc())
    )
    if department:
        query = query.where(ExecutiveInitiative.department == department)
    if status_filter:
        query = query.where(ExecutiveInitiative.status == status_filter)

    res = await db.execute(query)
    initiatives = res.scalars().all()
    today = date.today()

    return [
        ExecutiveInitiativeResponse(
            id=init.id,
            title=init.title,
            description=init.description,
            department=init.department,
            responsible_owner_id=init.responsible_owner_id,
            responsible_owner_name=(
                init.responsible_owner.full_name
                if init.responsible_owner
                else None
            ),
            status=init.status,
            priority=init.priority,
            target_date=init.target_date,
            start_date=init.start_date,
            completion_date=init.completion_date,
            progress_percentage=init.progress_percentage,
            latest_update=init.latest_update,
            reporting_notes=init.reporting_notes,
            is_overdue=bool(
                init.target_date
                and init.target_date < today
                and init.status not in ["COMPLETED", "CANCELLED"]
            ),
            created_at=init.created_at,
            updated_at=init.updated_at,
            history=[
                ExecutiveInitiativeHistoryResponse(
                    id=h.id,
                    initiative_id=h.initiative_id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    progress_percentage=h.progress_percentage,
                    update_note=h.update_note,
                    changed_by_name=(
                        h.changed_by.full_name
                        if h.changed_by
                        else None
                    ),
                    changed_at=h.changed_at,
                )
                for h in sorted(init.history, key=_history_sort_key, reverse=True)
            ],
        )
        for init in initiatives
    ]


@router.post(
    "/initiatives",
    response_model=ExecutiveInitiativeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new strategic initiative",
)
async def create_initiative(
    data: ExecutiveInitiativeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.EXECUTIVE_INITIATIVE_WRITE)),
) -> ExecutiveInitiativeResponse:
    await _assert_department_scope(db, current_user, data.department)
    init = await CeoDashboardService.create_initiative(db, data, current_user.id)
    # Reload with relations
    stmt = (
        select(ExecutiveInitiative)
        .where(ExecutiveInitiative.id == init.id)
        .options(
            selectinload(ExecutiveInitiative.responsible_owner),
            selectinload(ExecutiveInitiative.history).selectinload(ExecutiveInitiativeHistory.changed_by),
        )
    )
    res = await db.execute(stmt)
    full_init = res.scalar_one()

    return ExecutiveInitiativeResponse(
        id=full_init.id,
        title=full_init.title,
        description=full_init.description,
        department=full_init.department,
        responsible_owner_id=full_init.responsible_owner_id,
        responsible_owner_name=(
            full_init.responsible_owner.full_name
            if full_init.responsible_owner
            else None
        ),
        status=full_init.status,
        priority=full_init.priority,
        target_date=full_init.target_date,
        start_date=full_init.start_date,
        completion_date=full_init.completion_date,
        progress_percentage=full_init.progress_percentage,
        latest_update=full_init.latest_update,
        reporting_notes=full_init.reporting_notes,
        is_overdue=False,
        created_at=full_init.created_at,
        updated_at=full_init.updated_at,
        history=[
            ExecutiveInitiativeHistoryResponse(
                id=h.id,
                initiative_id=h.initiative_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                progress_percentage=h.progress_percentage,
                update_note=h.update_note,
                changed_by_name=(
                    h.changed_by.full_name
                    if h.changed_by
                    else None
                ),
                changed_at=h.changed_at,
            )
            for h in sorted(full_init.history, key=_history_sort_key, reverse=True)
        ],
    )


@router.patch(
    "/initiatives/{initiative_id}",
    response_model=ExecutiveInitiativeResponse,
    summary="Update a strategic initiative and preserve history",
)
async def update_initiative(
    initiative_id: uuid.UUID,
    data: ExecutiveInitiativeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.EXECUTIVE_INITIATIVE_WRITE)),
) -> ExecutiveInitiativeResponse:
    await _assert_department_scope(db, current_user, data.department)
    try:
        init = await CeoDashboardService.update_initiative(db, initiative_id, data, current_user.id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err

    stmt = (
        select(ExecutiveInitiative)
        .where(ExecutiveInitiative.id == init.id)
        .options(
            selectinload(ExecutiveInitiative.responsible_owner),
            selectinload(ExecutiveInitiative.history).selectinload(ExecutiveInitiativeHistory.changed_by),
        )
    )
    res = await db.execute(stmt)
    full_init = res.scalar_one()

    today = date.today()
    return ExecutiveInitiativeResponse(
        id=full_init.id,
        title=full_init.title,
        description=full_init.description,
        department=full_init.department,
        responsible_owner_id=full_init.responsible_owner_id,
        responsible_owner_name=(
            full_init.responsible_owner.full_name
            if full_init.responsible_owner
            else None
        ),
        status=full_init.status,
        priority=full_init.priority,
        target_date=full_init.target_date,
        start_date=full_init.start_date,
        completion_date=full_init.completion_date,
        progress_percentage=full_init.progress_percentage,
        latest_update=full_init.latest_update,
        reporting_notes=full_init.reporting_notes,
        is_overdue=bool(
            full_init.target_date
            and full_init.target_date < today
            and full_init.status not in ["COMPLETED", "CANCELLED"]
        ),
        created_at=full_init.created_at,
        updated_at=full_init.updated_at,
        history=[
            ExecutiveInitiativeHistoryResponse(
                id=h.id,
                initiative_id=h.initiative_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                progress_percentage=h.progress_percentage,
                update_note=h.update_note,
                changed_by_name=(
                    h.changed_by.full_name
                    if h.changed_by
                    else None
                ),
                changed_at=h.changed_at,
            )
            for h in sorted(full_init.history, key=_history_sort_key, reverse=True)
        ],
    )


# ── Board Actions ─────────────────────────────────────────────────────────────


@router.get(
    "/board-actions",
    response_model=list[BoardActionResponse],
    summary="List Board actions and governance requests",
)
async def list_board_actions(
    department: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.BOARD_ACTION_READ)),
) -> list[BoardActionResponse]:
    query = (
        select(BoardAction)
        .where(BoardAction.deleted_at.is_(None))
        .options(
            selectinload(BoardAction.submitted_by),
            selectinload(BoardAction.decided_by),
            selectinload(BoardAction.linked_initiative),
            selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
        )
        .order_by(BoardAction.required_by_date.asc().nullslast(), BoardAction.created_at.desc())
    )
    if department:
        query = query.where(BoardAction.originating_department == department)
    if status_filter:
        query = query.where(BoardAction.status == status_filter)

    res = await db.execute(query)
    actions = res.scalars().all()

    return [
        BoardActionResponse(
            id=ba.id,
            reference_number=ba.reference_number,
            originating_department=ba.originating_department,
            linked_initiative_id=ba.linked_initiative_id,
            linked_initiative_title=(
                ba.linked_initiative.title if ba.linked_initiative else None
            ),
            title=ba.title,
            background_summary=ba.background_summary,
            requested_action=ba.requested_action,
            priority=ba.priority,
            required_by_date=ba.required_by_date,
            status=ba.status,
            submitted_by_id=ba.submitted_by_id,
            submitted_by_name=(
                ba.submitted_by.full_name
                if ba.submitted_by
                else None
            ),
            submitted_date=ba.submitted_date,
            decision=ba.decision,
            decision_date=ba.decision_date,
            decided_by_name=(
                ba.decided_by.full_name
                if ba.decided_by
                else None
            ),
            is_governance_ready=ba.is_governance_ready,
            created_at=ba.created_at,
            updated_at=ba.updated_at,
            history=[
                BoardActionHistoryResponse(
                    id=h.id,
                    board_action_id=h.board_action_id,
                    previous_status=h.previous_status,
                    new_status=h.new_status,
                    decision_notes=h.decision_notes,
                    action_notes=h.action_notes,
                    changed_by_name=(
                        h.changed_by.full_name
                        if h.changed_by
                        else None
                    ),
                    changed_at=h.changed_at,
                )
                for h in sorted(ba.history, key=_history_sort_key, reverse=True)
            ],
        )
        for ba in actions
    ]


@router.post(
    "/board-actions",
    response_model=BoardActionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new governance action or decision request for Board attention",
)
async def create_board_action(
    data: BoardActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.BOARD_ACTION_WRITE)),
) -> BoardActionResponse:
    await _assert_department_scope(db, current_user, data.originating_department)
    ba = await CeoDashboardService.create_board_action(db, data, current_user.id)
    stmt = (
        select(BoardAction)
        .where(BoardAction.id == ba.id)
        .options(
            selectinload(BoardAction.submitted_by),
            selectinload(BoardAction.decided_by),
            selectinload(BoardAction.linked_initiative),
            selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
        )
    )
    res = await db.execute(stmt)
    full_ba = res.scalar_one()

    return BoardActionResponse(
        id=full_ba.id,
        reference_number=full_ba.reference_number,
        originating_department=full_ba.originating_department,
        linked_initiative_id=full_ba.linked_initiative_id,
        linked_initiative_title=(
            full_ba.linked_initiative.title if full_ba.linked_initiative else None
        ),
        title=full_ba.title,
        background_summary=full_ba.background_summary,
        requested_action=full_ba.requested_action,
        priority=full_ba.priority,
        required_by_date=full_ba.required_by_date,
        status=full_ba.status,
        submitted_by_id=full_ba.submitted_by_id,
        submitted_by_name=(
            full_ba.submitted_by.full_name
            if full_ba.submitted_by
            else None
        ),
        submitted_date=full_ba.submitted_date,
        decision=full_ba.decision,
        decision_date=full_ba.decision_date,
        decided_by_name=None,
        is_governance_ready=full_ba.is_governance_ready,
        created_at=full_ba.created_at,
        updated_at=full_ba.updated_at,
        history=[
            BoardActionHistoryResponse(
                id=h.id,
                board_action_id=h.board_action_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                decision_notes=h.decision_notes,
                action_notes=h.action_notes,
                changed_by_name=(
                    h.changed_by.full_name
                    if h.changed_by
                    else None
                ),
                changed_at=h.changed_at,
            )
            for h in sorted(full_ba.history, key=_history_sort_key, reverse=True)
        ],
    )


@router.patch(
    "/board-actions/{action_id}",
    response_model=BoardActionResponse,
    summary="Update a Board action request",
)
async def update_board_action(
    action_id: uuid.UUID,
    data: BoardActionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.BOARD_ACTION_WRITE)),
) -> BoardActionResponse:
    try:
        ba = await CeoDashboardService.update_board_action(db, action_id, data, current_user.id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err

    stmt = (
        select(BoardAction)
        .where(BoardAction.id == ba.id)
        .options(
            selectinload(BoardAction.submitted_by),
            selectinload(BoardAction.decided_by),
            selectinload(BoardAction.linked_initiative),
            selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
        )
    )
    res = await db.execute(stmt)
    full_ba = res.scalar_one()

    return BoardActionResponse(
        id=full_ba.id,
        reference_number=full_ba.reference_number,
        originating_department=full_ba.originating_department,
        linked_initiative_id=full_ba.linked_initiative_id,
        linked_initiative_title=(
            full_ba.linked_initiative.title if full_ba.linked_initiative else None
        ),
        title=full_ba.title,
        background_summary=full_ba.background_summary,
        requested_action=full_ba.requested_action,
        priority=full_ba.priority,
        required_by_date=full_ba.required_by_date,
        status=full_ba.status,
        submitted_by_id=full_ba.submitted_by_id,
        submitted_by_name=(
            full_ba.submitted_by.full_name
            if full_ba.submitted_by
            else None
        ),
        submitted_date=full_ba.submitted_date,
        decision=full_ba.decision,
        decision_date=full_ba.decision_date,
        decided_by_name=(
            full_ba.decided_by.full_name
            if full_ba.decided_by
            else None
        ),
        is_governance_ready=full_ba.is_governance_ready,
        created_at=full_ba.created_at,
        updated_at=full_ba.updated_at,
        history=[
            BoardActionHistoryResponse(
                id=h.id,
                board_action_id=h.board_action_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                decision_notes=h.decision_notes,
                action_notes=h.action_notes,
                changed_by_name=(
                    h.changed_by.full_name
                    if h.changed_by
                    else None
                ),
                changed_at=h.changed_at,
            )
            for h in sorted(full_ba.history, key=_history_sort_key, reverse=True)
        ],
    )


@router.post(
    "/board-actions/{action_id}/decision",
    response_model=BoardActionResponse,
    summary="Record Board decision and resolution notes",
)
async def record_board_decision(
    action_id: uuid.UUID,
    data: BoardActionDecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.BOARD_ACTION_WRITE)),
) -> BoardActionResponse:
    try:
        ba = await CeoDashboardService.record_board_decision(db, action_id, data, current_user.id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err

    stmt = (
        select(BoardAction)
        .where(BoardAction.id == ba.id)
        .options(
            selectinload(BoardAction.submitted_by),
            selectinload(BoardAction.decided_by),
            selectinload(BoardAction.linked_initiative),
            selectinload(BoardAction.history).selectinload(BoardActionHistory.changed_by),
        )
    )
    res = await db.execute(stmt)
    full_ba = res.scalar_one()

    return BoardActionResponse(
        id=full_ba.id,
        reference_number=full_ba.reference_number,
        originating_department=full_ba.originating_department,
        linked_initiative_id=full_ba.linked_initiative_id,
        linked_initiative_title=(
            full_ba.linked_initiative.title if full_ba.linked_initiative else None
        ),
        title=full_ba.title,
        background_summary=full_ba.background_summary,
        requested_action=full_ba.requested_action,
        priority=full_ba.priority,
        required_by_date=full_ba.required_by_date,
        status=full_ba.status,
        submitted_by_id=full_ba.submitted_by_id,
        submitted_by_name=(
            full_ba.submitted_by.full_name
            if full_ba.submitted_by
            else None
        ),
        submitted_date=full_ba.submitted_date,
        decision=full_ba.decision,
        decision_date=full_ba.decision_date,
        decided_by_name=(
            full_ba.decided_by.full_name
            if full_ba.decided_by
            else None
        ),
        is_governance_ready=full_ba.is_governance_ready,
        created_at=full_ba.created_at,
        updated_at=full_ba.updated_at,
        history=[
            BoardActionHistoryResponse(
                id=h.id,
                board_action_id=h.board_action_id,
                previous_status=h.previous_status,
                new_status=h.new_status,
                decision_notes=h.decision_notes,
                action_notes=h.action_notes,
                changed_by_name=(
                    h.changed_by.full_name
                    if h.changed_by
                    else None
                ),
                changed_at=h.changed_at,
            )
            for h in sorted(full_ba.history, key=_history_sort_key, reverse=True)
        ],
    )


# ── Department Executive Updates ──────────────────────────────────────────────


@router.get(
    "/department-updates",
    response_model=list[DepartmentExecutiveUpdateResponse],
    summary="List periodic department executive updates",
)
async def list_department_updates(
    reporting_period: str | None = Query(None),
    department: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DEPARTMENT_UPDATE_READ)),
) -> list[DepartmentExecutiveUpdateResponse]:
    query = (
        select(DepartmentExecutiveUpdate)
        .where(DepartmentExecutiveUpdate.deleted_at.is_(None))
        .options(
            selectinload(DepartmentExecutiveUpdate.submitted_by),
            selectinload(DepartmentExecutiveUpdate.linked_initiative),
            selectinload(DepartmentExecutiveUpdate.linked_board_action),
        )
        .order_by(
            DepartmentExecutiveUpdate.reporting_period.desc(),
            DepartmentExecutiveUpdate.created_at.desc(),
        )
    )
    if reporting_period:
        query = query.where(DepartmentExecutiveUpdate.reporting_period == reporting_period)
    if department:
        query = query.where(DepartmentExecutiveUpdate.department == department)

    res = await db.execute(query)
    updates = res.scalars().all()

    return [
        DepartmentExecutiveUpdateResponse(
            id=u.id,
            reporting_period=u.reporting_period,
            department=u.department,
            submitted_by_id=u.submitted_by_id,
            submitted_by_name=(
                u.submitted_by.full_name
                if u.submitted_by
                else None
            ),
            submitted_date=u.submitted_date,
            headline_summary=u.headline_summary,
            accomplishments_narrative=u.accomplishments_narrative,
            risks_issues=u.risks_issues,
            support_decision_requested=u.support_decision_requested,
            status=u.status,
            linked_initiative_id=u.linked_initiative_id,
            linked_initiative_title=(
                u.linked_initiative.title if u.linked_initiative else None
            ),
            linked_board_action_id=u.linked_board_action_id,
            linked_board_action_title=(
                u.linked_board_action.title if u.linked_board_action else None
            ),
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in updates
    ]


@router.post(
    "/department-updates",
    response_model=DepartmentExecutiveUpdateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit or update a periodic department executive update for a reporting period",
)
async def submit_department_update(
    data: DepartmentExecutiveUpdateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.DEPARTMENT_UPDATE_WRITE)),
) -> DepartmentExecutiveUpdateResponse:
    await _assert_department_scope(db, current_user, data.department)
    u = await CeoDashboardService.submit_department_update(db, data, current_user.id)
    stmt = (
        select(DepartmentExecutiveUpdate)
        .where(DepartmentExecutiveUpdate.id == u.id)
        .options(
            selectinload(DepartmentExecutiveUpdate.submitted_by),
            selectinload(DepartmentExecutiveUpdate.linked_initiative),
            selectinload(DepartmentExecutiveUpdate.linked_board_action),
        )
    )
    res = await db.execute(stmt)
    full_u = res.scalar_one()

    return DepartmentExecutiveUpdateResponse(
        id=full_u.id,
        reporting_period=full_u.reporting_period,
        department=full_u.department,
        submitted_by_id=full_u.submitted_by_id,
        submitted_by_name=(
            full_u.submitted_by.full_name
            if full_u.submitted_by
            else None
        ),
        submitted_date=full_u.submitted_date,
        headline_summary=full_u.headline_summary,
        accomplishments_narrative=full_u.accomplishments_narrative,
        risks_issues=full_u.risks_issues,
        support_decision_requested=full_u.support_decision_requested,
        status=full_u.status,
        linked_initiative_id=full_u.linked_initiative_id,
        linked_initiative_title=(
            full_u.linked_initiative.title if full_u.linked_initiative else None
        ),
        linked_board_action_id=full_u.linked_board_action_id,
        linked_board_action_title=(
            full_u.linked_board_action.title if full_u.linked_board_action else None
        ),
        created_at=full_u.created_at,
        updated_at=full_u.updated_at,
    )
