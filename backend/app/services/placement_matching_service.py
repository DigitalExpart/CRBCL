"""Placement Matching Decision-Support Service (Sprint 3).

Provides transparent, explainable decision-support matching between children and eligible Resource Homes.
IMPORTANT:
- Assistive only: the system NEVER autonomously places a child.
- Final placements remain human decisions via authorized PlacementEpisode workflows.
- Capacity locking and concurrency rules are preserved.
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit.service import AuditService
from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.placement_matching import (
    ChildPlacementProfile,
    PlacementMatchCandidate,
    PlacementMatchFactor,
    PlacementMatchResponse,
)


class PlacementMatchingService:
    """Assistive placement matching decision support service."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm = PermissionService(session)
        self.audit = AuditService(session)

    async def _require_matching_permission(self, user_id: uuid.UUID) -> None:
        if not await self.perm.user_has_permission(user_id, Permissions.RESOURCE_MATCHING_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to access placement matching decision support.",
            )

    async def evaluate_matches(
        self, profile: ChildPlacementProfile, user: User
    ) -> PlacementMatchResponse:
        """Evaluate candidate Resource Homes against child placement criteria with explainable factors."""
        await self._require_matching_permission(user.id)

        # Audit match search
        await self.audit.log(
            user_id=user.id,
            action="placement_matching.evaluate",
            resource_type="placement_matching",
            resource_id=profile.child_id or uuid.uuid4(),
            details={"age": profile.age, "sibling_group_size": profile.sibling_group_size},
        )

        today = date.today()

        # Query all non-deleted, non-archived placement homes with their active licenses and visits
        stmt = (
            select(PlacementHome)
            .where(
                PlacementHome.deleted_at.is_(None),
                PlacementHome.is_archived.is_(False),
            )
            .options(
                selectinload(PlacementHome.licenses),
                selectinload(PlacementHome.background_checks),
                selectinload(PlacementHome.visits),
                selectinload(PlacementHome.trainings),
            )
        )
        res = await self.session.execute(stmt)
        homes = list(res.scalars().all())

        eligible_candidates: list[PlacementMatchCandidate] = []
        excluded_candidates: list[PlacementMatchCandidate] = []

        for home in homes:
            # 1. Calculate active occupancy
            occ_stmt = select(func.count(PlacementEpisode.id)).where(
                PlacementEpisode.placement_home_id == home.id,
                PlacementEpisode.status == "ACTIVE",
                PlacementEpisode.deleted_at.is_(None),
            )
            occ_res = await self.session.execute(occ_stmt)
            active_occupancy = int(occ_res.scalar() or 0)
            available_beds = max(0, home.total_capacity - active_occupancy)

            factors: list[PlacementMatchFactor] = []
            exclusion_reasons: list[str] = []
            warnings: list[str] = []
            compatibility_notes: list[str] = []

            # 2. Check Home Operational Status
            if home.status != "ACTIVE":
                exclusion_reasons.append(f"Home operational status is '{home.status}' (must be ACTIVE)")
                factors.append(
                    PlacementMatchFactor(
                        factor_key="home_status",
                        name="Operational Status",
                        status="FAIL",
                        explanation=f"Home status is {home.status}.",
                    )
                )
            else:
                factors.append(
                    PlacementMatchFactor(
                        factor_key="home_status",
                        name="Operational Status",
                        status="PASS",
                        explanation="Home is currently in active operational status.",
                    )
                )

            # 3. Check Licensing Status & Active License
            active_license = next(
                (lic for lic in home.licenses if lic.status == "ACTIVE" and lic.deleted_at is None),
                None,
            )
            if not active_license or home.licensing_status not in ["ACTIVE", "STANDARD_FOSTER"]:
                if home.licensing_status == "PROVISIONAL":
                    warnings.append("Home holds a provisional license requiring supervisory review.")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="license_status",
                            name="Licensing Status",
                            status="WARNING",
                            explanation=f"Provisional license ({active_license.license_number if active_license else 'None'}).",
                        )
                    )
                else:
                    exclusion_reasons.append(f"Home licensing status is '{home.licensing_status}' (no valid active license)")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="license_status",
                            name="Licensing Status",
                            status="FAIL",
                            explanation=f"Invalid licensing status: {home.licensing_status}.",
                        )
                    )
            else:
                if active_license.expiry_date < today:
                    exclusion_reasons.append(f"Active license expired on {active_license.expiry_date}")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="license_expiry",
                            name="License Validity",
                            status="FAIL",
                            explanation=f"License {active_license.license_number} expired on {active_license.expiry_date}.",
                        )
                    )
                else:
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="license_status",
                            name="Licensing Status",
                            status="PASS",
                            explanation=f"Valid active license {active_license.license_number} (expires {active_license.expiry_date}).",
                        )
                    )

            # 4. Check Available Capacity & Sibling Group Capacity
            needed_beds = profile.sibling_group_size
            if available_beds < needed_beds:
                exclusion_reasons.append(
                    f"Insufficient capacity: home has {available_beds} available bed(s), but {needed_beds} needed."
                )
                factors.append(
                    PlacementMatchFactor(
                        factor_key="capacity",
                        name="Capacity & Sibling Bed Availability",
                        status="FAIL",
                        explanation=f"Capacity {home.total_capacity}, active {active_occupancy}, available {available_beds} < needed {needed_beds}.",
                    )
                )
            else:
                factors.append(
                    PlacementMatchFactor(
                        factor_key="capacity",
                        name="Capacity & Sibling Bed Availability",
                        status="PASS",
                        explanation=f"{available_beds} bed(s) available for {needed_beds} child(ren).",
                    )
                )
                if needed_beds > 1:
                    compatibility_notes.append(f"Accommodates full sibling group of {needed_beds} children together.")

            # 5. Check Age Compatibility
            min_age = active_license.min_age if (active_license and active_license.min_age is not None) else 0
            max_age = active_license.max_age if (active_license and active_license.max_age is not None) else 18
            if profile.age < min_age or profile.age > max_age:
                exclusion_reasons.append(
                    f"Child age ({profile.age}) is outside home's approved licensing age band ({min_age}-{max_age} years)."
                )
                factors.append(
                    PlacementMatchFactor(
                        factor_key="age_band",
                        name="Approved Age Range",
                        status="FAIL",
                        explanation=f"Child age {profile.age} is outside licensed range {min_age}-{max_age}.",
                    )
                )
            else:
                factors.append(
                    PlacementMatchFactor(
                        factor_key="age_band",
                        name="Approved Age Range",
                        status="PASS",
                        explanation=f"Child age {profile.age} is within approved range {min_age}-{max_age}.",
                    )
                )

            # 6. Check Home Type Preferences
            if profile.preferred_home_types:
                if home.home_type in profile.preferred_home_types:
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="home_type",
                            name="Home Type Match",
                            status="PASS",
                            explanation=f"Home type '{home.home_type}' matches preferred types.",
                        )
                    )
                    compatibility_notes.append(f"Matches preferred placement type '{home.home_type}'.")
                else:
                    warnings.append(f"Home type '{home.home_type}' does not match preferred types ({', '.join(profile.preferred_home_types)}).")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="home_type",
                            name="Home Type Match",
                            status="WARNING",
                            explanation=f"Home type '{home.home_type}' is not in preferred list.",
                        )
                    )

            # 7. Check Clearance Compliance
            expired_clearances = [
                chk for chk in home.background_checks
                if chk.deleted_at is None and (
                    chk.renewal_status == "EXPIRED" or (chk.expiry_date and chk.expiry_date < today)
                )
            ]
            if expired_clearances:
                exclusion_reasons.append(f"Home has {len(expired_clearances)} expired background check(s)/screening(s).")
                factors.append(
                    PlacementMatchFactor(
                        factor_key="clearance_compliance",
                        name="Caregiver Screenings & Clearances",
                        status="FAIL",
                        explanation=f"{len(expired_clearances)} screening record(s) currently expired.",
                    )
                )
            else:
                factors.append(
                    PlacementMatchFactor(
                        factor_key="clearance_compliance",
                        name="Caregiver Screenings & Clearances",
                        status="PASS",
                        explanation="All recorded caregiver clearances and screenings are currently up to date.",
                    )
                )

            # 8. Check Overdue Corrective Actions from Inspections
            overdue_actions = [
                v for v in home.visits
                if v.deleted_at is None and (
                    v.corrective_action_status == "OVERDUE"
                    or (
                        v.corrective_action_status in ["REQUIRED", "PENDING", "IN_PROGRESS"]
                        and v.corrective_action_due_date
                        and v.corrective_action_due_date < today
                    )
                )
            ]
            if overdue_actions:
                exclusion_reasons.append(f"Home has {len(overdue_actions)} overdue inspection corrective action(s).")
                factors.append(
                    PlacementMatchFactor(
                        factor_key="inspection_compliance",
                        name="Physical Safety & Inspection Compliance",
                        status="FAIL",
                        explanation=f"{len(overdue_actions)} corrective action(s) are past due.",
                    )
                )
            else:
                factors.append(
                    PlacementMatchFactor(
                        factor_key="inspection_compliance",
                        name="Physical Safety & Inspection Compliance",
                        status="PASS",
                        explanation="No overdue corrective actions or physical safety holds.",
                    )
                )

            # 8b. Home Placement Restrictions & Intake Criteria Review
            home_meta = home.metadata_ or {}
            home_restrictions = home_meta.get("placement_restrictions", []) if isinstance(home_meta, dict) else []
            intake_notes = (home.intake_criteria_notes or "").strip()

            # Structured deterministic restrictions
            has_structured_conflict = False
            if profile.gender and isinstance(home_restrictions, list):
                if profile.gender.upper() == "MALE" and "FEMALE_ONLY" in [str(r).upper() for r in home_restrictions]:
                    has_structured_conflict = True
                    exclusion_reasons.append("Home has structured restriction: FEMALE_ONLY (conflicts with male child).")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="placement_restrictions",
                            name="Placement Restrictions",
                            status="FAIL",
                            explanation="Home restriction excludes male placements.",
                        )
                    )
                elif profile.gender.upper() == "FEMALE" and "MALE_ONLY" in [str(r).upper() for r in home_restrictions]:
                    has_structured_conflict = True
                    exclusion_reasons.append("Home has structured restriction: MALE_ONLY (conflicts with female child).")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="placement_restrictions",
                            name="Placement Restrictions",
                            status="FAIL",
                            explanation="Home restriction excludes female placements.",
                        )
                    )

            if not has_structured_conflict:
                # Free-text intake criteria/restrictions must NOT be parsed by AI/regex as green light.
                # Flag as MANUAL_REVIEW_REQUIRED.
                if intake_notes:
                    warnings.append(f"Caregiver has documented intake/placement criteria: '{intake_notes}'.")
                    compatibility_notes.append(
                        f"MANUAL_REVIEW_REQUIRED: Placement criteria recorded ('{intake_notes}'). Authorized review required before referral."
                    )
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="placement_restrictions",
                            name="Placement Restrictions Review",
                            status="WARNING",
                            explanation="Documented intake criteria present; requires manual review by placement decision-maker.",
                        )
                    )
                else:
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="placement_restrictions",
                            name="Placement Restrictions Review",
                            status="PASS",
                            explanation="No restrictive intake criteria or placement limits recorded.",
                        )
                    )

            # 9. Cultural / Community Considerations
            if profile.indigenous_community:
                home_communities = [c.strip().lower() for c in (home.community or "").split(",") if c.strip()]
                target_community = profile.indigenous_community.strip().lower()
                if target_community in home_communities or target_community in (home.notes or "").lower():
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="cultural_match",
                            name="Cultural & Community Connection",
                            status="PASS",
                            explanation=f"Home has documented connection to {profile.indigenous_community}.",
                        )
                    )
                    compatibility_notes.append(f"Cultural/community alignment with {profile.indigenous_community}.")
                else:
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="cultural_match",
                            name="Cultural & Community Connection",
                            status="INFO",
                            explanation="Different geographic or community affiliation; cultural support plan required if selected.",
                        )
                    )

            # 10. Medical & Accessibility Complexity
            if profile.medical_complexity:
                med_supported = home_meta.get("medical_complexity_supported", False)
                if med_supported or "medical" in (home.intake_criteria_notes or "").lower():
                    compatibility_notes.append("Home has recorded experience or capability for medical complexity.")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="medical_support",
                            name="Medical Support Capability",
                            status="PASS",
                            explanation="Caregivers have recorded readiness for medical complexity.",
                        )
                    )
                else:
                    warnings.append("Child has medical complexity; home has not specifically recorded specialized medical readiness.")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="medical_support",
                            name="Medical Support Capability",
                            status="WARNING",
                            explanation="No explicit specialized medical endorsement recorded.",
                        )
                    )

            # 11. Geographic / Service Area
            if profile.preferred_location:
                if profile.preferred_location.lower() in home.city.lower() or profile.preferred_location.lower() in (home.community or "").lower():
                    compatibility_notes.append(f"Located in preferred location area ({home.city}).")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="location",
                            name="Geographic Proximity",
                            status="PASS",
                            explanation=f"Home is located in {home.city}.",
                        )
                    )
                else:
                    warnings.append(f"Home is located in {home.city}, outside preferred location '{profile.preferred_location}'.")
                    factors.append(
                        PlacementMatchFactor(
                            factor_key="location",
                            name="Geographic Proximity",
                            status="WARNING",
                            explanation=f"Home is in {home.city}.",
                        )
                    )

            # Determine eligibility and compatibility level
            is_eligible = len(exclusion_reasons) == 0
            if not is_eligible:
                compatibility_level = "INELIGIBLE"
            elif len(warnings) == 0:
                compatibility_level = "HIGH"
            elif len(warnings) <= 2:
                compatibility_level = "MODERATE"
            else:
                compatibility_level = "LOW"

            candidate = PlacementMatchCandidate(
                home_id=home.id,
                home_code=home.home_code,
                home_name=home.name,
                home_type=home.home_type,
                status=home.status,
                licensing_status=home.licensing_status,
                total_capacity=home.total_capacity,
                active_occupancy=active_occupancy,
                available_beds=available_beds,
                community=home.community,
                city=home.city,
                primary_caregiver_name=home.primary_caregiver_name,
                compatibility_level=compatibility_level,
                is_eligible=is_eligible,
                factors=factors,
                exclusion_reasons=exclusion_reasons,
                compatibility_notes=compatibility_notes,
                warnings=warnings,
            )

            if is_eligible:
                eligible_candidates.append(candidate)
            else:
                excluded_candidates.append(candidate)

        # Sort eligible candidates: HIGH first, then MODERATE, then LOW, then by available beds desc
        order_map = {"HIGH": 0, "MODERATE": 1, "LOW": 2}
        eligible_candidates.sort(key=lambda c: (order_map.get(c.compatibility_level, 3), -c.available_beds))

        return PlacementMatchResponse(
            child_profile=profile,
            total_homes_evaluated=len(homes),
            eligible_candidates=eligible_candidates,
            excluded_candidates=excluded_candidates,
        )
