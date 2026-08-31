"""Repository for Assessment instances, answers, option selections, and audit history."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.assessment import (
    Assessment,
    AssessmentAnswer,
    AssessmentAnswerOption,
    AssessmentQuestion,
    AssessmentSection,
    AssessmentSequence,
    AssessmentStatusHistory,
    AssessmentTemplate,
    AssessmentTemplateVersion,
    AssessmentUnlockEvent,
)
from app.repositories.base import BaseRepository


class AssessmentRepository(BaseRepository[Assessment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Assessment, db)

    async def generate_assessment_number(self, conducted_at: datetime | None = None) -> str:
        """Concurrency-safe sequence generator: ASM-YYYYMM-NNNN (e.g. ASM-202608-0001)."""
        dt = conducted_at or datetime.now(UTC)
        period = dt.strftime("%Y%m")

        stmt = select(AssessmentSequence).where(AssessmentSequence.period == period).with_for_update()
        res = await self.db.execute(stmt)
        seq = res.scalar_one_or_none()

        if not seq:
            seq = AssessmentSequence(period=period, last_value=1)
            self.db.add(seq)
            val = 1
        else:
            seq.last_value += 1
            val = seq.last_value

        await self.db.flush()
        return f"ASM-{period}-{val:04d}"

    async def get_by_id_with_details(self, assessment_id: uuid.UUID) -> Assessment | None:
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id, Assessment.deleted_at.is_(None))
            .options(
                joinedload(Assessment.case),
                joinedload(Assessment.person),
                joinedload(Assessment.client),
                joinedload(Assessment.family),
                joinedload(Assessment.household),
                joinedload(Assessment.template),
                joinedload(Assessment.conductor),
                joinedload(Assessment.completer),
                joinedload(Assessment.locker),
                selectinload(Assessment.template_version)
                .selectinload(AssessmentTemplateVersion.sections)
                .selectinload(AssessmentSection.questions)
                .selectinload(AssessmentQuestion.options),
                selectinload(Assessment.answers).joinedload(AssessmentAnswer.question),
                selectinload(Assessment.answers)
                .selectinload(AssessmentAnswer.selected_options)
                .joinedload(AssessmentAnswerOption.option),
                selectinload(Assessment.status_history).joinedload(AssessmentStatusHistory.author),
                selectinload(Assessment.unlock_events).joinedload(AssessmentUnlockEvent.director),
            )
            .execution_options(populate_existing=True)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_by_case(
        self,
        case_id: uuid.UUID,
        template_key: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Assessment], int]:
        stmt = (
            select(Assessment)
            .where(Assessment.case_id == case_id, Assessment.deleted_at.is_(None))
            .options(
                joinedload(Assessment.template),
                joinedload(Assessment.template_version),
                joinedload(Assessment.person),
                joinedload(Assessment.family),
                joinedload(Assessment.household),
                joinedload(Assessment.conductor),
            )
            .order_by(Assessment.conducted_at.desc(), Assessment.created_at.desc())
        )
        if template_key:
            stmt = stmt.join(AssessmentTemplate, AssessmentTemplate.id == Assessment.template_id).where(
                AssessmentTemplate.key == template_key
            )
        if status:
            stmt = stmt.where(Assessment.status == status)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        paginated = stmt.offset(offset).limit(limit)
        res = await self.db.execute(paginated)
        return list(res.scalars().all()), total

    async def list_by_family(self, family_id: uuid.UUID) -> list[Assessment]:
        stmt = (
            select(Assessment)
            .where(Assessment.family_id == family_id, Assessment.deleted_at.is_(None))
            .options(
                joinedload(Assessment.template),
                joinedload(Assessment.template_version),
                joinedload(Assessment.case),
                joinedload(Assessment.conductor),
            )
            .order_by(Assessment.conducted_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def save_answers(
        self,
        assessment_id: uuid.UUID,
        answers_data: list[dict[str, Any]],
    ) -> list[AssessmentAnswer]:
        """Upsert relational answers and update multi-select option links."""
        # Fetch existing answers
        stmt = (
            select(AssessmentAnswer)
            .where(AssessmentAnswer.assessment_id == assessment_id)
            .options(selectinload(AssessmentAnswer.selected_options))
        )
        res = await self.db.execute(stmt)
        existing_map = {ans.question_id: ans for ans in res.scalars().all()}

        saved_answers: list[AssessmentAnswer] = []

        for item in answers_data:
            q_id = item["question_id"]
            ans = existing_map.get(q_id)
            if not ans:
                ans = AssessmentAnswer(
                    assessment_id=assessment_id,
                    question_id=q_id,
                )
                self.db.add(ans)
                await self.db.flush()

            # Update typed fields
            ans.boolean_value = item.get("boolean_value")
            ans.number_value = item.get("number_value")
            ans.text_value = item.get("text_value")
            ans.date_value = item.get("date_value")
            ans.datetime_value = item.get("datetime_value")
            ans.json_value = item.get("json_value")
            ans.notes = item.get("notes")
            ans.updated_at = datetime.now(UTC)

            # Sync multi-select options
            selected_ids = item.get("selected_option_ids", [])
            # Remove old links
            await self.db.execute(delete(AssessmentAnswerOption).where(AssessmentAnswerOption.answer_id == ans.id))
            # Insert new links
            for opt_id in selected_ids:
                link = AssessmentAnswerOption(
                    answer_id=ans.id,
                    option_id=opt_id,
                )
                self.db.add(link)

            saved_answers.append(ans)

        await self.db.flush()
        return saved_answers

    async def add_status_history(
        self,
        assessment_id: uuid.UUID,
        from_status: str | None,
        to_status: str,
        reason: str | None,
        created_by: uuid.UUID,
    ) -> AssessmentStatusHistory:
        history = AssessmentStatusHistory(
            assessment_id=assessment_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            created_by=created_by,
        )
        self.db.add(history)
        await self.db.flush()
        return history

    async def add_unlock_event(
        self,
        assessment_id: uuid.UUID,
        unlocked_by: uuid.UUID,
        reason: str,
    ) -> AssessmentUnlockEvent:
        event = AssessmentUnlockEvent(
            assessment_id=assessment_id,
            unlocked_by=unlocked_by,
            reason=reason,
        )
        self.db.add(event)
        await self.db.flush()
        return event
