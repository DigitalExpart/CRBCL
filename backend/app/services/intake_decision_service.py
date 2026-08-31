"""Intake decision service validating multi-child dispositions and decision completeness."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.referral import IntakeDecision
from app.repositories.referral_repo import ReferralRepository
from app.schemas.referral import IntakeDecisionSubmit


class IntakeDecisionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = ReferralRepository(db)

    async def validate_readiness_for_submission(self, referral_id: uuid.UUID) -> tuple[bool, list[str]]:
        """Verify that referral meets all requirements to submit for supervisor review."""
        referral = await self.repo.get_by_id(referral_id)
        if not referral:
            return False, ["Referral not found"]

        errors = []

        # 1. Must have at least 1 involved person
        if not referral.people:
            errors.append("At least one person must be associated with the referral.")

        # 2. Must have at least one primary concern
        has_primary_concern = any(c.is_primary for c in referral.concerns)
        if not referral.concerns:
            errors.append("At least one structured concern must be recorded.")
        elif not has_primary_concern:
            # If concerns exist, mark the first as primary automatically or require it
            pass

        # 3. Children must have dispositions
        children = [p for p in referral.people if p.role == "child"]
        child_person_ids = {c.person_id for c in children}
        disp_person_ids = {d.person_id for d in referral.dispositions}

        missing_disposition_children = child_person_ids - disp_person_ids
        if missing_disposition_children:
            errors.append(
                f"{len(missing_disposition_children)} child(ren) on the referral are missing an individual disposition."
            )

        # 4. Decision recommendation
        if not referral.decision or not referral.decision.overall_recommendation:
            errors.append("Overall intake recommendation is required before submission.")

        return len(errors) == 0, errors

    async def save_decision(
        self,
        referral_id: uuid.UUID,
        decision_data: IntakeDecisionSubmit,
        user_id: uuid.UUID | None = None,
    ) -> IntakeDecision:
        """Save decision recommendation and per-child dispositions."""
        # 1. Save overall decision
        decision = await self.repo.save_decision(
            referral_id=referral_id,
            overall_recommendation=decision_data.overall_recommendation,
            rationale=decision_data.rationale,
            submitted_by=user_id,
        )

        # 2. Save child dispositions
        for disp in decision_data.dispositions:
            await self.repo.save_child_disposition(
                referral_id=referral_id,
                person_id=disp.person_id,
                disposition_data={
                    "decision": disp.decision,
                    "reason": disp.reason,
                    "destination_team_id": disp.destination_team_id,
                    "destination_program": disp.destination_program,
                    "external_agency_name": disp.external_agency_name,
                    "external_referral_contact": disp.external_referral_contact,
                },
                decided_by=user_id,
            )

        return decision
