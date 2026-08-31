"""Service for managing Assessment Templates and immutable Versions."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.assessment import (
    AssessmentQuestion,
    AssessmentQuestionOption,
    AssessmentSection,
    AssessmentTemplate,
    AssessmentTemplateVersion,
)
from app.repositories.assessment_template_repo import AssessmentTemplateRepository


class AssessmentTemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AssessmentTemplateRepository(db)
        self.audit = AuditService(db)

    async def list_templates(self, category: str | None = None, is_active: bool | None = None) -> list[AssessmentTemplate]:
        return await self.repo.list_templates(category=category, is_active=is_active)

    async def get_template_by_key_or_404(self, key: str) -> AssessmentTemplate:
        tmpl = await self.repo.get_by_key(key)
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment template '{key}' not found.")
        self.db.expire(tmpl, ["versions"])
        tmpl = await self.repo.get_by_key(key)
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Assessment template '{key}' not found.")
        return tmpl

    async def get_template_by_id_or_404(self, template_id: uuid.UUID) -> AssessmentTemplate:
        tmpl = await self.repo.get_with_versions(template_id)
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment template not found.")
        self.db.expire(tmpl, ["versions"])
        tmpl = await self.repo.get_with_versions(template_id)
        if not tmpl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment template not found.")
        return tmpl

    async def get_version_by_id_or_404(self, version_id: uuid.UUID) -> AssessmentTemplateVersion:
        version = await self.repo.get_version_with_full_structure(version_id)
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment template version not found.")
        return version

    async def create_template(
        self,
        key: str,
        name: str,
        description: str = "",
        category: str = "general",
        user_id: uuid.UUID | None = None,
        initial_version_notes: str | None = "Initial draft version",
    ) -> AssessmentTemplateVersion:
        existing = await self.repo.get_by_key(key)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Template with key '{key}' already exists.",
            )

        version = await self.repo.create_template_with_initial_version(
            key=key,
            name=name,
            description=description,
            category=category,
            created_by=user_id,
            change_notes=initial_version_notes,
        )
        await self.audit.log_event(
            event_type="ASSESSMENT_TEMPLATE_CREATED",
            user_id=user_id,
            entity_type="assessment_template",
            entity_id=version.template_id,
            metadata={"key": key, "name": name, "category": category},
        )
        return version

    async def create_new_version(
        self,
        template_id: uuid.UUID,
        clone_from_version_id: uuid.UUID | None = None,
        change_notes: str | None = None,
        user_id: uuid.UUID | None = None,
    ) -> AssessmentTemplateVersion:
        template = await self.get_template_by_id_or_404(template_id)
        new_version = await self.repo.create_new_version(
            template_id=template.id,
            clone_from_version_id=clone_from_version_id,
            change_notes=change_notes,
            created_by=user_id,
        )
        await self.audit.log_event(
            event_type="ASSESSMENT_TEMPLATE_VERSION_CREATED",
            user_id=user_id,
            entity_type="assessment_template_version",
            entity_id=new_version.id,
            metadata={"template_id": str(template.id), "version_number": new_version.version_number},
        )
        return new_version

    async def publish_version(
        self,
        version_id: uuid.UUID,
        user_id: uuid.UUID | None = None,
    ) -> AssessmentTemplateVersion:
        version = await self.get_version_by_id_or_404(version_id)
        if version.status == "PUBLISHED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version is already published.")
        if version.status == "RETIRED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot publish a retired version.")

        if not version.sections:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot publish a template version without any sections.")

        published = await self.repo.publish_version(version_id, published_by=user_id)
        await self.audit.log_event(
            event_type="ASSESSMENT_TEMPLATE_PUBLISHED",
            user_id=user_id,
            entity_type="assessment_template_version",
            entity_id=published.id,
            metadata={"template_id": str(published.template_id), "version_number": published.version_number},
        )
        return published

    async def add_section(
        self,
        version_id: uuid.UUID,
        key: str,
        title: str,
        description: str | None = None,
        sort_order: int = 0,
        is_required: bool = False,
        visibility_condition: dict[str, Any] | None = None,
    ) -> AssessmentSection:
        version = await self.get_version_by_id_or_404(version_id)
        if version.status == "PUBLISHED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Published versions are immutable. Create a new draft version to make changes.")

        section = AssessmentSection(
            template_version_id=version_id,
            key=key,
            title=title,
            description=description,
            sort_order=sort_order,
            is_required=is_required,
            visibility_condition=visibility_condition,
        )
        section.questions = []
        self.db.add(section)
        await self.db.flush()
        return section

    async def add_question(
        self,
        section_id: uuid.UUID,
        key: str,
        label: str,
        question_type: str,
        help_text: str | None = None,
        is_required: bool = False,
        sort_order: int = 0,
        is_reportable: bool = True,
        validation_rules: dict[str, Any] | None = None,
        visibility_condition: dict[str, Any] | None = None,
        lookup_list_key: str | None = None,
        options: list[dict[str, Any]] | None = None,
    ) -> AssessmentQuestion:
        # Check section's version status
        sec = await self.db.get(AssessmentSection, section_id)
        if not sec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found.")
        version = await self.get_version_by_id_or_404(sec.template_version_id)
        if version.status == "PUBLISHED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Published versions are immutable.")

        question = AssessmentQuestion(
            section_id=section_id,
            key=key,
            label=label,
            help_text=help_text,
            question_type=question_type,
            is_required=is_required,
            sort_order=sort_order,
            is_reportable=is_reportable,
            validation_rules=validation_rules,
            visibility_condition=visibility_condition,
            lookup_list_key=lookup_list_key,
        )
        question.options = []
        self.db.add(question)
        await self.db.flush()

        if options:
            for opt_data in options:
                opt = AssessmentQuestionOption(
                    question_id=question.id,
                    key=opt_data["key"],
                    label=opt_data["label"],
                    description=opt_data.get("description"),
                    score_value=opt_data.get("score_value"),
                    sort_order=opt_data.get("sort_order", 0),
                    is_active=opt_data.get("is_active", True),
                )
                self.db.add(opt)
                question.options.append(opt)
            await self.db.flush()

        return question
