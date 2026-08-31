"""Domain service for Placement Homes, Licensing, Members, Visits, Contacts, and History."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.case_management import CaseRestriction
from app.models.placement import BackgroundCheck, PlacementEpisode
from app.models.placement_home import (
    PlacementHome,
    PlacementHomeContactLog,
    PlacementHomeLicense,
    PlacementHomeMember,
    PlacementHomeVisit,
)
from app.repositories.placement_home_repo import PlacementHomeRepository
from app.schemas.placement_home import (
    HomeBackgroundCheckSummary,
    PlacementHistoryItemRead,
    PlacementHomeContactLogCreate,
    PlacementHomeContactLogUpdate,
    PlacementHomeCreate,
    PlacementHomeFilter,
    PlacementHomeLicenseCreate,
    PlacementHomeLicenseRenew,
    PlacementHomeLicenseUpdate,
    PlacementHomeMemberCreate,
    PlacementHomeMemberUpdate,
    PlacementHomeUpdate,
    PlacementHomeVisitCreate,
    PlacementHomeVisitUpdate,
)
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class PlacementHomeService:
    """Domain service managing placement home operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PlacementHomeRepository(session)
        self.audit = AuditService(session)
        self.outbox = OutboxService(session)
        self.timeline = TimelineService(session)

    async def create_home(self, payload: PlacementHomeCreate, user_id: uuid.UUID) -> PlacementHome:
        """Create a new placement home or care facility."""
        home_code = payload.home_code or await self.repo.generate_home_code()

        # Check unique code
        existing = await self.repo.get_by_code(home_code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Placement Home with code '{home_code}' already exists.",
            )

        home = PlacementHome(
            home_code=home_code,
            name=payload.name,
            provider_id=payload.provider_id,
            home_type=payload.home_type,
            status=payload.status,
            licensing_status=payload.licensing_status,
            total_capacity=payload.total_capacity,
            address_line_1=payload.address_line_1,
            address_line_2=payload.address_line_2,
            city=payload.city,
            province=payload.province,
            postal_code=payload.postal_code,
            community=payload.community,
            latitude=payload.latitude,
            longitude=payload.longitude,
            phone=payload.phone,
            email=payload.email,
            primary_caregiver_name=payload.primary_caregiver_name,
            intake_criteria_notes=payload.intake_criteria_notes,
            notes=payload.notes,
            metadata_=payload.metadata_,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.create(home)

        # Audit
        await self.audit.log(
            event_type="PLACEMENT_HOME_CREATED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "home_code": home.home_code,
                "name": home.name,
                "home_type": home.home_type,
                "total_capacity": home.total_capacity,
            },
        )

        return home

    async def get_home(self, home_id: uuid.UUID) -> PlacementHome:
        """Retrieve placement home by ID."""
        home = await self.repo.get_by_id(home_id)
        if not home:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Placement Home with ID '{home_id}' not found.",
            )
        return home

    async def get_home_detail(self, home_id: uuid.UUID) -> dict[str, Any]:
        """Retrieve placement home with live capacity and current license computed."""
        home = await self.get_home(home_id)
        occupied_beds = await self.repo.get_active_occupancy(home.id)
        available_beds = max(0, home.total_capacity - occupied_beds)

        # Identify current active license (sorted newest first)
        licenses_list = sorted(
            [l for l in home.licenses if l.deleted_at is None],
            key=lambda l: (l.effective_date or date.min, l.created_at or datetime.min),
            reverse=True,
        )
        current_lic = next((l for l in licenses_list if l.status == "ACTIVE"), None)

        return {
            "id": home.id,
            "home_code": home.home_code,
            "name": home.name,
            "provider_id": home.provider_id,
            "provider_name": home.provider.name if home.provider else None,
            "home_type": home.home_type,
            "status": home.status,
            "licensing_status": home.licensing_status,
            "total_capacity": home.total_capacity,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "address_line_1": home.address_line_1,
            "address_line_2": home.address_line_2,
            "city": home.city,
            "province": home.province,
            "postal_code": home.postal_code,
            "community": home.community,
            "latitude": home.latitude,
            "longitude": home.longitude,
            "phone": home.phone,
            "email": home.email,
            "primary_caregiver_name": home.primary_caregiver_name,
            "intake_criteria_notes": home.intake_criteria_notes,
            "notes": home.notes,
            "metadata_": home.metadata_,
            "is_archived": home.is_archived,
            "archived_at": home.archived_at,
            "created_at": home.created_at,
            "updated_at": home.updated_at,
            "current_license": current_lic,
            "members": [
                {
                    "id": m.id,
                    "placement_home_id": m.placement_home_id,
                    "person_id": m.person_id,
                    "person_name": f"{m.person.first_name} {m.person.last_name}" if m.person else None,
                    "role": m.role,
                    "start_date": m.start_date,
                    "end_date": m.end_date,
                    "is_active": m.is_active,
                    "notes": m.notes,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                }
                for m in home.members
                if m.deleted_at is None
            ],
            "licenses": licenses_list,
            "visits": [
                {
                    "id": v.id,
                    "placement_home_id": v.placement_home_id,
                    "worker_id": v.worker_id,
                    "worker_name": (v.worker.display_name or v.worker.full_name or v.worker.email) if v.worker else None,
                    "visit_date": v.visit_date,
                    "visit_type": v.visit_type,
                    "purpose": v.purpose,
                    "summary": v.summary,
                    "observations": v.observations,
                    "follow_up_required": v.follow_up_required,
                    "follow_up_due_date": v.follow_up_due_date,
                    "status": v.status,
                    "created_at": v.created_at,
                    "updated_at": v.updated_at,
                }
                for v in home.visits
                if v.deleted_at is None
            ],
            "contact_logs": [
                {
                    "id": c.id,
                    "placement_home_id": c.placement_home_id,
                    "person_id": c.person_id,
                    "person_name": f"{c.person.first_name} {c.person.last_name}" if c.person else None,
                    "worker_id": c.worker_id,
                    "worker_name": (c.worker.display_name or c.worker.full_name or c.worker.email) if c.worker else None,
                    "contact_type": c.contact_type,
                    "contact_date": c.contact_date,
                    "duration_minutes": c.duration_minutes,
                    "subject": c.subject,
                    "notes": c.notes,
                    "follow_up_action": c.follow_up_action,
                    "created_at": c.created_at,
                    "updated_at": c.updated_at,
                }
                for c in home.contact_logs
                if c.deleted_at is None
            ],
        }


    async def update_home(self, home_id: uuid.UUID, payload: PlacementHomeUpdate, user_id: uuid.UUID) -> PlacementHome:
        """Update placement home fields."""
        home = await self.get_home(home_id)
        update_data = payload.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            setattr(home, k, v)

        home.updated_by = user_id
        await self.repo.update(home)

        await self.audit.log(
            event_type="PLACEMENT_HOME_UPDATED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data=update_data,
        )
        return home

    async def archive_home(self, home_id: uuid.UUID, user_id: uuid.UUID) -> PlacementHome:
        """Archive a placement home without deleting historical placement linkages."""
        home = await self.get_home(home_id)
        occupied = await self.repo.get_active_occupancy(home_id)
        if occupied > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot archive home with {occupied} active placement(s). Please transfer or discharge residents first.",
            )

        home.is_archived = True
        home.status = "CLOSED"
        home.archived_at = datetime.now(UTC)
        home.archived_by = user_id
        home.updated_by = user_id

        await self.repo.update(home)
        await self.audit.log(
            event_type="PLACEMENT_HOME_ARCHIVED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={"status": "CLOSED", "is_archived": True},
        )
        return home

    # ── Members Management ─────────────────────────────────────
    async def add_member(
        self, home_id: uuid.UUID, payload: PlacementHomeMemberCreate, user_id: uuid.UUID
    ) -> PlacementHomeMember:
        """Attach a household member / caregiver to the placement home."""
        home = await self.get_home(home_id)

        member = PlacementHomeMember(
            placement_home_id=home.id,
            person_id=payload.person_id,
            role=payload.role,
            start_date=payload.start_date,
            end_date=payload.end_date,
            is_active=payload.is_active,
            notes=payload.notes,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.add_member(member)

        await self.audit.log(
            event_type="PLACEMENT_HOME_MEMBER_ADDED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "member_id": str(member.id),
                "person_id": str(payload.person_id),
                "role": payload.role,
            },
        )
        return await self.repo.get_member(member.id)

    async def update_member(
        self, home_id: uuid.UUID, member_id: uuid.UUID, payload: PlacementHomeMemberUpdate, user_id: uuid.UUID
    ) -> PlacementHomeMember:
        member = await self.repo.get_member(member_id)
        if not member or member.placement_home_id != home_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Home member not found.")

        update_data = payload.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(member, k, v)
        member.updated_by = user_id

        await self.session.flush()
        await self.audit.log(
            event_type="PLACEMENT_HOME_MEMBER_UPDATED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home_id,
            after_data=update_data,
        )
        return member

    async def remove_member(self, home_id: uuid.UUID, member_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = await self.repo.get_member(member_id)
        if not member or member.placement_home_id != home_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Home member not found.")

        member.deleted_at = datetime.now(UTC)
        await self.session.flush()

        await self.audit.log(
            event_type="PLACEMENT_HOME_MEMBER_REMOVED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home_id,
            after_data={"member_id": str(member_id)},
        )

    # ── Licensing Management ───────────────────────────────────
    async def create_license(
        self, home_id: uuid.UUID, payload: PlacementHomeLicenseCreate, user_id: uuid.UUID
    ) -> PlacementHomeLicense:
        """Record an initial or new license for a placement home."""
        home = await self.get_home(home_id)

        license_ = PlacementHomeLicense(
            placement_home_id=home.id,
            license_number=payload.license_number,
            license_type=payload.license_type,
            status=payload.status,
            application_date=payload.application_date,
            issue_date=payload.issue_date,
            effective_date=payload.effective_date,
            expiry_date=payload.expiry_date,
            renewal_date=payload.renewal_date,
            issuing_authority=payload.issuing_authority,
            max_capacity=payload.max_capacity,
            conditions=payload.conditions,
            notes=payload.notes,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.create_license(license_)

        # Update home status if license is active
        if payload.status == "ACTIVE":
            home.licensing_status = "ACTIVE"
            if payload.max_capacity is not None and payload.max_capacity > 0:
                home.total_capacity = payload.max_capacity
            await self.repo.update(home)

        await self.audit.log(
            event_type="PLACEMENT_HOME_LICENSE_CREATED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "license_number": payload.license_number,
                "expiry_date": str(payload.expiry_date),
                "status": payload.status,
            },
        )
        return license_

    async def renew_license(
        self, home_id: uuid.UUID, payload: PlacementHomeLicenseRenew, user_id: uuid.UUID
    ) -> PlacementHomeLicense:
        """Renew home licensing while preserving full historical licence records without destructive overwrites."""
        home = await self.get_home(home_id)

        # 1. Supersede previous active licenses
        for lic in home.licenses:
            if lic.status == "ACTIVE" and lic.deleted_at is None:
                lic.status = "EXPIRED"
                lic.updated_by = user_id

        # 2. Insert new active license record
        new_lic = PlacementHomeLicense(
            placement_home_id=home.id,
            license_number=payload.new_license_number,
            license_type=payload.license_type,
            status="ACTIVE",
            effective_date=payload.effective_date,
            expiry_date=payload.expiry_date,
            renewal_date=payload.effective_date,
            issuing_authority=payload.issuing_authority,
            max_capacity=payload.max_capacity,
            conditions=payload.conditions,
            notes=payload.notes,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.create_license(new_lic)
        home.licenses.append(new_lic)

        # 3. Keep home status synchronized
        home.licensing_status = "ACTIVE"
        if payload.max_capacity is not None and payload.max_capacity > 0:
            home.total_capacity = payload.max_capacity
        await self.repo.update(home)

        await self.audit.log(
            event_type="PLACEMENT_HOME_LICENSE_RENEWED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "new_license_number": payload.new_license_number,
                "effective_date": str(payload.effective_date),
                "expiry_date": str(payload.expiry_date),
            },
        )

        return new_lic

    # ── Visits & Inspections ───────────────────────────────────
    async def create_visit(
        self, home_id: uuid.UUID, payload: PlacementHomeVisitCreate, user_id: uuid.UUID
    ) -> PlacementHomeVisit:
        """Log a home inspection or support visit."""
        home = await self.get_home(home_id)

        visit = PlacementHomeVisit(
            placement_home_id=home.id,
            worker_id=user_id,
            visit_date=payload.visit_date,
            visit_type=payload.visit_type,
            purpose=payload.purpose,
            summary=payload.summary,
            observations=payload.observations,
            follow_up_required=payload.follow_up_required,
            follow_up_due_date=payload.follow_up_due_date,
            status=payload.status,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.create_visit(visit)

        await self.audit.log(
            event_type="PLACEMENT_HOME_VISIT_LOGGED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "visit_date": str(payload.visit_date),
                "visit_type": payload.visit_type,
                "follow_up_required": payload.follow_up_required,
            },
        )
        return await self.repo.get_visit(visit.id)

    # ── Contact Logs ───────────────────────────────────────────
    async def create_contact_log(
        self, home_id: uuid.UUID, payload: PlacementHomeContactLogCreate, user_id: uuid.UUID
    ) -> PlacementHomeContactLog:
        """Log direct communication with home caregivers."""
        home = await self.get_home(home_id)

        contact = PlacementHomeContactLog(
            placement_home_id=home.id,
            person_id=payload.person_id,
            worker_id=user_id,
            contact_type=payload.contact_type,
            contact_date=payload.contact_date,
            duration_minutes=payload.duration_minutes,
            subject=payload.subject,
            notes=payload.notes,
            follow_up_action=payload.follow_up_action,
            created_by=user_id,
            updated_by=user_id,
        )
        await self.repo.create_contact_log(contact)

        await self.audit.log(
            event_type="PLACEMENT_HOME_CONTACT_LOGGED",
            user_id=user_id,
            entity_type="placement_home",
            entity_id=home.id,
            after_data={
                "contact_type": payload.contact_type,
                "subject": payload.subject,
            },
        )
        return await self.repo.get_contact_log(contact.id)

    # ── Background Checks Summary ──────────────────────────────
    async def get_background_checks_summary(
        self, home_id: uuid.UUID, current_user: Any
    ) -> list[HomeBackgroundCheckSummary]:
        """Aggregate background screening status for all household members."""
        home = await self.get_home(home_id)
        person_ids = [m.person_id for m in home.members if m.deleted_at is None]

        if not person_ids:
            return []

        # Query background checks for these persons
        query = select(BackgroundCheck).where(
            BackgroundCheck.subject_id.in_(person_ids),
            BackgroundCheck.deleted_at.is_(None),
        )
        res = await self.session.execute(query)
        checks_by_person: dict[uuid.UUID, list[BackgroundCheck]] = {}
        for chk in res.scalars().all():
            if chk.subject_id:
                checks_by_person.setdefault(chk.subject_id, []).append(chk)

        today = date.today()
        summaries: list[HomeBackgroundCheckSummary] = []

        for m in home.members:
            if m.deleted_at is not None:
                continue
            person_name = f"{m.person.first_name} {m.person.last_name}" if m.person else "Unknown"
            p_checks = checks_by_person.get(m.person_id, [])

            if not p_checks:
                summaries.append(
                    HomeBackgroundCheckSummary(
                        member_id=m.id,
                        member_name=person_name,
                        role=m.role,
                        status="NOT_STARTED",
                        is_eligible=False,
                    )
                )
            else:
                latest_chk = sorted(p_checks, key=lambda c: c.request_date, reverse=True)[0]
                is_exp = bool(latest_chk.expiry_date and latest_chk.expiry_date < today)
                summaries.append(
                    HomeBackgroundCheckSummary(
                        member_id=m.id,
                        member_name=person_name,
                        role=m.role,
                        check_id=latest_chk.id,
                        check_type=latest_chk.check_type,
                        status=latest_chk.status if not is_exp else "EXPIRED",
                        clearance_number=latest_chk.clearance_reference_number,
                        completed_date=latest_chk.completion_date,
                        expiry_date=latest_chk.expiry_date,
                        is_expired=is_exp,
                        is_eligible=latest_chk.is_eligible_for_placement and not is_exp,
                    )
                )

        return summaries

    # ── Placement History with Privacy Redaction ───────────────
    async def get_placement_history(
        self, home_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> list[PlacementHistoryItemRead]:
        """Fetch historical placements. If the requesting user is restricted from a child's case, redact child/case identity."""
        home = await self.get_home(home_id)
        episodes = await self.repo.get_placement_history(home.id)

        # Query all active case restrictions for current user
        restr_query = select(CaseRestriction.case_id).where(
            CaseRestriction.user_id == current_user_id,
            CaseRestriction.is_active.is_(True),
        )

        restr_res = await self.session.execute(restr_query)
        restricted_case_ids = set(restr_res.scalars().all())

        items: list[PlacementHistoryItemRead] = []
        for ep in episodes:
            is_restricted = ep.case_id in restricted_case_ids

            end = ep.end_date or date.today()
            duration = max(1, (end - ep.start_date).days)

            if is_restricted:
                items.append(
                    PlacementHistoryItemRead(
                        placement_id=ep.id,
                        case_id=None,
                        case_number="[CONFIDENTIAL / RESTRICTED]",
                        child_id=None,
                        child_name="[RESTRICTED CHILD RECORD]",
                        is_redacted=True,
                        placement_type=ep.placement_type,
                        start_date=ep.start_date,
                        end_date=ep.end_date,
                        duration_days=duration,
                        status=ep.status,
                        discharge_reason=ep.discharge_episode.discharge_reason if ep.discharge_episode else None,
                    )
                )
            else:
                child_name = (
                    f"{ep.child.first_name} {ep.child.last_name}" if ep.child else "Unknown Child"
                )
                case_num = ep.case.case_number if ep.case else None
                items.append(
                    PlacementHistoryItemRead(
                        placement_id=ep.id,
                        case_id=ep.case_id,
                        case_number=case_num,
                        child_id=ep.child_id,
                        child_name=child_name,
                        is_redacted=False,
                        placement_type=ep.placement_type,
                        start_date=ep.start_date,
                        end_date=ep.end_date,
                        duration_days=duration,
                        status=ep.status,
                        discharge_reason=ep.discharge_episode.discharge_reason if ep.discharge_episode else None,
                    )
                )

        return items
