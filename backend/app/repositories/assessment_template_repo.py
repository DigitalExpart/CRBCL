"""Repository for Assessment Templates, Versions, Sections, Questions, and Options."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.assessment import (
    AssessmentQuestion,
    AssessmentQuestionOption,
    AssessmentSection,
    AssessmentTemplate,
    AssessmentTemplateVersion,
)
from app.repositories.base import BaseRepository


class AssessmentTemplateRepository(BaseRepository[AssessmentTemplate]):
    def __init__(self, db: AsyncSession):
        super().__init__(AssessmentTemplate, db)

    async def get_by_key(self, key: str) -> AssessmentTemplate | None:
        stmt = (
            select(AssessmentTemplate)
            .where(AssessmentTemplate.key == key)
            .options(
                selectinload(AssessmentTemplate.versions)
                .selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options)
            )
            .execution_options(populate_existing=True)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_with_versions(self, template_id: uuid.UUID) -> AssessmentTemplate | None:
        stmt = (
            select(AssessmentTemplate)
            .where(AssessmentTemplate.id == template_id)
            .options(
                selectinload(AssessmentTemplate.versions)
                .selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options)
            )
            .execution_options(populate_existing=True)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_version_with_full_structure(self, version_id: uuid.UUID) -> AssessmentTemplateVersion | None:
        stmt = (
            select(AssessmentTemplateVersion)
            .where(
                AssessmentTemplateVersion.id == version_id,
                AssessmentTemplateVersion.deleted_at.is_(None),
            )
            .options(
                selectinload(AssessmentTemplateVersion.template),
                selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options),
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_published_version(self, template_id: uuid.UUID) -> AssessmentTemplateVersion | None:
        stmt = (
            select(AssessmentTemplateVersion)
            .where(
                AssessmentTemplateVersion.template_id == template_id,
                AssessmentTemplateVersion.status == "PUBLISHED",
                AssessmentTemplateVersion.deleted_at.is_(None),
            )
            .order_by(AssessmentTemplateVersion.version_number.desc())
            .options(
                selectinload(AssessmentTemplateVersion.template),
                selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options),
            )
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_active_published_version_by_key(self, key: str) -> AssessmentTemplateVersion | None:
        stmt = (
            select(AssessmentTemplateVersion)
            .join(AssessmentTemplate, AssessmentTemplate.id == AssessmentTemplateVersion.template_id)
            .where(
                AssessmentTemplate.key == key,
                AssessmentTemplateVersion.status == "PUBLISHED",
                AssessmentTemplateVersion.deleted_at.is_(None),
            )
            .order_by(AssessmentTemplateVersion.version_number.desc())
            .options(
                selectinload(AssessmentTemplateVersion.template),
                selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options),
            )
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_templates(
        self, category: str | None = None, is_active: bool | None = None
    ) -> list[AssessmentTemplate]:
        stmt = (
            select(AssessmentTemplate)
            .options(selectinload(AssessmentTemplate.versions))
            .order_by(AssessmentTemplate.name.asc())
        )
        if category:
            stmt = stmt.where(AssessmentTemplate.category == category)
        if is_active is not None:
            stmt = stmt.where(AssessmentTemplate.is_active == is_active)
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_template_with_initial_version(
        self,
        key: str,
        name: str,
        description: str = "",
        category: str = "general",
        created_by: uuid.UUID | None = None,
        change_notes: str | None = "Initial version",
    ) -> AssessmentTemplateVersion:
        template = AssessmentTemplate(
            key=key,
            name=name,
            description=description,
            category=category,
            is_active=True,
        )
        self.db.add(template)
        await self.db.flush()

        version = AssessmentTemplateVersion(
            template_id=template.id,
            version_number=1,
            status="DRAFT",
            change_notes=change_notes,
            created_by=created_by,
        )
        self.db.add(version)
        await self.db.flush()
        return version

    async def create_new_version(
        self,
        template_id: uuid.UUID,
        clone_from_version_id: uuid.UUID | None = None,
        change_notes: str | None = None,
        created_by: uuid.UUID | None = None,
    ) -> AssessmentTemplateVersion:
        # Determine highest version number
        stmt = (
            select(AssessmentTemplateVersion.version_number)
            .where(AssessmentTemplateVersion.template_id == template_id)
            .order_by(AssessmentTemplateVersion.version_number.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        max_v = res.scalar_one_or_none() or 0

        new_version = AssessmentTemplateVersion(
            template_id=template_id,
            version_number=max_v + 1,
            status="DRAFT",
            change_notes=change_notes,
            created_by=created_by,
        )
        self.db.add(new_version)
        await self.db.flush()

        if clone_from_version_id:
            source = await self.get_version_with_full_structure(clone_from_version_id)
            if source:
                for sec in source.sections:
                    new_sec = AssessmentSection(
                        template_version_id=new_version.id,
                        key=sec.key,
                        title=sec.title,
                        description=sec.description,
                        sort_order=sec.sort_order,
                        is_required=sec.is_required,
                        visibility_condition=sec.visibility_condition,
                    )
                    self.db.add(new_sec)
                    await self.db.flush()

                    for q in sec.questions:
                        new_q = AssessmentQuestion(
                            section_id=new_sec.id,
                            key=q.key,
                            label=q.label,
                            help_text=q.help_text,
                            question_type=q.question_type,
                            is_required=q.is_required,
                            sort_order=q.sort_order,
                            is_reportable=q.is_reportable,
                            validation_rules=q.validation_rules,
                            visibility_condition=q.visibility_condition,
                            lookup_list_key=q.lookup_list_key,
                        )
                        self.db.add(new_q)
                        await self.db.flush()

                        for opt in q.options:
                            new_opt = AssessmentQuestionOption(
                                question_id=new_q.id,
                                key=opt.key,
                                label=opt.label,
                                description=opt.description,
                                score_value=opt.score_value,
                                sort_order=opt.sort_order,
                                is_active=opt.is_active,
                            )
                            self.db.add(new_opt)

        await self.db.flush()
        return new_version

    async def publish_version(
        self, version_id: uuid.UUID, published_by: uuid.UUID | None = None
    ) -> AssessmentTemplateVersion:
        version = await self.get_version_with_full_structure(version_id)
        if not version:
            raise ValueError("Template version not found")

        # Retire previously published versions for this template
        retire_stmt = select(AssessmentTemplateVersion).where(
            AssessmentTemplateVersion.template_id == version.template_id,
            AssessmentTemplateVersion.status == "PUBLISHED",
            AssessmentTemplateVersion.id != version_id,
        )
        retire_res = await self.db.execute(retire_stmt)
        for prev in retire_res.scalars().all():
            prev.status = "RETIRED"
            prev.effective_to = datetime.now(UTC)

        version.status = "PUBLISHED"
        version.published_by = published_by
        version.published_at = datetime.now(UTC)
        version.effective_from = datetime.now(UTC)
        await self.db.flush()
        return version
