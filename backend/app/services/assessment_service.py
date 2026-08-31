"""Domain service orchestrating Assessment lifecycle, answers, validations, locking, unlock, reassignment, and time-series comparisons."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.assessment import Assessment, AssessmentAnswer
from app.models.case import Case
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.assessment_template_repo import AssessmentTemplateRepository
from app.schemas.assessment import (
    AssessmentAnswersSaveRequest,
    AssessmentComparisonQuestion,
    AssessmentComparisonQuestionValue,
    AssessmentComparisonResponse,
    AssessmentCompleteRequest,
    AssessmentCreate,
    AssessmentLockRequest,
    AssessmentReassignRequest,
    AssessmentResponse,
    AssessmentUnlockRequest,
    AssessmentUpdate,
)
from app.services.assessment_validation_service import AssessmentValidationService
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class AssessmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AssessmentRepository(db)
        self.template_repo = AssessmentTemplateRepository(db)
        self.perm_service = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def get_assessment_or_404(
        self,
        assessment_id: uuid.UUID,
        current_user: User | None = None,
    ) -> Assessment:
        assessment = await self.repo.get_by_id_with_details(assessment_id)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        # Expire relationship collections to ensure fresh reload on subsequent calls
        self.db.expire(assessment, ["answers", "unlock_events", "status_history"])
        assessment = await self.repo.get_by_id_with_details(assessment_id)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found.")

        if current_user and await self.perm_service.is_user_restricted_from_case(current_user.id, assessment.case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

        return assessment

    def _compute_indicator_summary(self, assessment: Assessment) -> dict[str, Any]:
        """Deterministic computation of danger indicators, protective capacities, and concerns."""
        active_concerns: list[str] = []
        protective_capacities: list[str] = []
        present_danger_count = 0
        impending_danger_count = 0
        total_answered = 0

        for ans in assessment.answers:
            if not ans.question:
                continue
            total_answered += 1
            q = ans.question
            key = q.key.lower()

            if q.question_type == "BOOLEAN" and ans.boolean_value is True:
                if any(w in key for w in ("capacity", "protective", "strength", "willing", "recognize", "support", "kinship")):
                    protective_capacities.append(q.label)
                elif any(w in key for w in ("danger", "concern", "threat", "substance", "chemical", "broken", "overcrowd", "structural", "harm", "incapacitated", "peril", "vulnerable", "hazard")):
                    active_concerns.append(q.label)
                    if "present" in key or "immediate" in key or "incapacitated" in key or "peril" in key:
                        present_danger_count += 1
                    elif "impending" in key or "uncontrolled" in key or "vulnerable" in key:
                        impending_danger_count += 1

            elif q.question_type in ("SINGLE_SELECT", "MULTI_SELECT"):
                for opt_link in ans.selected_options:
                    if opt_link.option:
                        opt = opt_link.option
                        opt_key = opt.key.lower()
                        if any(w in opt_key for w in ("concern", "danger", "severe", "unsafe", "risk", "unstable", "overcrowded", "homeless", "plan_created", "custody")):
                            active_concerns.append(f"{q.label}: {opt.label}")
                        elif any(w in opt_key for w in ("safe", "connected", "stable", "protective")):
                            protective_capacities.append(f"{q.label}: {opt.label}")

        return {
            "total_questions_answered": total_answered,
            "active_concerns_count": len(active_concerns),
            "active_concerns": active_concerns,
            "protective_capacities_count": len(protective_capacities),
            "protective_capacities": protective_capacities,
            "present_danger_count": present_danger_count,
            "impending_danger_count": impending_danger_count,
        }

    async def create_assessment(
        self,
        payload: AssessmentCreate,
        current_user: User,
    ) -> Assessment:
        # 1. Check Case Restriction (ADR-010)
        if await self.perm_service.is_user_restricted_from_case(current_user.id, payload.case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

        # 2. Verify Case exists
        case = await self.db.get(Case, payload.case_id)
        if not case or case.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")

        # 3. Load Template & Version
        if payload.template_version_id:
            version = await self.template_repo.get_version_with_full_structure(payload.template_version_id)
            if not version:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified template version not found.")
            template = await self.template_repo.get(version.template_id)
        else:
            version = await self.template_repo.get_active_published_version_by_key(payload.template_key)
            if not version:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No active published version found for template '{payload.template_key}'.",
                )
            template = version.template

        if not template:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment template not found.")

        # 4. Generate Assessment Sequence Number
        conducted_at = payload.conducted_at or datetime.now(UTC)
        asm_number = await self.repo.generate_assessment_number(conducted_at)

        title = payload.title or f"{template.name} ({conducted_at.strftime('%Y-%m-%d')})"

        assessment = Assessment(
            case_id=payload.case_id,
            person_id=payload.person_id or case.client_id,
            client_id=payload.client_id or case.client_id,
            family_id=payload.family_id or case.family_id,
            household_id=payload.household_id,
            template_id=template.id,
            template_version_id=version.id,
            assessment_number=asm_number,
            title=title,
            status="DRAFT",
            conducted_by=current_user.id,
            conducted_at=conducted_at,
            summary=payload.summary,
            metadata_=payload.metadata_,
            created_by=current_user.id,
        )
        self.db.add(assessment)
        await self.db.flush()

        # Record Initial Status History
        await self.repo.add_status_history(
            assessment_id=assessment.id,
            from_status=None,
            to_status="DRAFT",
            reason="Assessment draft created.",
            created_by=current_user.id,
        )

        # Record Timeline & Audit
        await self.timeline.record_event(
            event_type="ASSESSMENT_STARTED",
            title=f"{template.name} Started ({asm_number})",
            description=f"Assessment initialized under version {version.version_number}.",
            entity_type="assessment",
            entity_id=assessment.id,
            case_id=assessment.case_id,
            client_id=assessment.client_id,
            family_id=assessment.family_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="ASSESSMENT_CREATED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={"assessment_number": asm_number, "template_key": template.key, "case_id": str(case.id)},
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def list_case_assessments(
        self,
        case_id: uuid.UUID,
        current_user: User,
        template_key: str | None = None,
        status_filter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[Assessment], int]:
        if await self.perm_service.is_user_restricted_from_case(current_user.id, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )
        return await self.repo.list_by_case(
            case_id=case_id,
            template_key=template_key,
            status=status_filter,
            limit=limit,
            offset=offset,
        )

    async def update_assessment_metadata(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentUpdate,
        current_user: User,
    ) -> Assessment:
        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)
        if assessment.status == "LOCKED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot edit a locked assessment.")

        if payload.title is not None:
            assessment.title = payload.title
        if payload.conducted_at is not None:
            assessment.conducted_at = payload.conducted_at
        if payload.determination is not None:
            assessment.determination = payload.determination
        if payload.determination_notes is not None:
            assessment.determination_notes = payload.determination_notes
        if payload.summary is not None:
            assessment.summary = payload.summary
        if payload.metadata_ is not None:
            assessment.metadata_ = payload.metadata_

        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)
        await self.db.flush()
        return assessment

    async def save_answers(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentAnswersSaveRequest,
        current_user: User,
    ) -> Assessment:
        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)
        if assessment.status == "LOCKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit answers of a locked assessment. An authorized Director must unlock it first.",
            )

        # 1. Validate answers format
        version = await self.template_repo.get_version_with_full_structure(assessment.template_version_id)
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found.")

        answers_data = [a.model_dump() for a in payload.answers]
        validation_errors = AssessmentValidationService.validate_answers(version, answers_data, is_completing=False)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Validation errors encountered.", "errors": validation_errors},
            )

        # 2. Upsert answers
        await self.repo.save_answers(assessment.id, answers_data)

        # 3. Update optional top-level determination/summary
        if payload.determination is not None:
            assessment.determination = payload.determination
        if payload.determination_notes is not None:
            assessment.determination_notes = payload.determination_notes
        if payload.summary is not None:
            assessment.summary = payload.summary

        # 4. Advance status from DRAFT to IN_PROGRESS
        if assessment.status == "DRAFT":
            assessment.status = "IN_PROGRESS"
            await self.repo.add_status_history(
                assessment_id=assessment.id,
                from_status="DRAFT",
                to_status="IN_PROGRESS",
                reason="Answers entered by worker.",
                created_by=current_user.id,
            )

        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)
        await self.db.flush()

        await self.audit.log_event(
            event_type="ASSESSMENT_ANSWERS_SAVED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={"answers_count": len(answers_data), "determination": assessment.determination},
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def complete_assessment(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentCompleteRequest,
        current_user: User,
    ) -> Assessment:
        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)
        if assessment.status == "LOCKED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment is locked.")

        # 1. Full validation including all required fields
        version = await self.template_repo.get_version_with_full_structure(assessment.template_version_id)
        if not version:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template version not found.")

        # Extract current answers
        current_answers_data = [
            {
                "question_id": ans.question_id,
                "boolean_value": ans.boolean_value,
                "number_value": float(ans.number_value) if ans.number_value is not None else None,
                "text_value": ans.text_value,
                "date_value": ans.date_value,
                "datetime_value": ans.datetime_value,
                "selected_option_ids": [opt.option_id for opt in ans.selected_options],
            }
            for ans in assessment.answers
        ]

        validation_errors = AssessmentValidationService.validate_answers(version, current_answers_data, is_completing=True)
        if validation_errors:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": "Cannot complete assessment. Required fields missing or invalid.", "errors": validation_errors},
            )

        prev_status = assessment.status
        assessment.status = "COMPLETED"
        assessment.determination = payload.determination
        assessment.determination_notes = payload.determination_notes
        if payload.summary:
            assessment.summary = payload.summary
        assessment.completed_at = datetime.now(UTC)
        assessment.completed_by = current_user.id
        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)

        await self.repo.add_status_history(
            assessment_id=assessment.id,
            from_status=prev_status,
            to_status="COMPLETED",
            reason=f"Assessment completed with determination: {payload.determination}",
            created_by=current_user.id,
        )

        await self.timeline.record_event(
            event_type="ASSESSMENT_COMPLETED",
            title=f"{assessment.template.name} Completed ({assessment.assessment_number})",
            description=f"Determination: {payload.determination}. Conducted by {current_user.full_name or current_user.email}.",
            entity_type="assessment",
            entity_id=assessment.id,
            case_id=assessment.case_id,
            client_id=assessment.client_id,
            family_id=assessment.family_id,
            created_by=current_user.id,
        )

        await self.outbox.enqueue(
            event_type="ASSESSMENT_COMPLETED",
            aggregate_type="assessment",
            aggregate_id=assessment.id,
            payload={
                "assessment_id": str(assessment.id),
                "assessment_number": assessment.assessment_number,
                "case_id": str(assessment.case_id),
                "determination": assessment.determination,
                "completed_by": str(current_user.id),
            },
        )

        await self.audit.log_event(
            event_type="ASSESSMENT_COMPLETED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={"determination": payload.determination, "assessment_number": assessment.assessment_number},
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def lock_assessment(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentLockRequest,
        current_user: User,
    ) -> Assessment:
        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)
        if assessment.status == "LOCKED":
            return assessment

        if assessment.status != "COMPLETED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only COMPLETED assessments can be locked.",
            )

        prev_status = assessment.status
        assessment.status = "LOCKED"
        assessment.locked_at = datetime.now(UTC)
        assessment.locked_by = current_user.id
        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)

        await self.repo.add_status_history(
            assessment_id=assessment.id,
            from_status=prev_status,
            to_status="LOCKED",
            reason=payload.reason or "Assessment finalized and locked.",
            created_by=current_user.id,
        )

        await self.timeline.record_event(
            event_type="ASSESSMENT_LOCKED",
            title=f"{assessment.template.name} Locked ({assessment.assessment_number})",
            description=f"Assessment permanently finalized and locked by {current_user.full_name or current_user.email}.",
            entity_type="assessment",
            entity_id=assessment.id,
            case_id=assessment.case_id,
            client_id=assessment.client_id,
            family_id=assessment.family_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="ASSESSMENT_LOCKED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={"assessment_number": assessment.assessment_number, "reason": payload.reason},
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def unlock_assessment(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentUnlockRequest,
        current_user: User,
    ) -> Assessment:
        # 1. Require Director/Supervisor unlock permission
        has_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.ASSESSMENT_UNLOCK)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only authorized Executive Directors/Supervisors can unlock assessments.",
            )

        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)
        if assessment.status != "LOCKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment is not currently locked.",
            )

        # 2. Record Append-Only Unlock Event
        await self.repo.add_unlock_event(
            assessment_id=assessment.id,
            unlocked_by=current_user.id,
            reason=payload.reason,
        )

        # 3. Transition back to COMPLETED for editing
        assessment.status = "COMPLETED"
        assessment.locked_at = None
        assessment.locked_by = None
        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)

        await self.repo.add_status_history(
            assessment_id=assessment.id,
            from_status="LOCKED",
            to_status="COMPLETED",
            reason=f"Director Unlock: {payload.reason}",
            created_by=current_user.id,
        )

        await self.timeline.record_event(
            event_type="ASSESSMENT_UNLOCKED",
            title=f"{assessment.template.name} Unlocked by Director ({assessment.assessment_number})",
            description=f"Reason: {payload.reason}",
            entity_type="assessment",
            entity_id=assessment.id,
            case_id=assessment.case_id,
            client_id=assessment.client_id,
            family_id=assessment.family_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="ASSESSMENT_UNLOCKED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={"reason": payload.reason, "assessment_number": assessment.assessment_number},
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def reassign_assessment(
        self,
        assessment_id: uuid.UUID,
        payload: AssessmentReassignRequest,
        current_user: User,
    ) -> Assessment:
        # 1. Require Director reassign permission
        has_perm = await self.perm_service.user_has_permission(current_user.id, Permissions.ASSESSMENT_REASSIGN)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: Only authorized Directors can reassign assessments to another case/family.",
            )

        assessment = await self.get_assessment_or_404(assessment_id, current_user=current_user)

        # 2. Check Case Restrictions on target case
        if await self.perm_service.is_user_restricted_from_case(current_user.id, payload.target_case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active on destination case.",
            )

        target_case = await self.db.get(Case, payload.target_case_id)
        if not target_case or target_case.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target case not found.")

        old_case_id = assessment.case_id
        assessment.case_id = payload.target_case_id
        if payload.target_family_id:
            assessment.family_id = payload.target_family_id
        if payload.target_household_id:
            assessment.household_id = payload.target_household_id
        if payload.target_person_id:
            assessment.person_id = payload.target_person_id

        assessment.updated_by = current_user.id
        assessment.updated_at = datetime.now(UTC)
        await self.db.flush()

        await self.timeline.record_event(
            event_type="ASSESSMENT_REASSIGNED",
            title=f"{assessment.template.name} Reassigned ({assessment.assessment_number})",
            description=f"Reassigned from case {old_case_id} to case {target_case.case_number}. Reason: {payload.reason}",
            entity_type="assessment",
            entity_id=assessment.id,
            case_id=target_case.id,
            client_id=assessment.client_id,
            family_id=assessment.family_id,
            created_by=current_user.id,
        )

        await self.audit.log_event(
            event_type="ASSESSMENT_REASSIGNED",
            user_id=current_user.id,
            entity_type="assessment",
            entity_id=assessment.id,
            metadata={
                "from_case_id": str(old_case_id),
                "to_case_id": str(target_case.id),
                "reason": payload.reason,
                "assessment_number": assessment.assessment_number,
            },
        )

        return await self.get_assessment_or_404(assessment.id, current_user=current_user)

    async def compare_assessments(
        self,
        assessment_ids: list[uuid.UUID],
        current_user: User,
    ) -> AssessmentComparisonResponse:
        if len(assessment_ids) < 2:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least 2 assessment IDs are required for comparison.")

        # Load all assessments
        assessments: list[Assessment] = []
        for aid in assessment_ids:
            asm = await self.get_assessment_or_404(aid, current_user=current_user)
            assessments.append(asm)

        # Sort chronologically
        assessments.sort(key=lambda x: x.conducted_at)

        # Verify same template lineage
        template_ids = {a.template_id for a in assessments}
        if len(template_ids) > 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot compare assessments of different template types.",
            )

        primary_template = assessments[0].template

        # Fetch all questions across versions used
        version_ids = {a.template_version_id for a in assessments}
        questions_by_key: dict[str, dict[str, Any]] = {}

        for vid in version_ids:
            v = await self.template_repo.get_version_with_full_structure(vid)
            if v:
                for sec in v.sections:
                    for q in sec.questions:
                        if q.key not in questions_by_key:
                            questions_by_key[q.key] = {
                                "question_id": q.id,
                                "question_key": q.key,
                                "label": q.label,
                                "section_title": sec.title,
                                "question_type": q.question_type,
                                "sort_order": (sec.sort_order * 100) + q.sort_order,
                            }

        # Build comparison grid
        comparison_questions: list[AssessmentComparisonQuestion] = []

        for q_key, q_info in sorted(questions_by_key.items(), key=lambda item: item[1]["sort_order"]):
            values: list[AssessmentComparisonQuestionValue] = []
            distinct_displays: set[str] = set()

            for asm in assessments:
                # Find answer for this question key
                matching_ans: AssessmentAnswer | None = None
                for ans in asm.answers:
                    if ans.question and ans.question.key == q_key:
                        matching_ans = ans
                        break

                display_str = "Not Answered"
                b_val = None
                n_val = None
                t_val = None
                d_val = None
                opt_labels: list[str] = []

                if matching_ans:
                    b_val = matching_ans.boolean_value
                    n_val = float(matching_ans.number_value) if matching_ans.number_value is not None else None
                    t_val = matching_ans.text_value
                    d_val = matching_ans.date_value

                    if b_val is not None:
                        display_str = "Yes" if b_val else "No"
                    elif n_val is not None:
                        display_str = str(n_val)
                    elif t_val:
                        display_str = t_val
                    elif d_val:
                        display_str = str(d_val)
                    elif matching_ans.selected_options:
                        opt_labels = [opt.option.label for opt in matching_ans.selected_options if opt.option]
                        display_str = ", ".join(opt_labels)

                distinct_displays.add(display_str)
                values.append(
                    AssessmentComparisonQuestionValue(
                        assessment_id=asm.id,
                        conducted_at=asm.conducted_at,
                        answer_display=display_str,
                        boolean_value=b_val,
                        number_value=n_val,
                        text_value=t_val,
                        date_value=d_val,
                        selected_option_labels=opt_labels,
                    )
                )

            is_changed = len(distinct_displays) > 1 and "Not Answered" not in distinct_displays

            comparison_questions.append(
                AssessmentComparisonQuestion(
                    question_id=q_info["question_id"],
                    question_key=q_key,
                    label=q_info["label"],
                    section_title=q_info["section_title"],
                    question_type=q_info["question_type"],
                    is_changed=is_changed,
                    values=values,
                )
            )

        # Build summary deltas
        summary_deltas = {
            "first_determination": assessments[0].determination,
            "latest_determination": assessments[-1].determination,
            "total_questions_tracked": len(comparison_questions),
            "changed_questions_count": sum(1 for q in comparison_questions if q.is_changed),
        }

        # Convert assessment models to response summaries
        asm_responses: list[AssessmentResponse] = []
        for a in assessments:
            asm_responses.append(
                AssessmentResponse(
                    id=a.id,
                    case_id=a.case_id,
                    case_number=a.case.case_number if a.case else None,
                    person_id=a.person_id,
                    person_name=f"{a.person.first_name} {a.person.last_name}" if a.person else None,
                    client_id=a.client_id,
                    family_id=a.family_id,
                    family_name=a.family.family_name if a.family else None,
                    household_id=a.household_id,
                    template_id=a.template_id,
                    template_key=a.template.key if a.template else None,
                    template_name=a.template.name if a.template else None,
                    template_category=a.template.category if a.template else None,
                    template_version_id=a.template_version_id,
                    version_number=a.template_version.version_number if a.template_version else None,
                    assessment_number=a.assessment_number,
                    title=a.title,
                    status=a.status,
                    determination=a.determination,
                    determination_notes=a.determination_notes,
                    conducted_by=a.conducted_by,
                    conducted_by_name=a.conductor.full_name or a.conductor.email if a.conductor else None,
                    conducted_at=a.conducted_at,
                    completed_at=a.completed_at,
                    completed_by=a.completed_by,
                    locked_at=a.locked_at,
                    locked_by=a.locked_by,
                    is_locked=a.status == "LOCKED",
                    summary=a.summary,
                    metadata_=a.metadata_,
                    created_at=a.created_at,
                    updated_at=a.updated_at,
                )
            )

        return AssessmentComparisonResponse(
            template_key=primary_template.key,
            template_name=primary_template.name,
            assessments=asm_responses,
            questions=comparison_questions,
            summary_deltas=summary_deltas,
        )
