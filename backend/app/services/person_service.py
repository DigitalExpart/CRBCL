"""Comprehensive Person service managing canonical identities, numeric IDs, profile aggregation, and security boundaries."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.case import Case
from app.models.case_management import CaseAssignment, CasePerson
from app.models.client import Client
from app.models.document import Document
from app.models.medical import (
    ClientAllergy,
    ClientMedicalCondition,
    ClientMedicalProfile,
    ClientMedication,
)
from app.models.person import (
    Person,
    PersonAddress,
    PersonCulturalProfile,
    PersonPhysicalDescription,
)
from app.models.placement import (
    BackgroundCheck,
    InHomePlacement,
    PlacementEpisode,
)
from app.models.provider import ClientProvider
from app.models.referral import Referral, ReferralPerson
from app.models.relationship import (
    FamilyRelationship,
    Household,
    HouseholdMembership,
)
from app.models.role import Role, UserRole
from app.models.school import ClientSchoolEnrolment
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.person_repo import PersonRepository
from app.schemas.person import (
    PersonBackgroundCheckSummary,
    PersonCandidateResponse,
    PersonCaseSummary,
    PersonCreate,
    PersonDocumentSummary,
    PersonDuplicateCheckRequest,
    PersonDuplicateCheckResponse,
    PersonHouseholdSummary,
    PersonMedicalSummary,
    PersonPlacementSummary,
    PersonProfileResponse,
    PersonReferralSummary,
    PersonRelationshipSummary,
    PersonResponse,
    PersonTimelineSummary,
    PersonUpdate,
)
from app.services.file_security import generate_signed_file_url, validate_file_upload
from app.storage.service import StorageService


class PersonService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.person_repo = PersonRepository(db)

    async def get_person_or_404(self, person_id: uuid.UUID) -> Person:
        person = await self.person_repo.get_full(person_id)
        if not person or person.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "PERSON_NOT_FOUND", "message": "Person identity record not found"}},
            )
        return person

    async def create_person(self, payload: PersonCreate, current_user_id: uuid.UUID | None = None) -> Person:
        """
        Create canonical Person record with an automatically assigned, permanent,
        strictly numeric 10-digit CRBCL Person ID.
        """
        # Concurrency-safe atomic generation
        numeric_id = await self.person_repo.generate_person_id_number()

        data = payload.model_dump(exclude={"physical_description", "address", "cultural_profile"})
        data["person_id_number"] = numeric_id
        if current_user_id:
            data["created_by"] = current_user_id
            data["updated_by"] = current_user_id

        person = Person(**data)
        self.db.add(person)
        await self.db.flush()

        # Handle nested sub-profiles if provided in creation form
        if payload.physical_description:
            phys_data = payload.physical_description.model_dump(exclude_unset=True)
            phys = PersonPhysicalDescription(person_id=person.id, **phys_data)
            self.db.add(phys)

        if payload.address:
            addr_data = payload.address.model_dump(exclude_unset=True)
            addr = PersonAddress(person_id=person.id, **addr_data)
            self.db.add(addr)

        if payload.cultural_profile:
            cult_data = payload.cultural_profile.model_dump(exclude_unset=True)
            cult = PersonCulturalProfile(person_id=person.id, **cult_data)
            self.db.add(cult)

        await self.db.flush()
        return await self.get_person_or_404(person.id)

    async def assert_person_role_authorized(self, current_user: User, action_label: str = "access") -> set[str]:
        """
        Verify that user does not have an administrative/governance role that lacks
        operational authority over canonical Person records (e.g. IT Admin, Board Member, Front Desk).
        """
        if not current_user or not current_user.is_active or current_user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "UNAUTHENTICATED", "message": "Authentication required."}},
            )

        user_roles_stmt = (
            select(Role.key)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == current_user.id, Role.is_active == True)  # noqa: E712
        )
        user_roles_res = await self.db.execute(user_roles_stmt)
        user_roles = set(user_roles_res.scalars().all())

        if "it_admin" in user_roles and not any(r in user_roles for r in ["executive_director", "ceo"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "ROLE_ACCESS_DENIED", "message": f"IT Administrators cannot {action_label} Person records."}},
            )
        if "board_member" in user_roles and not any(r in user_roles for r in ["executive_director", "ceo"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "ROLE_ACCESS_DENIED", "message": f"Board members cannot {action_label} Person records."}},
            )
        if "front_desk" in user_roles and not any(r in user_roles for r in ["executive_director", "ceo", "caseworker", "supervisor"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"error": {"code": "ROLE_ACCESS_DENIED", "message": f"Front desk staff cannot {action_label} Person records."}},
            )
        return user_roles

    async def check_person_operational_access(
        self, person_id: uuid.UUID, current_user: User, write: bool = False
    ) -> None:
        """
        Verify that current_user has an authorized operational relationship to person_id.
        Prevents organization-wide IDOR by ensuring generic caseworker permissions
        do not automatically grant access to arbitrary canonical Person profiles.

        Access is authorized if:
        1. User is Executive Leadership (CEO, Executive Director); OR
        2. User directly created this person record; OR
        3. Person participates in at least one Case accessible to the user
           (user is assigned worker, creator, on active CaseAssignment, or case is in user's accessible team scope,
            and user is NOT restricted from that case); OR
        4. Person is a Client accessible to the user (assigned worker, creator, or team scope); OR
        5. Person participates in a Referral accessible to the user (assigned worker, creator, or team scope).

        If Person's only linked Cases are all restricted from the user:
        raises HTTP 403 Forbidden (code: CASE_RESTRICTION_ACTIVE).

        If Person has no operational relationship to the user:
        raises HTTP 403 Forbidden (code: PERSON_ACCESS_DENIED).
        """
        user_roles = await self.assert_person_role_authorized(current_user, "access")
        perm_service = PermissionService(self.db)

        # Executive Leadership oversight (approved executive leadership roles only)
        if any(r in user_roles for r in ["executive_director", "ceo"]):
            return

        person = await self.get_person_or_404(person_id)

        # 1. Direct creator
        if person.created_by == current_user.id:
            return

        # 2. Case Participation
        case_rows_stmt = (
            select(CasePerson, Case)
            .join(Case, CasePerson.case_id == Case.id)
            .where(
                CasePerson.person_id == person_id,
                CasePerson.deleted_at.is_(None),
                Case.deleted_at.is_(None),
            )
        )
        case_rows = (await self.db.execute(case_rows_stmt)).all()
        has_case_link = bool(case_rows)
        all_cases_restricted = has_case_link
        has_accessible_case = False

        user_team_ids = await perm_service.get_user_accessible_team_ids(current_user.id)

        for _cp, c in case_rows:
            is_restricted = await perm_service.is_user_restricted_from_case(current_user.id, c.id)
            if not is_restricted:
                all_cases_restricted = False
                is_linked_worker = (
                    c.assigned_worker_id == current_user.id
                    or c.created_by == current_user.id
                )
                if not is_linked_worker:
                    assign_stmt = select(CaseAssignment).where(
                        CaseAssignment.case_id == c.id,
                        CaseAssignment.user_id == current_user.id,
                        CaseAssignment.is_active == True,  # noqa: E712
                    )
                    assign_res = await self.db.execute(assign_stmt)
                    if assign_res.scalar_one_or_none():
                        is_linked_worker = True

                team_accessible = (
                    c.assigned_team_id is not None
                    and user_team_ids is not None
                    and c.assigned_team_id in user_team_ids
                )

                if is_linked_worker or team_accessible:
                    has_accessible_case = True
                    break

        if has_accessible_case:
            return

        # If Person occurs only in cases that are all restricted for this user
        if has_case_link and all_cases_restricted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "CASE_RESTRICTION_ACTIVE",
                        "message": "Access denied: active conflict-of-interest restriction prevents accessing records associated with this individual.",
                    }
                },
            )

        # 3. Client Participation
        client_stmt = select(Client).where(Client.person_id == person_id, Client.deleted_at.is_(None))
        clients = (await self.db.execute(client_stmt)).scalars().all()
        for cl in clients:
            if getattr(cl, "assigned_worker_id", None) == current_user.id or cl.created_by == current_user.id:
                return
            if cl.assigned_team_id is not None and user_team_ids is not None and cl.assigned_team_id in user_team_ids:
                return

        # 4. Referral Participation
        ref_stmt = (
            select(ReferralPerson, Referral)
            .join(Referral, ReferralPerson.referral_id == Referral.id)
            .where(
                ReferralPerson.person_id == person_id,
                Referral.deleted_at.is_(None),
            )
        )
        refs = (await self.db.execute(ref_stmt)).all()
        for _rp, r in refs:
            if r.assigned_worker_id == current_user.id or r.created_by == current_user.id:
                return
            if r.assigned_team_id is not None and user_team_ids is not None and r.assigned_team_id in user_team_ids:
                return

        # No authorized operational relationship found -> IDOR block
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "PERSON_ACCESS_DENIED",
                    "message": "Access denied: You do not have an authorized operational relationship to view or modify this individual's records.",
                }
            },
        )

    async def update_person(
        self, person_id: uuid.UUID, payload: PersonUpdate, current_user: User | None = None
    ) -> Person:
        """Update Person demographics and sub-profiles. Person ID is permanent and immutable."""
        person = await self.get_person_or_404(person_id)

        # Enforce authorized operational relationship / IDOR security
        if current_user:
            await self.check_person_operational_access(person_id, current_user, write=True)

        update_dict = payload.model_dump(exclude_unset=True, exclude={"physical_description", "cultural_profile"})
        # Person ID and photo references cannot be manually modified via generic patch
        update_dict.pop("person_id_number", None)
        update_dict.pop("id", None)
        update_dict.pop("photo_url", None)
        update_dict.pop("photo_document_id", None)

        for field, val in update_dict.items():
            setattr(person, field, val)

        if current_user:
            person.updated_by = current_user.id

        # Update physical description if provided
        if payload.physical_description is not None:
            phys_data = payload.physical_description.model_dump(exclude_unset=True)
            if person.physical_description:
                for k, v in phys_data.items():
                    setattr(person.physical_description, k, v)
            else:
                person.physical_description = PersonPhysicalDescription(person_id=person.id, **phys_data)

        # Update cultural profile if provided
        if payload.cultural_profile is not None:
            cult_data = payload.cultural_profile.model_dump(exclude_unset=True)
            if person.cultural_profile:
                for k, v in cult_data.items():
                    setattr(person.cultural_profile, k, v)
            else:
                person.cultural_profile = PersonCulturalProfile(person_id=person.id, **cult_data)

        await self.db.flush()
        loaded = await self.get_person_or_404(person.id)
        if loaded.photo_document_id:
            loaded.photo_url = generate_signed_file_url(loaded.photo_document_id, expiry_seconds=3600)
        return loaded

    async def upload_photo(
        self, person_id: uuid.UUID, filename: str, content: bytes, content_type: str, current_user: User
    ) -> str:
        """Secure photo upload associated with Person."""
        if not content_type.lower().startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Profile photos must be an image (JPEG, PNG, WebP).",
            )

        try:
            validate_file_upload(filename, content_type, len(content))
        except ValueError as err:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err

        person = await self.get_person_or_404(person_id)

        # Enforce authorized operational relationship / IDOR security
        await self.check_person_operational_access(person_id, current_user, write=True)

        storage_service = StorageService(self.db)
        doc = await storage_service.store_document(
            filename=filename,
            content=content,
            content_type=content_type,
            uploaded_by=current_user.id,
            entity_type="person",
            entity_id=person.id,
            description=f"Profile photo for {person.first_name} {person.last_name}",
        )

        person.photo_document_id = doc.id
        person.photo_url = None
        await self.db.flush()
        fresh_signed_url = generate_signed_file_url(doc.id, expiry_seconds=3600)
        return fresh_signed_url

    async def check_duplicates(self, criteria: PersonDuplicateCheckRequest) -> PersonDuplicateCheckResponse:
        """Run fuzzy candidate matching across existing canonical identities."""
        results = await self.person_repo.find_duplicates(
            first_name=criteria.first_name,
            last_name=criteria.last_name,
            date_of_birth=criteria.date_of_birth,
            treaty_number=criteria.treaty_number,
            health_card_number=criteria.health_card_number,
            phone=criteria.phone,
            email=criteria.email,
            person_id_number=criteria.person_id_number,
        )

        candidates = [
            PersonCandidateResponse(
                person_id=p.id,
                person_id_number=p.person_id_number,
                first_name=p.first_name,
                last_name=p.last_name,
                date_of_birth=str(p.date_of_birth) if p.date_of_birth else None,
                similarity_score=score,
                matching_factors=factors,
            )
            for p, score, factors in results
        ]

        return PersonDuplicateCheckResponse(
            has_potential_duplicates=len(candidates) > 0,
            candidates=candidates,
        )

    async def get_comprehensive_profile(self, person_id: uuid.UUID, current_user: User) -> PersonProfileResponse:
        """
        Consolidate canonical Person identity with all authoritative relational records:
        cases, referrals, family relationships, households, placements, background checks,
        documents, timeline, and permission-checked medical/school/provider data.
        """
        person = await self.get_person_or_404(person_id)

        # Enforce authorized operational relationship / IDOR security
        await self.check_person_operational_access(person_id, current_user, write=False)

        # Dynamically generate fresh signed photo URL from durable photo_document_id
        if person.photo_document_id:
            person.photo_url = generate_signed_file_url(person.photo_document_id, expiry_seconds=3600)

        perm_service = PermissionService(self.db)
        user_perms = await perm_service.get_user_permissions(current_user.id)

        # 1. Cases participated in (filter out any restricted cases)
        cases_stmt = (
            select(CasePerson, Case)
            .join(Case, CasePerson.case_id == Case.id)
            .where(CasePerson.person_id == person.id, CasePerson.deleted_at.is_(None), Case.deleted_at.is_(None))
            .order_by(Case.created_at.desc())
        )
        cases_res = await self.db.execute(cases_stmt)
        all_case_rows = cases_res.all()
        cases_list = []

        for cp, c in all_case_rows:
            is_restricted = await perm_service.is_user_restricted_from_case(current_user.id, c.id)
            if not is_restricted:
                cases_list.append(
                    PersonCaseSummary(
                        case_id=c.id,
                        case_number=c.case_number,
                        title=c.title,
                        case_type=c.case_type,
                        stage=c.stage,
                        role_in_case=cp.role,
                        relationship_to_subject=cp.relationship_to_subject,
                        is_primary=cp.is_primary,
                        start_date=cp.start_date,
                        notes=cp.notes,
                    )
                )

        # 2. Referrals / Intakes participated in
        refs_stmt = (
            select(ReferralPerson, Referral)
            .join(Referral, ReferralPerson.referral_id == Referral.id)
            .where(ReferralPerson.person_id == person.id, Referral.deleted_at.is_(None))
            .order_by(Referral.created_at.desc())
        )
        refs_res = await self.db.execute(refs_stmt)
        referrals_list = [
            PersonReferralSummary(
                referral_id=ref.id,
                referral_number=ref.referral_number,
                status=ref.status,
                role=rp.role,
                relationship_to_child=rp.relationship_to_child,
                received_date=ref.received_date,
            )
            for rp, ref in refs_res.all()
        ]

        # 3. Family Memberships and Directional Interpersonal Relationships
        rel_stmt = (
            select(FamilyRelationship, Person)
            .outerjoin(
                Person,
                or_(
                    (FamilyRelationship.person_b_id == Person.id) & (FamilyRelationship.person_a_id == person.id),
                    (FamilyRelationship.person_a_id == Person.id) & (FamilyRelationship.person_b_id == person.id),
                ),
            )
            .where(
                or_(FamilyRelationship.person_a_id == person.id, FamilyRelationship.person_b_id == person.id),
                FamilyRelationship.is_active.is_(True),
            )
        )
        rel_res = await self.db.execute(rel_stmt)
        relationships_list = []
        for fr, other_p in rel_res.all():
            if other_p and other_p.id != person.id:
                relationships_list.append(
                    PersonRelationshipSummary(
                        relationship_id=fr.id,
                        target_person_id=other_p.id,
                        target_person_id_number=other_p.person_id_number,
                        target_person_name=f"{other_p.first_name} {other_p.last_name}",
                        relationship_type=fr.relationship_type,
                        is_active=fr.is_active,
                        family_id=fr.family_id,
                    )
                )

        # 4. Household Memberships
        hh_stmt = (
            select(HouseholdMembership, Household)
            .join(Household, HouseholdMembership.household_id == Household.id)
            .where(HouseholdMembership.person_id == person.id, HouseholdMembership.is_current.is_(True))
        )
        hh_res = await self.db.execute(hh_stmt)
        households_list = [
            PersonHouseholdSummary(
                household_id=h.id,
                household_name=h.name,
                address=h.address_line_1,
                city=h.city,
                province=h.province,
                is_active=hm.is_current,
            )
            for hm, h in hh_res.all()
        ]

        # 5. Out-of-Home & In-Home Placements (respect case restrictions)
        placements_list = []
        ep_stmt = (
            select(PlacementEpisode, Case)
            .join(Case, PlacementEpisode.case_id == Case.id)
            .where(PlacementEpisode.child_id == person.id, PlacementEpisode.deleted_at.is_(None))
            .order_by(PlacementEpisode.start_date.desc())
        )
        ep_res = await self.db.execute(ep_stmt)
        for ep, c in ep_res.all():
            if not await perm_service.is_user_restricted_from_case(current_user.id, c.id):
                placements_list.append(
                    PersonPlacementSummary(
                        episode_id=ep.id,
                        case_id=c.id,
                        case_number=c.case_number,
                        placement_type=ep.placement_type,
                        status=ep.status,
                        start_date=ep.start_date,
                        end_date=ep.end_date,
                        provider_name=ep.provider_name,
                    )
                )

        ih_stmt = (
            select(InHomePlacement, Case)
            .join(Case, InHomePlacement.case_id == Case.id)
            .where(
                or_(InHomePlacement.child_id == person.id, InHomePlacement.primary_caregiver_id == person.id),
                InHomePlacement.deleted_at.is_(None),
            )
            .order_by(InHomePlacement.start_date.desc())
        )
        ih_res = await self.db.execute(ih_stmt)
        for ih, c in ih_res.all():
            if not await perm_service.is_user_restricted_from_case(current_user.id, c.id):
                placements_list.append(
                    PersonPlacementSummary(
                        episode_id=ih.id,
                        case_id=c.id,
                        case_number=c.case_number,
                        placement_type=f"In-Home ({ih.supervision_level})",
                        status=ih.status,
                        start_date=ih.start_date,
                        end_date=ih.end_date,
                        provider_name="In-Home Customary Care",
                    )
                )

        # 6. Background Checks (gated by BACKGROUND_CHECK_READ)
        bg_list = []
        if (
            Permissions.BACKGROUND_CHECK_READ in user_perms
            or Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ in user_perms
        ):
            bg_stmt = select(BackgroundCheck).where(
                BackgroundCheck.subject_id == person.id, BackgroundCheck.deleted_at.is_(None)
            )
            bg_res = await self.db.execute(bg_stmt)
            bg_list = [
                PersonBackgroundCheckSummary(
                    id=bg.id,
                    check_type=bg.check_type,
                    status=bg.status,
                    request_date=bg.request_date,
                    completion_date=bg.completion_date,
                    expiry_date=bg.expiry_date,
                    is_eligible_for_placement=bg.is_eligible_for_placement,
                )
                for bg in bg_res.scalars().all()
            ]

        # 7. Timeline events (gated by TIMELINE_READ)
        timeline_list = []
        if Permissions.TIMELINE_READ in user_perms:
            timeline_stmt = (
                select(TimelineEvent)
                .where(
                    or_(
                        (TimelineEvent.entity_type == "person") & (TimelineEvent.entity_id == person.id),
                        TimelineEvent.client_id == person.id,
                    )
                )
                .order_by(TimelineEvent.occurred_at.desc())
                .limit(50)
            )
            tl_res = await self.db.execute(timeline_stmt)
            timeline_list = [
                PersonTimelineSummary(
                    id=t.id,
                    event_type=t.event_type,
                    title=t.title,
                    description=t.description,
                    occurred_at=t.occurred_at,
                )
                for t in tl_res.scalars().all()
            ]

        # 8. Documents (gated by DOCUMENT_READ)
        documents_list = []
        if (
            Permissions.DOCUMENT_READ in user_perms
            or Permissions.CLIENT_DOCUMENTS_READ in user_perms
        ):
            doc_stmt = (
                select(Document)
                .where(
                    or_(
                        (Document.entity_type == "person") & (Document.entity_id == person.id),
                        (Document.entity_type == "client") & (Document.entity_id == person.id),
                    ),
                    Document.deleted_at.is_(None),
                )
                .order_by(Document.created_at.desc())
            )
            doc_res = await self.db.execute(doc_stmt)
            documents_list = [
                PersonDocumentSummary(
                    id=d.id,
                    filename=d.filename,
                    content_type=d.content_type,
                    size_bytes=d.size_bytes,
                    download_url=generate_signed_file_url(d.id, expiry_seconds=3600),
                    created_at=d.created_at,
                )
                for d in doc_res.scalars().all()
            ]

        # 9. Linked Client Context & Permission-Gated Health/School/Provider Data
        client_stmt = select(Client).where(
            or_(Client.person_id == person.id, Client.id == person.id),
            Client.deleted_at.is_(None),
        )
        client_res = await self.db.execute(client_stmt)
        linked_client = client_res.scalar_one_or_none()

        medical_summary: PersonMedicalSummary | None = None
        schools_list: list[dict[str, Any]] = []
        providers_list: list[dict[str, Any]] = []

        if linked_client:
            # Enforce Permission boundary: Only users with CLIENT_MEDICAL_READ can access medical/health
            if Permissions.CLIENT_MEDICAL_READ in user_perms:
                med_prof_stmt = select(ClientMedicalProfile).where(ClientMedicalProfile.client_id == linked_client.id)
                med_prof = (await self.db.execute(med_prof_stmt)).scalar_one_or_none()

                allergies_stmt = select(ClientAllergy).where(ClientAllergy.client_id == linked_client.id)
                allergies = (await self.db.execute(allergies_stmt)).scalars().all()

                cond_stmt = select(ClientMedicalCondition).where(ClientMedicalCondition.client_id == linked_client.id)
                conditions = (await self.db.execute(cond_stmt)).scalars().all()

                meds_stmt = select(ClientMedication).where(ClientMedication.client_id == linked_client.id)
                meds = (await self.db.execute(meds_stmt)).scalars().all()

                medical_summary = PersonMedicalSummary(
                    dental_notes=med_prof.dental_notes if med_prof else None,
                    mental_health_notes=med_prof.mental_health_notes if med_prof else None,
                    chemical_dependency_history=med_prof.chemical_dependency_history if med_prof else None,
                    general_notes=med_prof.general_notes if med_prof else None,
                    primary_physician_name=med_prof.primary_physician_name if med_prof else None,
                    primary_physician_phone=med_prof.primary_physician_phone if med_prof else None,
                    allergies=[
                        {"id": str(a.id), "allergen": a.allergen, "severity": a.severity, "reaction": a.reaction}
                        for a in allergies
                    ],
                    conditions=[
                        {"id": str(c.id), "condition_name": c.condition_name, "is_chronic": c.is_chronic}
                        for c in conditions
                    ],
                    medications=[
                        {"id": str(m.id), "medication_name": m.medication_name, "dosage": m.dosage, "frequency": m.frequency, "status": m.status}
                        for m in meds
                    ],
                )

            # Education & Schools
            if Permissions.CLIENT_SCHOOL_READ in user_perms or Permissions.CLIENT_READ in user_perms:
                sch_stmt = (
                    select(ClientSchoolEnrolment)
                    .options(selectinload(ClientSchoolEnrolment.school))
                    .where(ClientSchoolEnrolment.client_id == linked_client.id)
                )
                sch_res = await self.db.execute(sch_stmt)
                for se in sch_res.scalars().all():
                    schools_list.append({
                        "id": str(se.id),
                        "school_name": se.school.name if se.school else "Unknown School",
                        "grade_level": se.grade_level,
                        "is_current": se.is_current,
                        "has_iep": se.has_iep,
                    })

            # Providers
            prov_stmt = (
                select(ClientProvider)
                .options(selectinload(ClientProvider.provider))
                .where(ClientProvider.client_id == linked_client.id)
            )
            prov_res = await self.db.execute(prov_stmt)
            for cp in prov_res.scalars().all():
                providers_list.append({
                    "id": str(cp.id),
                    "provider_name": cp.provider.name if cp.provider else "Unknown Provider",
                    "provider_type": cp.provider.provider_type if cp.provider else "Specialist",
                    "role": cp.role,
                })

        return PersonProfileResponse(
            person=PersonResponse.model_validate(person),
            cases=cases_list,
            referrals=referrals_list,
            relationships=relationships_list,
            households=households_list,
            placements=placements_list,
            background_checks=bg_list,
            timeline=timeline_list,
            documents=documents_list,
            medical=medical_summary,
            schools=schools_list,
            providers=providers_list,
            client_id=linked_client.id if linked_client else None,
        )
