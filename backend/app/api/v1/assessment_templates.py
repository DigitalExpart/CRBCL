"""API Router for Assessment Templates, Version Management, Sections, and Questions."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.assessment import (
    AssessmentQuestionCreate,
    AssessmentQuestionResponse,
    AssessmentSectionCreate,
    AssessmentSectionResponse,
    AssessmentTemplateCreate,
    AssessmentTemplateDetailResponse,
    AssessmentTemplateResponse,
    AssessmentTemplateVersionCreate,
    AssessmentTemplateVersionDetailResponse,
    AssessmentTemplateVersionResponse,
)
from app.services.assessment_template_service import AssessmentTemplateService

router = APIRouter(prefix="/assessment-templates", tags=["Assessment Templates"])


@router.get("", response_model=list[AssessmentTemplateResponse])
async def list_assessment_templates(
    category: str | None = Query(None, description="Filter by category (e.g. home, threat, prevention)"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List all available assessment questionnaire templates."""
    service = AssessmentTemplateService(db)
    templates = await service.list_templates(category=category, is_active=is_active)
    results: list[AssessmentTemplateResponse] = []
    for t in templates:
        pub_version = next((v for v in t.versions if v.status == "PUBLISHED"), None)
        results.append(
            AssessmentTemplateResponse(
                id=t.id,
                key=t.key,
                name=t.name,
                description=t.description,
                category=t.category,
                is_active=t.is_active,
                created_at=t.created_at,
                updated_at=t.updated_at,
                published_version=AssessmentTemplateVersionResponse.model_validate(pub_version)
                if pub_version
                else None,
            )
        )
    return results


@router.get("/{identifier}", response_model=AssessmentTemplateDetailResponse)
async def get_assessment_template(
    identifier: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get assessment template metadata with all versions by key or UUID."""
    service = AssessmentTemplateService(db)
    try:
        tmpl_id = uuid.UUID(identifier)
        tmpl = await service.get_template_by_id_or_404(tmpl_id)
    except ValueError:
        tmpl = await service.get_template_by_key_or_404(identifier)

    # Find active published version with details
    active_pub = next((v for v in tmpl.versions if v.status == "PUBLISHED"), None)
    active_detail = None
    if active_pub:
        full_version = await service.get_version_by_id_or_404(active_pub.id)
        active_detail = AssessmentTemplateVersionDetailResponse.model_validate(full_version)

    return AssessmentTemplateDetailResponse(
        id=tmpl.id,
        key=tmpl.key,
        name=tmpl.name,
        description=tmpl.description,
        category=tmpl.category,
        is_active=tmpl.is_active,
        created_at=tmpl.created_at,
        updated_at=tmpl.updated_at,
        versions=[AssessmentTemplateVersionResponse.model_validate(v) for v in tmpl.versions],
        active_version=active_detail,
    )


@router.get("/versions/{version_id}", response_model=AssessmentTemplateVersionDetailResponse)
async def get_template_version(
    version_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get full questionnaire structure (sections, questions, options) for a specific template version."""
    service = AssessmentTemplateService(db)
    version = await service.get_version_by_id_or_404(version_id)
    return AssessmentTemplateVersionDetailResponse.model_validate(version)


@router.post("", response_model=AssessmentTemplateVersionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment_template(
    payload: AssessmentTemplateCreate,
    user: User = Depends(require_permission(Permissions.ASSESSMENT_TEMPLATE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new assessment template with an initial draft version (Admin only)."""
    service = AssessmentTemplateService(db)
    version = await service.create_template(
        key=payload.key,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        user_id=user.id,
        initial_version_notes=payload.initial_version_notes,
    )
    await db.commit()
    full_version = await service.get_version_by_id_or_404(version.id)
    return AssessmentTemplateVersionDetailResponse.model_validate(full_version)


@router.post(
    "/{template_id}/versions",
    response_model=AssessmentTemplateVersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template_version(
    template_id: uuid.UUID,
    payload: AssessmentTemplateVersionCreate,
    user: User = Depends(require_permission(Permissions.ASSESSMENT_TEMPLATE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Create a new draft version for a template (optionally cloning an existing version)."""
    service = AssessmentTemplateService(db)
    version = await service.create_new_version(
        template_id=template_id,
        clone_from_version_id=payload.clone_from_version_id,
        change_notes=payload.change_notes,
        user_id=user.id,
    )
    await db.commit()
    full_version = await service.get_version_by_id_or_404(version.id)
    return AssessmentTemplateVersionDetailResponse.model_validate(full_version)


@router.post("/versions/{version_id}/publish", response_model=AssessmentTemplateVersionDetailResponse)
async def publish_template_version(
    version_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.ASSESSMENT_TEMPLATE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Publish a draft template version, making it immutable and active for new assessments."""
    service = AssessmentTemplateService(db)
    published = await service.publish_version(version_id, user_id=user.id)
    await db.commit()
    full_version = await service.get_version_by_id_or_404(published.id)
    return AssessmentTemplateVersionDetailResponse.model_validate(full_version)


@router.post(
    "/versions/{version_id}/sections", response_model=AssessmentSectionResponse, status_code=status.HTTP_201_CREATED
)
async def add_section_to_version(
    version_id: uuid.UUID,
    payload: AssessmentSectionCreate,
    user: User = Depends(require_permission(Permissions.ASSESSMENT_TEMPLATE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Add a section to a draft template version."""
    service = AssessmentTemplateService(db)
    sec = await service.add_section(
        version_id=version_id,
        key=payload.key,
        title=payload.title,
        description=payload.description,
        sort_order=payload.sort_order,
        is_required=payload.is_required,
        visibility_condition=payload.visibility_condition,
    )
    # Add optional initial questions
    for q_data in payload.questions:
        options_data = [opt.model_dump() for opt in q_data.options] if q_data.options else None
        await service.add_question(
            section_id=sec.id,
            key=q_data.key,
            label=q_data.label,
            question_type=q_data.question_type,
            help_text=q_data.help_text,
            is_required=q_data.is_required,
            sort_order=q_data.sort_order,
            is_reportable=q_data.is_reportable,
            validation_rules=q_data.validation_rules,
            visibility_condition=q_data.visibility_condition,
            lookup_list_key=q_data.lookup_list_key,
            options=options_data,
        )
    await db.commit()
    return AssessmentSectionResponse.model_validate(sec)


@router.post(
    "/sections/{section_id}/questions", response_model=AssessmentQuestionResponse, status_code=status.HTTP_201_CREATED
)
async def add_question_to_section(
    section_id: uuid.UUID,
    payload: AssessmentQuestionCreate,
    user: User = Depends(require_permission(Permissions.ASSESSMENT_TEMPLATE_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    """Add a question to a draft template section."""
    service = AssessmentTemplateService(db)
    options_data = [opt.model_dump() for opt in payload.options] if payload.options else None
    q = await service.add_question(
        section_id=section_id,
        key=payload.key,
        label=payload.label,
        question_type=payload.question_type,
        help_text=payload.help_text,
        is_required=payload.is_required,
        sort_order=payload.sort_order,
        is_reportable=payload.is_reportable,
        validation_rules=payload.validation_rules,
        visibility_condition=payload.visibility_condition,
        lookup_list_key=payload.lookup_list_key,
        options=options_data,
    )
    await db.commit()
    return AssessmentQuestionResponse.model_validate(q)
