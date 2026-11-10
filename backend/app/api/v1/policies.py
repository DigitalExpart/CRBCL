"""Company Policy API routes — centralized policy documents with version history and narrow RBAC."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.policy import CompanyPolicy, CompanyPolicyVersion
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission

router = APIRouter(prefix="/policies", tags=["Company Policies"])


class PolicyVersionResponse(BaseModel):
    id: uuid.UUID
    policy_id: uuid.UUID
    version_number: int
    title: str
    content: str
    change_summary: str
    author_id: uuid.UUID | None
    author_name: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PolicyResponse(BaseModel):
    id: uuid.UUID
    title: str
    slug: str
    category: str
    content: str
    version: int
    status: str
    department: str | None
    created_at: datetime
    updated_at: datetime
    created_by: uuid.UUID | None
    updated_by: uuid.UUID | None
    versions: list[PolicyVersionResponse] = []

    model_config = {"from_attributes": True}


class PolicyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    category: str = Field(default="General", max_length=100)
    content: str = Field(..., min_length=1)
    department: str | None = None
    status: str = Field(default="published")
    change_summary: str = Field(default="Initial draft")


class PolicyUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    category: str | None = None
    content: str | None = None
    department: str | None = None
    status: str | None = None
    change_summary: str = Field(..., min_length=3, description="Auditable reason for policy content edit")


def _slugify(text: str) -> str:
    import re
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s.strip("-") or "policy"


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    q: str | None = Query(None, description="Search query"),
    category: str | None = Query(None, description="Category filter"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active company policies. Accessible to all authenticated platform staff."""
    stmt = select(CompanyPolicy).where(CompanyPolicy.deleted_at.is_(None))
    if category:
        stmt = stmt.where(CompanyPolicy.category == category)
    if q:
        query_like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(CompanyPolicy.title).like(query_like),
                func.lower(CompanyPolicy.content).like(query_like),
                func.lower(CompanyPolicy.category).like(query_like),
            )
        )
    stmt = stmt.order_by(CompanyPolicy.category.asc(), CompanyPolicy.title.asc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.get("/{policy_id}", response_model=PolicyResponse)
async def get_policy(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single company policy with full version history."""
    stmt = select(CompanyPolicy).where(
        CompanyPolicy.id == policy_id,
        CompanyPolicy.deleted_at.is_(None),
    )
    res = await db.execute(stmt)
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return policy


@router.post("", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
async def create_policy(
    payload: PolicyCreate,
    request: Request,
    current_user: User = Depends(require_permission(Permissions.POLICY_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new company policy. Strictly restricted to designated Policy staff."""
    base_slug = _slugify(payload.title)
    slug = base_slug
    idx = 1
    while True:
        existing = await db.execute(select(CompanyPolicy).where(CompanyPolicy.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{idx}"
        idx += 1

    policy = CompanyPolicy(
        title=payload.title.strip(),
        slug=slug,
        category=payload.category,
        content=payload.content,
        version=1,
        status=payload.status,
        department=payload.department,
        created_by=current_user.id,
        updated_by=current_user.id,
    )
    db.add(policy)
    await db.flush()

    initial_version = CompanyPolicyVersion(
        policy_id=policy.id,
        version_number=1,
        title=policy.title,
        content=policy.content,
        change_summary=payload.change_summary or "Initial publication",
        author_id=current_user.id,
        author_name=current_user.full_name or current_user.email,
    )
    db.add(initial_version)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="COMPANY_POLICY_CREATED",
        user_id=current_user.id,
        entity_type="company_policy",
        entity_id=policy.id,
        after_data={"title": policy.title, "slug": policy.slug, "version": 1},
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(policy)
    return policy


@router.put("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    payload: PolicyUpdate,
    request: Request,
    current_user: User = Depends(require_permission(Permissions.POLICY_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    """
    Update company policy content and record an immutable version history entry.
    Strictly restricted to designated Policy staff.
    """
    stmt = select(CompanyPolicy).where(
        CompanyPolicy.id == policy_id,
        CompanyPolicy.deleted_at.is_(None),
    )
    res = await db.execute(stmt)
    policy = res.scalar_one_or_none()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    # Increment version
    new_version_num = policy.version + 1
    policy.version = new_version_num
    if payload.title:
        policy.title = payload.title.strip()
    if payload.category:
        policy.category = payload.category
    if payload.content is not None:
        policy.content = payload.content
    if payload.department is not None:
        policy.department = payload.department
    if payload.status:
        policy.status = payload.status
    policy.updated_by = current_user.id

    version_record = CompanyPolicyVersion(
        policy_id=policy.id,
        version_number=new_version_num,
        title=policy.title,
        content=policy.content,
        change_summary=payload.change_summary.strip(),
        author_id=current_user.id,
        author_name=current_user.full_name or current_user.email,
    )
    db.add(version_record)

    audit_service = AuditService(db)
    await audit_service.log_event(
        event_type="COMPANY_POLICY_UPDATED",
        user_id=current_user.id,
        entity_type="company_policy",
        entity_id=policy.id,
        after_data={
            "version": new_version_num,
            "change_summary": payload.change_summary,
            "editor": current_user.email,
        },
        ip_address=request.client.host if request.client else None,
    )

    await db.commit()
    await db.refresh(policy)
    return policy


@router.get("/{policy_id}/versions", response_model=list[PolicyVersionResponse])
async def list_policy_versions(
    policy_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve complete immutable version history for a company policy."""
    stmt = (
        select(CompanyPolicyVersion)
        .where(CompanyPolicyVersion.policy_id == policy_id)
        .order_by(CompanyPolicyVersion.version_number.desc())
    )
    res = await db.execute(stmt)
    return list(res.scalars().all())

