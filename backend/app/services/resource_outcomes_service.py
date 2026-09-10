"""Resource Unit Strategic Outcomes Service (Sprint 3).

Calculates authoritative strategic outcome indicators from real relational records:
growth, retention, recruitment conversion, placement stability, length of stay,
and cultural connection rates.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.placement import PlacementEpisode
from app.models.placement_home import PlacementHome, PlacementHomeLicense
from app.models.resource_complaint import ResourceComplaint
from app.models.resource_recruitment import RecruitmentState, ResourceRecruitment
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.schemas.resource_outcomes import StrategicOutcomesMetrics


class ResourceOutcomesService:
    """Domain service calculating authoritative strategic outcomes for the Resource Unit."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.perm = PermissionService(session)

    async def _require_outcomes_perm(self, user_id: uuid.UUID) -> None:
        if not await self.perm.user_has_permission(user_id, Permissions.RESOURCE_OUTCOMES_READ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to view strategic resource outcomes.",
            )

    async def get_strategic_outcomes(self, user: User) -> StrategicOutcomesMetrics:
        """Calculate live strategic metrics from authoritative relational data."""
        await self._require_outcomes_perm(user.id)

        today = date.today()
        year_start = date(today.year, 1, 1)

        # 1. Operational scale: Active homes & bed capacity
        homes_stmt = select(PlacementHome).where(
            PlacementHome.status == "ACTIVE",
            PlacementHome.deleted_at.is_(None),
            PlacementHome.is_archived.is_(False),
        )
        homes = list((await self.session.execute(homes_stmt)).scalars().all())
        active_homes_count = len(homes)
        total_capacity = sum(h.total_capacity for h in homes)

        # Active placements count
        active_episodes_stmt = select(func.count(PlacementEpisode.id)).where(
            PlacementEpisode.status == "ACTIVE",
            PlacementEpisode.deleted_at.is_(None),
        )
        occupied_beds = int((await self.session.execute(active_episodes_stmt)).scalar() or 0)
        available_beds = max(0, total_capacity - occupied_beds)

        # 2. Resource Home Growth YTD (authoritative license effective_date)
        new_approvals_stmt = (
            select(func.count(func.distinct(PlacementHomeLicense.placement_home_id)))
            .join(PlacementHome, PlacementHome.id == PlacementHomeLicense.placement_home_id)
            .where(
                PlacementHomeLicense.effective_date >= year_start,
                PlacementHomeLicense.status == "ACTIVE",
                PlacementHomeLicense.deleted_at.is_(None),
                PlacementHome.status == "ACTIVE",
                PlacementHome.deleted_at.is_(None),
            )
        )
        new_approvals = int((await self.session.execute(new_approvals_stmt)).scalar() or 0)

        # 3. Active Home Longevity (operational longevity of currently active homes)
        one_year_ago = datetime.utcnow() - timedelta(days=365)
        longevity_homes_stmt = select(func.count(PlacementHome.id)).where(
            PlacementHome.status == "ACTIVE",
            PlacementHome.created_at <= one_year_ago,
            PlacementHome.deleted_at.is_(None),
        )
        longevity_homes = int((await self.session.execute(longevity_homes_stmt)).scalar() or 0)
        longevity_pct = (
            round((longevity_homes / active_homes_count * 100.0), 1)
            if active_homes_count > 0
            else 100.0
        )

        # 4. Recruitment Conversion Rate & Average Days to Approval
        total_apps_stmt = select(func.count(ResourceRecruitment.id)).where(
            ResourceRecruitment.deleted_at.is_(None)
        )
        total_apps = int((await self.session.execute(total_apps_stmt)).scalar() or 0)

        approved_apps_stmt = select(ResourceRecruitment).where(
            ResourceRecruitment.current_state == RecruitmentState.APPROVED,
            ResourceRecruitment.deleted_at.is_(None),
        )
        approved_apps = list((await self.session.execute(approved_apps_stmt)).scalars().all())
        approved_count = len(approved_apps)

        conversion_pct = round((approved_count / total_apps * 100.0), 1) if total_apps > 0 else 0.0

        days_list = []
        for app in approved_apps:
            delta = (app.updated_at.date() - app.created_at.date()).days
            if delta >= 0:
                days_list.append(delta)
        avg_days_to_approval = round(sum(days_list) / len(days_list), 1) if days_list else 0.0

        # 5. Placement Stability (% of completed/active episodes without unplanned disruption)
        all_episodes_stmt = select(PlacementEpisode).where(PlacementEpisode.deleted_at.is_(None))
        all_episodes = list((await self.session.execute(all_episodes_stmt)).scalars().all())
        total_episodes = len(all_episodes)
        disrupted_count = sum(1 for ep in all_episodes if ep.status == "DISRUPTED")
        stability_pct = (
            round(((total_episodes - disrupted_count) / total_episodes * 100.0), 1)
            if total_episodes > 0
            else 100.0
        )

        # 6. Placement Length of Stay (average days for completed or active episodes)
        lengths = []
        for ep in all_episodes:
            end_d = ep.end_date or today
            duration = (end_d - ep.start_date).days
            if duration >= 0:
                lengths.append(duration)
        avg_length_of_stay = round(sum(lengths) / len(lengths), 1) if lengths else 0.0

        # 7. Sibling Placements Together
        # Calculate from sibling relationships and active placements
        from app.models.relationship import FamilyRelationship

        sibling_rels_stmt = select(FamilyRelationship).where(
            FamilyRelationship.relationship_type.in_(["SIBLING", "HALF_SIBLING", "STEP_SIBLING", "sibling_of"]),
            FamilyRelationship.is_active.is_(True),
        )
        sibling_rels = list((await self.session.execute(sibling_rels_stmt)).scalars().all())

        # Map active child placements
        child_home_map: dict[uuid.UUID, uuid.UUID] = {
            ep.child_id: ep.placement_home_id
            for ep in all_episodes
            if ep.status == "ACTIVE" and ep.placement_home_id is not None
        }

        sibling_pairs_checked = 0
        sibling_pairs_together = 0
        for rel in sibling_rels:
            h1 = child_home_map.get(rel.person_a_id)
            h2 = child_home_map.get(rel.person_b_id)
            if h1 and h2:
                sibling_pairs_checked += 1
                if h1 == h2:
                    sibling_pairs_together += 1

        sibling_together_pct = (
            round((sibling_pairs_together / sibling_pairs_checked * 100.0), 1)
            if sibling_pairs_checked > 0
            else 100.0
        )



        # 9. Complaint Trends by Severity
        complaints_stmt = select(ResourceComplaint.severity, func.count(ResourceComplaint.id)).where(
            ResourceComplaint.deleted_at.is_(None)
        ).group_by(ResourceComplaint.severity)
        complaint_res = await self.session.execute(complaints_stmt)
        complaint_trends = {str(sev): int(cnt) for sev, cnt in complaint_res.all()}

        # 10. Compliance Trends
        compliance_trends = {
            "active_homes": active_homes_count,
            "total_licensed_capacity": total_capacity,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
        }

        return StrategicOutcomesMetrics(
            active_resource_homes=active_homes_count,
            total_licensed_capacity=total_capacity,
            occupied_beds=occupied_beds,
            available_beds=available_beds,
            resource_home_growth={
                "new_approvals_ytd": new_approvals,
                "closures_ytd": None,
                "closures_available": False,
                "closures_reason": "Authoritative closure date tracking is not configured.",
                "net_growth": None,
            },
            caregiver_retention_rate_pct=None,
            caregiver_retention_available=False,
            caregiver_retention_reason="Authoritative longitudinal cohort tracking is required to calculate true retention.",
            active_home_longevity_over_one_year_pct=longevity_pct,
            recruitment_conversion_rate_pct=conversion_pct,
            average_days_inquiry_to_approval=avg_days_to_approval,
            placement_stability_pct=stability_pct,
            average_placement_length_of_stay_days=avg_length_of_stay,
            sibling_placements_together_pct=sibling_together_pct,
            family_connection_rate_pct=None,
            family_connection_available=False,
            family_connection_reason="Authoritative family connection structured data tracking is not configured.",
            cultural_connection_rate_pct=None,
            cultural_connection_available=False,
            cultural_connection_reason="Authoritative cultural connection plan data tracking is not configured.",
            compliance_trends=compliance_trends,
            complaint_trends=complaint_trends,
        )
