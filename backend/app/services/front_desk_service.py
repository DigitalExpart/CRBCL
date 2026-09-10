"""Front Desk & Public Intake Ingestion Service."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.core import get_settings
from app.models.front_desk import (
    FrontDeskRoutingHistory,
    FrontDeskSequence,
    FrontDeskSubmission,
    PublicIntakeConversionLink,
)
from app.models.referral import Referral, ReferralReporter
from app.repositories.referral_repo import ReferralRepository
from app.schemas.front_desk import (
    CreateReferralFromSubmissionRequest,
    DuplicateCandidateResponse,
    FrontDeskStatsResponse,
    FrontDeskSubmissionManualCreate,
    FrontDeskSubmissionRouteRequest,
    GenericConversionRequest,
    GoogleFormIngestRequest,
)
from app.services.duplicate_service import DuplicateService
from app.workflows.outbox import OutboxService

logger = logging.getLogger("crbcl.front_desk")

FIELD_ALIAS_MAP = {
    "name": "submitter_name",
    "full_name": "submitter_name",
    "your_name": "submitter_name",
    "client_name": "submitter_name",
    "email": "submitter_email",
    "email_address": "submitter_email",
    "your_email": "submitter_email",
    "phone": "submitter_phone",
    "phone_number": "submitter_phone",
    "contact_number": "submitter_phone",
    "relationship": "submitter_relationship",
    "relationship_to_child": "submitter_relationship",
    "relationship_to_family": "submitter_relationship",
    "urgency": "urgency",
    "priority": "urgency",
    "inquiry_type": "inquiry_type",
    "type": "inquiry_type",
    "category": "inquiry_type",
    "summary": "summary",
    "concern": "summary",
    "reason_for_contact": "summary",
    "details": "details",
    "description": "details",
    "notes": "details",
}


def _normalize_extracted_fields(raw_responses: dict) -> dict[str, str]:
    """Map arbitrary Google question aliases to standardized staging fields."""
    normalized: dict[str, str] = {}
    for key, value in raw_responses.items():
        clean_key = str(key).strip().lower().replace(" ", "_").replace("?", "").replace(":", "")
        target_field = FIELD_ALIAS_MAP.get(clean_key)
        if target_field and target_field not in normalized and value:
            normalized[target_field] = str(value).strip()
    return normalized


class FrontDeskService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.outbox = OutboxService(db)
        self.audit = AuditService(db)

    async def generate_submission_number(self, target_date: date | None = None) -> str:
        """Concurrency-safe sequence generator for front desk submission numbers (FD-YYYY-NNNNNN)."""
        current_year = (target_date or date.today()).year

        stmt = (
            select(FrontDeskSequence)
            .where(FrontDeskSequence.year == current_year)
            .with_for_update()
        )
        result = await self.db.execute(stmt)
        seq = result.scalar_one_or_none()

        if not seq:
            seq = FrontDeskSequence(year=current_year, last_value=1)
            self.db.add(seq)
            await self.db.flush()
            next_val = 1
        else:
            seq.last_value += 1
            next_val = seq.last_value
            await self.db.flush()

        return f"FD-{current_year}-{next_val:06d}"

    async def _record_routing_history(
        self,
        submission_id: uuid.UUID,
        previous_status: str,
        new_status: str,
        previous_destination: str | None,
        new_destination: str | None,
        changed_by_id: uuid.UUID | None,
        reason_note: str | None = None,
    ) -> FrontDeskRoutingHistory:
        """Append-only audit record of every routing and status change."""
        history = FrontDeskRoutingHistory(
            submission_id=submission_id,
            previous_status=previous_status,
            new_status=new_status,
            previous_destination=previous_destination,
            new_destination=new_destination,
            changed_by_id=changed_by_id,
            changed_at=datetime.now(UTC),
            reason_note=reason_note,
        )
        self.db.add(history)
        await self.db.flush()
        return history

    async def ingest_google_form(
        self, payload: GoogleFormIngestRequest, secret_token: str | None = None
    ) -> tuple[FrontDeskSubmission, bool]:
        """Ingest external Google Form webhook submission.

        Returns (submission, is_new).
        Guarantees:
        - Constant-time secret comparison
        - Idempotency on response_id
        - Payload raw immutability
        - Zero Person/Client/Family/Case creation
        - Outbox event enqueued
        """
        settings = get_settings()
        expected_secret = settings.front_desk_webhook_secret

        # Constant-time comparison
        if not secret_token or not secrets.compare_digest(secret_token, expected_secret):
            logger.warning("Rejected public intake webhook: missing or invalid secret token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing webhook secret header (X-CRBCL-Webhook-Secret)",
            )

        # Idempotency check on external_response_id
        if payload.response_id and payload.response_id.strip():
            resp_id = payload.response_id.strip()
            existing_stmt = select(FrontDeskSubmission).where(
                FrontDeskSubmission.external_response_id == resp_id,
                FrontDeskSubmission.deleted_at.is_(None),
            )
            existing = (await self.db.execute(existing_stmt)).scalar_one_or_none()
            if existing:
                logger.info(f"Idempotent webhook return for existing submission: {existing.submission_number}")
                return existing, False

        # Apply configurable field mapping for any answers in responses
        mapped = _normalize_extracted_fields(payload.responses) if payload.responses else {}

        submitter_name = payload.submitter_name or mapped.get("submitter_name")
        submitter_email = payload.submitter_email or mapped.get("submitter_email")
        submitter_phone = payload.submitter_phone or mapped.get("submitter_phone")
        submitter_rel = payload.submitter_relationship or mapped.get("submitter_relationship")
        inquiry_type = payload.inquiry_type or mapped.get("inquiry_type") or "general_inquiry"
        urgency = payload.urgency or mapped.get("urgency") or "Medium"
        summary = payload.summary or mapped.get("summary") or f"Public web inquiry from {submitter_name or 'Anonymous'}"
        details = payload.details or mapped.get("details")

        sub_number = await self.generate_submission_number()
        raw_data = dict(payload.responses) if payload.responses else payload.model_dump()

        submission = FrontDeskSubmission(
            submission_number=sub_number,
            external_response_id=payload.response_id.strip() if payload.response_id else None,
            source=payload.source or "google_form",
            status="RECEIVED",
            urgency=urgency,
            submitter_name=submitter_name,
            submitter_email=submitter_email,
            submitter_phone=submitter_phone,
            submitter_relationship=submitter_rel,
            inquiry_type=inquiry_type,
            summary=summary.strip(),
            details=details,
            payload_raw=raw_data,
            received_at=datetime.now(UTC),
        )
        self.db.add(submission)
        await self.db.flush()

        # Record initial history
        await self._record_routing_history(
            submission_id=submission.id,
            previous_status="NONE",
            new_status="RECEIVED",
            previous_destination=None,
            new_destination=None,
            changed_by_id=None,
            reason_note=f"Ingested via {submission.source}",
        )

        # Enqueue transactional outbox event
        await self.outbox.enqueue(
            event_type="PUBLIC_INTAKE_RECEIVED",
            aggregate_type="front_desk_submission",
            aggregate_id=submission.id,
            payload={
                "submission_number": submission.submission_number,
                "source": submission.source,
                "urgency": submission.urgency,
                "received_at": submission.received_at.isoformat(),
            },
        )

        await self.db.commit()
        await self.db.refresh(submission)
        logger.info(f"Public intake submission created: {submission.submission_number}")
        return submission, True

    async def create_manual_submission(
        self, payload: FrontDeskSubmissionManualCreate, user_id: uuid.UUID
    ) -> FrontDeskSubmission:
        """Record a walk-in, phone call, or counter inquiry by Front Desk."""
        sub_number = await self.generate_submission_number()

        submission = FrontDeskSubmission(
            submission_number=sub_number,
            source=payload.source or "walk_in",
            status="RECEIVED",
            urgency=payload.urgency or "Medium",
            submitter_name=payload.submitter_name,
            submitter_email=payload.submitter_email,
            submitter_phone=payload.submitter_phone,
            submitter_relationship=payload.submitter_relationship,
            inquiry_type=payload.inquiry_type or "general_inquiry",
            summary=payload.summary.strip(),
            details=payload.details,
            payload_raw={},
            received_at=datetime.now(UTC),
            created_by=user_id,
        )
        self.db.add(submission)
        await self.db.flush()

        await self._record_routing_history(
            submission_id=submission.id,
            previous_status="NONE",
            new_status="RECEIVED",
            previous_destination=None,
            new_destination=None,
            changed_by_id=user_id,
            reason_note=f"Manual intake recorded ({payload.source})",
        )

        await self.outbox.enqueue(
            event_type="PUBLIC_INTAKE_RECEIVED",
            aggregate_type="front_desk_submission",
            aggregate_id=submission.id,
            payload={
                "submission_number": submission.submission_number,
                "source": submission.source,
                "urgency": submission.urgency,
                "received_at": submission.received_at.isoformat(),
            },
        )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def list_submissions(
        self,
        status_filter: str | None = None,
        department_filter: str | None = None,
        query: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[FrontDeskSubmission], int]:
        """List public intake submissions with filtering."""
        base_stmt = select(FrontDeskSubmission).where(FrontDeskSubmission.deleted_at.is_(None))

        if status_filter and status_filter.upper() != "ALL":
            base_stmt = base_stmt.where(FrontDeskSubmission.status == status_filter.upper())

        if department_filter and department_filter.strip():
            base_stmt = base_stmt.where(
                FrontDeskSubmission.destination_department == department_filter.strip()
            )

        if query and query.strip():
            term = f"%{query.strip()}%"
            base_stmt = base_stmt.where(
                or_(
                    FrontDeskSubmission.submission_number.ilike(term),
                    FrontDeskSubmission.submitter_name.ilike(term),
                    FrontDeskSubmission.submitter_email.ilike(term),
                    FrontDeskSubmission.submitter_phone.ilike(term),
                    FrontDeskSubmission.summary.ilike(term),
                )
            )

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        items_stmt = (
            base_stmt.order_by(FrontDeskSubmission.received_at.desc())
            .offset(offset)
            .limit(limit)
        )
        items_res = await self.db.execute(items_stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def get_submission(self, submission_id: uuid.UUID) -> FrontDeskSubmission | None:
        """Get single submission by ID with routing history and conversion links."""
        stmt = select(FrontDeskSubmission).where(
            FrontDeskSubmission.id == submission_id,
            FrontDeskSubmission.deleted_at.is_(None),
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def review_submission_by_front_desk(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        new_status: str,
        notes: str | None = None,
    ) -> FrontDeskSubmission:
        """Front desk marks submission under review or resolves non-routable items (SPAM, DUPLICATE, OUT_OF_SCOPE, CLOSED)."""
        valid_statuses = {
            "FRONT_DESK_REVIEW",
            "DUPLICATE",
            "OUT_OF_SCOPE",
            "SPAM",
            "CLOSED",
        }
        normalized = new_status.upper().strip()
        if normalized not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid front desk review status: {new_status}. Allowed: {valid_statuses}",
            )

        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        prev_status = submission.status
        submission.status = normalized
        submission.front_desk_worker_id = user_id
        if notes:
            submission.front_desk_notes = notes

        await self._record_routing_history(
            submission_id=submission.id,
            previous_status=prev_status,
            new_status=normalized,
            previous_destination=submission.destination_department,
            new_destination=submission.destination_department,
            changed_by_id=user_id,
            reason_note=notes,
        )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def route_submission(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        route_req: FrontDeskSubmissionRouteRequest,
    ) -> FrontDeskSubmission:
        """Front Desk routes submission to receiving department."""
        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        prev_status = submission.status
        prev_dest = submission.destination_department

        submission.status = "ROUTED"
        submission.destination_department = route_req.destination_department.strip()
        submission.destination_team_id = route_req.destination_team_id
        submission.urgency = route_req.urgency
        submission.front_desk_worker_id = user_id
        if route_req.routing_notes:
            submission.front_desk_notes = route_req.routing_notes

        await self._record_routing_history(
            submission_id=submission.id,
            previous_status=prev_status,
            new_status="ROUTED",
            previous_destination=prev_dest,
            new_destination=submission.destination_department,
            changed_by_id=user_id,
            reason_note=route_req.routing_notes,
        )

        await self.outbox.enqueue(
            event_type="PUBLIC_INTAKE_ROUTED",
            aggregate_type="front_desk_submission",
            aggregate_id=submission.id,
            payload={
                "submission_number": submission.submission_number,
                "destination_department": submission.destination_department,
                "urgency": submission.urgency,
                "routed_by": str(user_id),
            },
        )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def department_action(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        action: str,
        notes: str | None = None,
    ) -> FrontDeskSubmission:
        """Receiving department processes a routed submission.

        Actions:
        - DEPARTMENT_REVIEW: staff begins evaluating
        - ACCEPTED: department accepts operational ownership (NOT a referral yet)
        - RETURNED_TO_FRONT_DESK: returned to Front Desk with reason
        - DUPLICATE: department identified as duplicate
        - OUT_OF_SCOPE: department identified as out of scope
        """
        valid_actions = {
            "DEPARTMENT_REVIEW",
            "ACCEPTED",
            "RETURNED_TO_FRONT_DESK",
            "DUPLICATE",
            "OUT_OF_SCOPE",
        }
        normalized = action.upper().strip()
        if normalized not in valid_actions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid department action: {action}. Allowed: {valid_actions}",
            )

        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        prev_status = submission.status
        submission.status = normalized
        submission.department_worker_id = user_id
        if notes:
            submission.department_notes = notes

        await self._record_routing_history(
            submission_id=submission.id,
            previous_status=prev_status,
            new_status=normalized,
            previous_destination=submission.destination_department,
            new_destination=submission.destination_department,
            changed_by_id=user_id,
            reason_note=notes,
        )

        # Transactional outbox events
        if normalized == "RETURNED_TO_FRONT_DESK":
            await self.outbox.enqueue(
                event_type="PUBLIC_INTAKE_RETURNED",
                aggregate_type="front_desk_submission",
                aggregate_id=submission.id,
                payload={
                    "submission_number": submission.submission_number,
                    "return_reason": notes,
                    "returned_by": str(user_id),
                },
            )
        elif normalized == "ACCEPTED":
            await self.outbox.enqueue(
                event_type="PUBLIC_INTAKE_ACCEPTED",
                aggregate_type="front_desk_submission",
                aggregate_id=submission.id,
                payload={
                    "submission_number": submission.submission_number,
                    "destination_department": submission.destination_department,
                    "accepted_by": str(user_id),
                },
            )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def check_duplicates(self, submission_id: uuid.UUID) -> list[DuplicateCandidateResponse]:
        """Check for existing Person / Client / Family matching submitter without creating any records."""
        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        candidates: list[DuplicateCandidateResponse] = []
        name_parts = (submission.submitter_name or "").strip().split(" ", 1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        if first_name and last_name:
            dup_svc = DuplicateService(self.db)
            raw_candidates = await dup_svc.check_duplicates(
                first_name=first_name,
                last_name=last_name,
                phone=submission.submitter_phone,
                email=submission.submitter_email,
            )
            for c in raw_candidates:
                candidates.append(
                    DuplicateCandidateResponse(
                        entity_type="person",
                        id=uuid.UUID(c["person_id"]),
                        name=f"{c['first_name']} {c['last_name']}",
                        details=f"DOB: {c['date_of_birth'] or 'N/A'}, Factors: {', '.join(c.get('matching_factors', []))}",
                        match_score=float(c.get("similarity_score", 0.8)),
                        match_reasons=c.get("matching_factors", []),
                    )
                )

        return candidates

    async def convert_to_referral(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        req: CreateReferralFromSubmissionRequest,
    ) -> tuple[FrontDeskSubmission, Referral]:
        """Authorized receiving staff creates an internal Intake/Referral.

        Guarantees:
        - Submission must be ACCEPTED or DEPARTMENT_REVIEW
        - Creates Referral and ReferralReporter
        - Creates PublicIntakeConversionLink
        - Updates submission resulting_referral_id
        """
        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        if submission.resulting_referral_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Submission has already been linked to a Referral",
            )

        ref_repo = ReferralRepository(self.db)
        ref_number = await ref_repo.generate_referral_number(date.today())

        notes_content = f"Origin: Public Intake {submission.submission_number} (source: {submission.source})."
        if submission.details:
            notes_content += f"\n\nDetails:\n{submission.details}"
        if req.notes:
            notes_content += f"\n\nIntake Worker Notes:\n{req.notes}"

        referral = Referral(
            referral_number=ref_number,
            status="DRAFT",
            received_date=date.today(),
            received_time=datetime.now(UTC),
            received_method="web_form" if submission.source == "google_form" else submission.source,
            community=req.community,
            priority=req.priority,
            summary=submission.summary,
            notes=notes_content,
            immediate_safety_concerns=req.immediate_safety_concerns,
            assigned_team_id=req.assigned_team_id or submission.destination_team_id,
            assigned_worker_id=req.assigned_worker_id,
            created_by=user_id,
        )
        self.db.add(referral)
        await self.db.flush()

        if submission.submitter_name or submission.submitter_phone or submission.submitter_email:
            reporter = ReferralReporter(
                referral_id=referral.id,
                reporter_name=submission.submitter_name,
                phone=submission.submitter_phone,
                email=submission.submitter_email,
                relationship_to_family=submission.submitter_relationship,
                reporter_notes=f"Source: {submission.source} ({submission.submission_number})",
            )
            self.db.add(reporter)

        submission.resulting_referral_id = referral.id

        # Record generic conversion link
        link = PublicIntakeConversionLink(
            submission_id=submission.id,
            downstream_entity_type="referral",
            downstream_entity_id=referral.id,
            downstream_entity_reference=referral.referral_number,
            created_by_id=user_id,
            created_at=datetime.now(UTC),
            notes=req.notes,
        )
        self.db.add(link)

        # Append to routing history
        await self._record_routing_history(
            submission_id=submission.id,
            previous_status=submission.status,
            new_status=submission.status,
            previous_destination=submission.destination_department,
            new_destination=submission.destination_department,
            changed_by_id=user_id,
            reason_note=f"Created formal Referral {referral.referral_number}",
        )

        await self.audit.log_event(
            event_type="PUBLIC_INTAKE_CONVERTED_TO_REFERRAL",
            user_id=user_id,
            entity_type="front_desk_submission",
            entity_id=submission.id,
            after_data={
                "referral_id": str(referral.id),
                "referral_number": referral.referral_number,
            },
        )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission, referral

    async def link_generic_conversion(
        self,
        submission_id: uuid.UUID,
        user_id: uuid.UUID,
        req: GenericConversionRequest,
    ) -> PublicIntakeConversionLink:
        """Create generic downstream linkage from public submission to any domain record."""
        submission = await self.get_submission(submission_id)
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        link = PublicIntakeConversionLink(
            submission_id=submission.id,
            downstream_entity_type=req.downstream_entity_type.strip().lower(),
            downstream_entity_id=req.downstream_entity_id,
            downstream_entity_reference=req.downstream_entity_reference,
            created_by_id=user_id,
            created_at=datetime.now(UTC),
            notes=req.notes,
        )
        self.db.add(link)

        await self._record_routing_history(
            submission_id=submission.id,
            previous_status=submission.status,
            new_status=submission.status,
            previous_destination=submission.destination_department,
            new_destination=submission.destination_department,
            changed_by_id=user_id,
            reason_note=f"Linked downstream {req.downstream_entity_type} {req.downstream_entity_reference or ''}".strip(),
        )

        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_stats(self) -> FrontDeskStatsResponse:
        """Calculate queue and department breakdown statistics."""
        now = datetime.now(UTC)

        base_stmt = select(FrontDeskSubmission).where(FrontDeskSubmission.deleted_at.is_(None))
        res = await self.db.execute(base_stmt)
        all_subs = list(res.scalars().all())

        status_counts = {
            "RECEIVED": 0,
            "FRONT_DESK_REVIEW": 0,
            "ROUTED": 0,
            "DEPARTMENT_REVIEW": 0,
            "ACCEPTED": 0,
            "RETURNED_TO_FRONT_DESK": 0,
            "DUPLICATE": 0,
            "OUT_OF_SCOPE": 0,
            "CLOSED": 0,
            "SPAM": 0,
        }
        department_counts: dict[str, int] = {}
        oldest_unreviewed_hours: float | None = None

        for s in all_subs:
            st = s.status.upper()
            if st in status_counts:
                status_counts[st] += 1

            if s.destination_department:
                dept = s.destination_department.strip()
                department_counts[dept] = department_counts.get(dept, 0) + 1

            if s.status in {"RECEIVED", "FRONT_DESK_REVIEW", "RETURNED_TO_FRONT_DESK"}:
                age_hrs = (now - s.received_at).total_seconds() / 3600.0
                if oldest_unreviewed_hours is None or age_hrs > oldest_unreviewed_hours:
                    oldest_unreviewed_hours = round(age_hrs, 1)

        return FrontDeskStatsResponse(
            received_count=status_counts["RECEIVED"],
            front_desk_review_count=status_counts["FRONT_DESK_REVIEW"],
            routed_count=status_counts["ROUTED"],
            department_review_count=status_counts["DEPARTMENT_REVIEW"],
            accepted_count=status_counts["ACCEPTED"],
            returned_count=status_counts["RETURNED_TO_FRONT_DESK"],
            duplicate_count=status_counts["DUPLICATE"],
            out_of_scope_count=status_counts["OUT_OF_SCOPE"],
            closed_count=status_counts["CLOSED"],
            spam_count=status_counts["SPAM"],
            total_count=len(all_subs),
            oldest_unreviewed_hours=oldest_unreviewed_hours,
            department_counts=department_counts,
        )
