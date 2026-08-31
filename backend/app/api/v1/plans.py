"""FastAPI Endpoints for Safety Plans, Case Plans, Goals, Activities, Signatures."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.plan import Plan
from app.models.user import User
from app.permissions.constants import Permissions
from app.schemas.plan import (
    ActiveGoalItem,
    PhysicalSignatureUploadRequest,
    PlanActivityCompleteRequest,
    PlanActivityCreate,
    PlanActivityResponse,
    PlanActivityUpdate,
    PlanApproveRequest,
    PlanCloneRequest,
    PlanCreate,
    PlanDetailResponse,
    PlanFinalizeRequest,
    PlanGoalCompleteRequest,
    PlanGoalCreate,
    PlanGoalResponse,
    PlanGoalUpdate,
    PlanLockRequest,
    PlanPrintResponse,
    PlanReturnRequest,
    PlanSignatureCreate,
    PlanSignatureResponse,
    PlanSubmitRequest,
    PlanSummaryResponse,
    PlanUnlockRequest,
    PlanUpdate,
    PlanVersionCreate,
    PlanVersionResponse,
)
from app.services.plan_service import PlanService

router = APIRouter(tags=["Plans & Signatures"])


def _format_plan_response(service: PlanService, plan: Plan) -> PlanDetailResponse:
    curr_v = service._get_current_version(plan)
    metrics = service._compute_metrics(curr_v.goals)
    resp = PlanDetailResponse.model_validate(plan)
    resp.metrics = metrics
    resp.current_version = curr_v  # type: ignore
    return resp


# ── Case Level Endpoints ──────────────────────────────────────────────
@router.get("/cases/{case_id}/plans", response_model=list[PlanSummaryResponse])
async def list_case_plans(
    case_id: uuid.UUID,
    plan_type: Annotated[str | None, Query(description="SAFETY_PLAN, CASE_PLAN")] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all Safety Plans and Case Plans for a specific case with summary metrics."""
    service = PlanService(db)
    return await service.list_case_plans(current_user, case_id, plan_type)


