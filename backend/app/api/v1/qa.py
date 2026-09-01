"""Quality Assurance & Audit Tickler API Router (Phase 11)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.repositories.reporting_qa_repo import ReportingQARepository
from app.schemas.reporting_qa import QAAuditCreate, QAAuditResponse, QATemplateCreate
from app.services.qa_audit_service import QAAuditService

router = APIRouter(prefix="/qa", tags=["Quality Assurance & Case Audits"])


# ── 1. Templates & Checklist Governance ────────────────────────
@router.get(
    "/templates",
    dependencies=[Depends(require_permission(Permissions.QA_READ))],
)
async def list_qa_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.QA_READ)),
):
    await QAAuditService.ensure_default_template(db, current_user.id)
    return await ReportingQARepository.get_qa_audit_templates(db)


@router.post(
    "/templates",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.QA_TEMPLATE_MANAGE))],
)
async def create_qa_template(
    payload: QATemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.QA_TEMPLATE_MANAGE)),
):
    t_data = payload.model_dump()
    items_data = t_data.pop("items", [])
    return await ReportingQARepository.create_qa_audit_template(db, t_data, items_data, current_user.id)


# ── 2. Case Audits & Reviews ───────────────────────────────────
@router.get(
    "/audits",
    dependencies=[Depends(require_permission(Permissions.QA_READ))],
)
async def list_qa_audits(
    case_id: uuid.UUID | None = None,
    reviewer_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    audits, total = await ReportingQARepository.get_qa_audits(
        db, case_id=case_id, reviewer_id=reviewer_id, status=status, limit=limit, offset=offset
    )
    return {"items": audits, "total": total}


@router.post(
    "/audits",
    response_model=QAAuditResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permissions.QA_AUDIT_CREATE))],
)
async def create_qa_audit(
    payload: QAAuditCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.QA_AUDIT_CREATE)),
):
    return await QAAuditService.create_audit(db, payload.model_dump(), current_user.id)


@router.get(
    "/audits/{audit_id}",
    dependencies=[Depends(require_permission(Permissions.QA_READ))],
)
async def get_qa_audit_detail(
    audit_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    audit = await ReportingQARepository.get_qa_audit_by_id(db, audit_id)
    if not audit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QA audit not found")
    return audit


@router.put(
    "/audits/{audit_id}",
    response_model=QAAuditResponse,
    dependencies=[Depends(require_permission(Permissions.QA_AUDIT_CREATE))],
)
async def update_qa_audit(
    audit_id: uuid.UUID,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.QA_AUDIT_CREATE)),
):
    return await QAAuditService.update_audit(db, audit_id, payload, current_user.id)


# ── 3. Audit Tickler Engine & QA Dashboard ─────────────────────
@router.get(
    "/tickler",
    dependencies=[Depends(require_permission(Permissions.QA_READ))],
)
async def get_audit_tickler(
    db: AsyncSession = Depends(get_db),
):
    return await QAAuditService.get_audit_tickler_status(db)


@router.get(
    "/dashboard",
    dependencies=[Depends(require_permission(Permissions.QA_READ))],
)
async def get_qa_dashboard(
    db: AsyncSession = Depends(get_db),
):
    return await QAAuditService.get_qa_dashboard_metrics(db)