@router.post("/cases/{case_id}/plans", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    case_id: uuid.UUID,
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new Safety Plan or Case Plan with initial Version 1."""
    if payload.case_id != case_id:
        payload.case_id = case_id
    service = PlanService(db)
    plan = await service.create_plan(current_user, payload)
    detailed_plan = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed_plan)


@router.get("/cases/{case_id}/active-goals", response_model=list[ActiveGoalItem])
async def list_active_goals_for_case(
    case_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List lightweight active goals for dropdown in Case Note authoring."""
    service = PlanService(db)
    await service._require_case_access(current_user.id, case_id)
    await service._require_perm(current_user.id, Permissions.PLAN_READ)
    goals = await service.repo.get_active_goals_by_case(case_id)
    items: list[ActiveGoalItem] = []
    for g in goals:
        plan = g.plan_version.plan
        items.append(
            ActiveGoalItem(
                id=g.id,
                goal_text=g.goal_text,
                category=g.category,
                target_date=g.target_date,
                status=g.status,
                plan_id=plan.id,
                plan_number=plan.plan_number,
                plan_type=plan.plan_type,
                plan_title=plan.title,
                activities=[
                    {"id": str(a.id), "activity_text": a.activity_text, "status": a.status, "due_date": a.due_date.isoformat() if a.due_date else None}
                    for a in g.activities
                ],
            )
        )
    return items


# ── Master Plan Endpoints ─────────────────────────────────────────────
@router.get("/plans/{id}", response_model=PlanDetailResponse)
async def get_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get complete Plan details with current version, goals, activities, and signatures."""
    service = PlanService(db)
    plan = await service.get_plan(current_user, id)
    return _format_plan_response(service, plan)


@router.put("/plans/{id}", response_model=PlanDetailResponse)
async def update_plan(
    id: uuid.UUID,
    payload: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update master plan details and metadata."""
    service = PlanService(db)
    plan = await service.update_plan(current_user, id, payload)
    return _format_plan_response(service, plan)


@router.post("/plans/{id}/submit", response_model=PlanDetailResponse)
async def submit_plan(
    id: uuid.UUID,
    payload: PlanSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Submit plan for supervisor clinical review."""
    service = PlanService(db)
    plan = await service.submit_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/approve", response_model=PlanDetailResponse)
async def approve_plan(
    id: uuid.UUID,
    payload: PlanApproveRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Supervisor approves plan and seals it into FINALIZED state with canonical SHA-256 hash."""
    service = PlanService(db)
    plan = await service.approve_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/return", response_model=PlanDetailResponse)
async def return_plan(
    id: uuid.UUID,
    payload: PlanReturnRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Supervisor returns plan to worker with actionable revisions."""
    service = PlanService(db)
    plan = await service.return_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/finalize", response_model=PlanDetailResponse)
async def finalize_plan(
    id: uuid.UUID,
    payload: PlanFinalizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Directly finalize plan and compute SHA-256 document hash."""
    service = PlanService(db)
    plan = await service.finalize_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/lock", response_model=PlanDetailResponse)
async def lock_plan(
    id: uuid.UUID,
    payload: PlanLockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Lock finalized plan to enforce complete immutability."""
    service = PlanService(db)
    plan = await service.lock_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/unlock", response_model=PlanDetailResponse)
async def unlock_plan(
    id: uuid.UUID,
    payload: PlanUnlockRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Director unlock with mandatory written justification."""
    service = PlanService(db)
    plan = await service.unlock_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, plan.id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/versions", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_new_version(
    id: uuid.UUID,
    payload: PlanVersionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create next version on an existing running plan."""
    service = PlanService(db)
    await service.create_new_version(current_user, id, payload)
    detailed = await service.get_plan(current_user, id)
    return _format_plan_response(service, detailed)


@router.post("/plans/{id}/clone", response_model=PlanDetailResponse, status_code=status.HTTP_201_CREATED)
async def clone_plan(
    id: uuid.UUID,
    payload: PlanCloneRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Clone an existing plan into a brand new Plan instance."""
    service = PlanService(db)
    new_plan = await service.clone_plan(current_user, id, payload)
    detailed = await service.get_plan(current_user, new_plan.id)
    return _format_plan_response(service, detailed)


# ── Goal & Activity Sub-Resources ─────────────────────────────────────
@router.post("/plans/{id}/goals", response_model=PlanGoalResponse, status_code=status.HTTP_201_CREATED)
async def add_goal(
    id: uuid.UUID,
    payload: PlanGoalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Add a goal to the current plan version."""
    service = PlanService(db)
    return await service.add_goal(current_user, id, payload)


@router.put("/plans/goals/{goal_id}", response_model=PlanGoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    payload: PlanGoalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update an existing goal."""
    service = PlanService(db)
    return await service.update_goal(current_user, goal_id, payload)


@router.post("/plans/goals/{goal_id}/complete", response_model=PlanGoalResponse)
async def complete_goal(
    goal_id: uuid.UUID,
    payload: PlanGoalCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Complete a goal command endpoint."""
    service = PlanService(db)
    return await service.complete_goal(current_user, goal_id, payload)


@router.post("/plans/goals/{goal_id}/activities", response_model=PlanActivityResponse, status_code=status.HTTP_201_CREATED)
async def add_activity(
    goal_id: uuid.UUID,
    payload: PlanActivityCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Add an activity to a goal."""
    service = PlanService(db)
    return await service.add_activity(current_user, goal_id, payload)


@router.put("/plans/activities/{activity_id}", response_model=PlanActivityResponse)
async def update_activity(
    activity_id: uuid.UUID,
    payload: PlanActivityUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update an activity."""
    service = PlanService(db)
    activity = await service.repo.get_activity_by_id(activity_id)
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found.")
    plan = activity.goal.plan_version.plan
    await PermissionService.check_case_access(service.db, current_user, plan.case_id)
    await PermissionService.require_permission(service.db, current_user, Permissions.PLAN_ACTIVITY_UPDATE)

    if payload.activity_text is not None:
        activity.activity_text = payload.activity_text
    if payload.responsible_type is not None:
        activity.responsible_type = payload.responsible_type
    if payload.responsible_user_id is not None:
        activity.responsible_user_id = payload.responsible_user_id
    if payload.responsible_person_id is not None:
        activity.responsible_person_id = payload.responsible_person_id
    if payload.responsible_name is not None:
        activity.responsible_name = payload.responsible_name
    if payload.due_date is not None:
        activity.due_date = payload.due_date
    if payload.status is not None:
        activity.status = payload.status
    if payload.completion_notes is not None:
        activity.completion_notes = payload.completion_notes
    if payload.sort_order is not None:
        activity.sort_order = payload.sort_order

    await service.db.flush()
    return await service.repo.get_activity_by_id(activity_id)


@router.post("/plans/activities/{activity_id}/complete", response_model=PlanActivityResponse)
async def complete_activity(
    activity_id: uuid.UUID,
    payload: PlanActivityCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Complete an activity."""
    service = PlanService(db)
    return await service.complete_activity(current_user, activity_id, payload)


# ── Signatures & Attestation ──────────────────────────────────────────
@router.post("/plans/{id}/signatures", response_model=PlanSignatureResponse, status_code=status.HTTP_201_CREATED)
async def add_signature(
    id: uuid.UUID,
    payload: PlanSignatureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Capture electronic signature verified against canonical SHA-256 document hash."""
    service = PlanService(db)
    return await service.add_signature(current_user, id, payload)


@router.post("/plans/{id}/physical-signature", response_model=PlanSignatureResponse, status_code=status.HTTP_201_CREATED)
async def add_physical_signature(
    id: uuid.UUID,
    payload: PhysicalSignatureUploadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Attach scanned physical signature document to finalized plan version."""
    service = PlanService(db)
    return await service.add_physical_signature(current_user, id, payload)


# ── Print View ────────────────────────────────────────────────────────
@router.get("/plans/{id}/print", response_model=PlanPrintResponse)
async def get_print_plan(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get printable plan representation with lodge branding and verified document hash."""
    service = PlanService(db)
    return await service.get_print_data(current_user, id)
