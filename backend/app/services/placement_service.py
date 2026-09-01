"""Service for Primary Placement Episodes, Respite, Discharge, In-Home Placements & Longitudinal History."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.service import AuditService
from app.models.placement import (
    DischargeEpisode,
    InHomePlacement,
    PlacementEpisode,
    RespiteEpisode,
)
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.service import PermissionService
from app.repositories.placement_repo import PlacementRepository
from app.schemas.placement import (
    ChildLongitudinalEpisodesResponse,
    DischargeEpisodeCreate,
    InHomePlacementCreate,
    InHomePlacementEnd,
    InHomePlacementUpdate,
    PlacementEpisodeCreate,
    PlacementEpisodeUpdate,
    RespiteEpisodeCreate,
    RespiteEpisodeUpdate,
)
from app.workflows.outbox import OutboxService
from app.workflows.timeline import TimelineService


class PlacementService:
    """Business logic for Child Placements, In-Home Preservations, Respite, and Discharges."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PlacementRepository(db)
        self.perm = PermissionService(db)
        self.audit = AuditService(db)
        self.timeline = TimelineService(db)
        self.outbox = OutboxService(db)

    async def _require_case_access(self, user_id: uuid.UUID, case_id: uuid.UUID) -> None:
        if await self.perm.is_user_restricted_from_case(user_id, case_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Case restriction active.",
            )

    async def _require_perm(self, user_id: uuid.UUID, permission_key: str) -> None:
        if not await self.perm.user_has_permission(user_id, permission_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have required permission: {permission_key}",
            )

    # ── Primary Placement Episodes ───────────────────────────────────
    async def create_placement_episode(
        self, user: User, case_id: uuid.UUID, data: PlacementEpisodeCreate
    ) -> PlacementEpisode:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        # Invariant: Single active primary placement or in-home placement per child (ADR-016)
        active_in_home = await self.repo.get_active_in_home_placement_for_child(data.child_id)
        if active_in_home:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Child already has an active in-home placement. End the in-home placement before initiating an out-of-home placement.",
            )

        active_placement = await self.repo.get_active_placement_for_child(data.child_id)
        if active_placement:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Child already has an active primary placement episode. Complete discharge or transfer before creating a new placement.",
            )

        if data.removal_episode_id:
            removal = await self.repo.get_removal_episode_by_id(data.removal_episode_id)
            if not removal or removal.case_id != case_id or removal.child_id != data.child_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Referenced removal episode is invalid or does not match the case and child.",
                )

        provider_name = data.provider_name
        provider_contact = data.provider_contact
        provider_address = data.provider_address
        primary_caregiver_name = data.primary_caregiver_name

        # Concurrency & Capacity Protection for Placement Homes (ADR-018)
        if data.placement_home_id:
            from app.repositories.placement_home_repo import PlacementHomeRepository

            home_repo = PlacementHomeRepository(self.db)
            # Row lock placement_home to prevent overbooking races
            home = await home_repo.get_for_update(data.placement_home_id)
            if not home:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Placement Home with ID '{data.placement_home_id}' not found.",
                )
            if home.is_archived or home.status == "CLOSED":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Placement Home '{home.name}' is closed / archived and cannot accept new placements.",
                )

            current_occupancy = await home_repo.get_active_occupancy(home.id)
            if current_occupancy >= home.total_capacity:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Placement Home '{home.name}' is at full capacity (approved capacity: {home.total_capacity}, active occupants: {current_occupancy}).",
                )

            if not provider_name:
                provider_name = home.name
            if not provider_address and home.address_line_1:
                provider_address = f"{home.address_line_1}, {home.city}"
            if not provider_contact and home.phone:
                provider_contact = home.phone
            if not primary_caregiver_name and home.primary_caregiver_name:
                primary_caregiver_name = home.primary_caregiver_name

        if not provider_name:
            provider_name = "Placement Destination"

        placement = PlacementEpisode(
            case_id=case_id,
            child_id=data.child_id,
            removal_episode_id=data.removal_episode_id,
            placement_home_id=data.placement_home_id,
            placement_type=data.placement_type.upper(),
            provider_name=provider_name,
            provider_contact=provider_contact,
            provider_address=provider_address,
            start_date=data.start_date,
            status="ACTIVE",
            primary_caregiver_name=primary_caregiver_name,
            per_diem_rate=data.per_diem_rate,
            cultural_plan_in_place=data.cultural_plan_in_place,
            placement_notes=data.placement_notes,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_placement_episode(placement)

        # Audit & Timeline
        await self.audit.log(
            event_type="PLACEMENT_EPISODE_CREATED",
            user_id=user.id,
            entity_type="placement_episode",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "placement_type": created.placement_type,
                "provider_name": created.provider_name,
                "start_date": str(created.start_date),
            },
        )
        await self.timeline.record_event(
            event_type="PLACEMENT_STARTED",
            title=f"Placement Started: {created.provider_name} ({created.placement_type})",
            description=f"Child placed with {created.provider_name} under {created.placement_type} arrangement.",
            entity_type="placement_episode",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="placement.created",
            aggregate_type="placement_episode",
            aggregate_id=created.id,
            payload={
                "placement_id": str(created.id),
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "placement_type": created.placement_type,
                "provider_name": created.provider_name,
            },
        )

        return created

    async def get_placement_episode(self, user: User, placement_id: uuid.UUID) -> PlacementEpisode:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)
        return placement

    async def list_placement_episodes_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[PlacementEpisode], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)
        return await self.repo.list_placement_episodes_by_case(case_id, page=page, page_size=page_size)

    async def update_placement_episode(
        self, user: User, placement_id: uuid.UUID, data: PlacementEpisodeUpdate
    ) -> PlacementEpisode:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("placement_type"):
            update_fields["placement_type"] = update_fields["placement_type"].upper()
        if update_fields.get("status"):
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(placement, k, v)
        placement.updated_by = user.id
        placement.version += 1

        await self.audit.log(
            event_type="PLACEMENT_EPISODE_UPDATED",
            user_id=user.id,
            entity_type="placement_episode",
            entity_id=placement.id,
            after_data=update_fields,
        )
        return placement

    async def disrupt_placement_episode(
        self, user: User, placement_id: uuid.UUID, reason: str | None = None
    ) -> PlacementEpisode:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        if placement.status not in ["ACTIVE"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot disrupt placement in status '{placement.status}'.",
            )

        placement.status = "DISRUPTED"
        if reason:
            placement.placement_notes = (f"{placement.placement_notes or ''}\n[Disruption Reason]: {reason}").strip()
        placement.updated_by = user.id
        placement.version += 1

        await self.timeline.record_event(
            event_type="PLACEMENT_DISRUPTED",
            title=f"Placement Disrupted: {placement.provider_name}",
            description=reason or "Placement episode marked as disrupted.",
            entity_type="placement_episode",
            entity_id=placement.id,
            case_id=placement.case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="placement.disrupted",
            aggregate_type="placement_episode",
            aggregate_id=placement.id,
            payload={"placement_id": str(placement.id), "reason": reason},
        )
        return placement

    # ── Respite Episodes ─────────────────────────────────────────────
    async def create_respite_episode(
        self, user: User, placement_id: uuid.UUID, data: RespiteEpisodeCreate
    ) -> RespiteEpisode:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        if placement.status not in ["ACTIVE", "DISRUPTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Respite care can only be scheduled for active or disrupted placement episodes.",
            )

        if data.end_date < data.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Respite end date cannot precede start date.",
            )

        respite = RespiteEpisode(
            placement_episode_id=placement_id,
            respite_provider_name=data.respite_provider_name,
            respite_type=data.respite_type.upper(),
            start_date=data.start_date,
            end_date=data.end_date,
            reason=data.reason,
            status=data.status.upper(),
            notes=data.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_respite_episode(respite)

        await self.timeline.record_event(
            event_type="RESPITE_SCHEDULED",
            title=f"Respite Scheduled: {created.respite_provider_name}",
            description=f"Respite from {created.start_date} to {created.end_date} with {created.respite_provider_name}.",
            entity_type="respite_episode",
            entity_id=created.id,
            case_id=placement.case_id,
            created_by=user.id,
        )
        return created

    async def list_respite_episodes(self, user: User, placement_id: uuid.UUID) -> list[RespiteEpisode]:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)
        return await self.repo.list_respite_episodes_by_placement(placement_id)

    async def update_respite_episode(
        self, user: User, respite_id: uuid.UUID, data: RespiteEpisodeUpdate
    ) -> RespiteEpisode:
        respite = await self.repo.get_respite_episode_by_id(respite_id)
        if not respite:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Respite episode not found.")
        placement = await self.repo.get_placement_episode_by_id(respite.placement_episode_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent placement not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("respite_type"):
            update_fields["respite_type"] = update_fields["respite_type"].upper()
        if update_fields.get("status"):
            update_fields["status"] = update_fields["status"].upper()

        for k, v in update_fields.items():
            setattr(respite, k, v)
        respite.updated_by = user.id
        respite.version += 1
        return respite

    # ── Discharge Episodes ───────────────────────────────────────────
    async def create_discharge_episode(
        self, user: User, placement_id: uuid.UUID, data: DischargeEpisodeCreate
    ) -> DischargeEpisode:
        placement = await self.repo.get_placement_episode_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement episode not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_DISCHARGE)

        if placement.status not in ["ACTIVE", "DISRUPTED"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Placement in status '{placement.status}' cannot be discharged.",
            )

        existing_discharge = await self.repo.get_discharge_by_placement_id(placement_id)
        if existing_discharge:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Placement episode already has a discharge record.",
            )

        if data.discharge_date < placement.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Discharge date cannot precede placement start date.",
            )

        discharge = DischargeEpisode(
            placement_episode_id=placement_id,
            discharge_date=data.discharge_date,
            discharge_type=data.discharge_type.upper(),
            destination_name=data.destination_name,
            destination_relationship=data.destination_relationship,
            post_discharge_supervision_plan=data.post_discharge_supervision_plan,
            discharge_readiness_assessed=data.discharge_readiness_assessed,
            approved_by=user.id,
            approved_at=datetime.now(UTC),
            notes=data.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_discharge_episode(discharge)

        # Conclude the primary placement episode
        placement.status = "COMPLETED"
        placement.end_date = data.discharge_date
        placement.updated_by = user.id
        placement.version += 1

        # Audit & Timeline
        await self.audit.log(
            event_type="PLACEMENT_DISCHARGED",
            user_id=user.id,
            entity_type="discharge_episode",
            entity_id=created.id,
            after_data={
                "placement_episode_id": str(placement_id),
                "discharge_date": str(data.discharge_date),
                "discharge_type": created.discharge_type,
                "destination_name": created.destination_name,
            },
        )
        await self.timeline.record_event(
            event_type="PLACEMENT_DISCHARGED",
            title=f"Placement Discharged: {created.discharge_type}",
            description=f"Child discharged from {placement.provider_name} to {created.destination_name or 'designated caregiver'}.",
            entity_type="discharge_episode",
            entity_id=created.id,
            case_id=placement.case_id,
            created_by=user.id,
        )
        await self.outbox.publish_event(
            event_type="placement.discharged",
            aggregate_type="discharge_episode",
            aggregate_id=created.id,
            payload={
                "discharge_id": str(created.id),
                "placement_id": str(placement_id),
                "case_id": str(placement.case_id),
                "discharge_type": created.discharge_type,
            },
        )
        return created

    # ── In-Home Placements ───────────────────────────────────────────
    async def create_in_home_placement(
        self, user: User, case_id: uuid.UUID, data: InHomePlacementCreate
    ) -> InHomePlacement:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        # Invariant: Single active placement per child
        active_in_home = await self.repo.get_active_in_home_placement_for_child(data.child_id)
        if active_in_home:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Child already has an active in-home placement.",
            )

        active_primary = await self.repo.get_active_placement_for_child(data.child_id)
        if active_primary:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Child is currently in an active out-of-home placement. Discharge the placement first.",
            )

        in_home = InHomePlacement(
            case_id=case_id,
            child_id=data.child_id,
            primary_caregiver_id=data.primary_caregiver_id,
            caregiver_relationship=data.caregiver_relationship,
            start_date=data.start_date,
            status="ACTIVE",
            supervision_level=data.supervision_level.upper(),
            safety_monitoring_frequency=data.safety_monitoring_frequency.upper(),
            support_services_provided=data.support_services_provided,
            notes=data.notes,
            created_by=user.id,
            updated_by=user.id,
        )
        created = await self.repo.create_in_home_placement(in_home)

        await self.audit.log(
            event_type="IN_HOME_PLACEMENT_CREATED",
            user_id=user.id,
            entity_type="in_home_placement",
            entity_id=created.id,
            after_data={
                "case_id": str(case_id),
                "child_id": str(data.child_id),
                "start_date": str(created.start_date),
            },
        )
        await self.timeline.record_event(
            event_type="IN_HOME_PLACEMENT_STARTED",
            title="In-Home Family Preservation Placement Initiated",
            description=f"In-home safety monitoring initiated under {created.supervision_level} supervision.",
            entity_type="in_home_placement",
            entity_id=created.id,
            case_id=case_id,
            created_by=user.id,
        )
        return created

    async def get_in_home_placement(self, user: User, placement_id: uuid.UUID) -> InHomePlacement:
        placement = await self.repo.get_in_home_placement_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="In-home placement not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)
        return placement

    async def list_in_home_placements_by_case(
        self, user: User, case_id: uuid.UUID, page: int = 1, page_size: int = 50
    ) -> tuple[list[InHomePlacement], int]:
        await self._require_case_access(user.id, case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)
        return await self.repo.list_in_home_placements_by_case(case_id, page=page, page_size=page_size)

    async def update_in_home_placement(
        self, user: User, placement_id: uuid.UUID, data: InHomePlacementUpdate
    ) -> InHomePlacement:
        placement = await self.repo.get_in_home_placement_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="In-home placement not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        update_fields = data.model_dump(exclude_unset=True)
        if update_fields.get("supervision_level"):
            update_fields["supervision_level"] = update_fields["supervision_level"].upper()
        if update_fields.get("safety_monitoring_frequency"):
            update_fields["safety_monitoring_frequency"] = update_fields["safety_monitoring_frequency"].upper()

        for k, v in update_fields.items():
            setattr(placement, k, v)
        placement.updated_by = user.id
        placement.version += 1
        return placement

    async def end_in_home_placement(
        self, user: User, placement_id: uuid.UUID, data: InHomePlacementEnd
    ) -> InHomePlacement:
        placement = await self.repo.get_in_home_placement_by_id(placement_id)
        if not placement:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="In-home placement not found.")
        await self._require_case_access(user.id, placement.case_id)
        await self._require_perm(user.id, Permissions.PLACEMENT_WRITE)

        if placement.status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"In-home placement is already in '{placement.status}' status.",
            )

        if data.end_date < placement.start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date cannot precede placement start date.",
            )

        placement.status = data.status.upper()
        placement.end_date = data.end_date
        placement.closure_reason = data.closure_reason
        if data.notes:
            placement.notes = f"{placement.notes or ''}\n[Closure Note]: {data.notes}".strip()
        placement.updated_by = user.id
        placement.version += 1

        await self.timeline.record_event(
            event_type="IN_HOME_PLACEMENT_ENDED",
            title=f"In-Home Placement Ended ({placement.status})",
            description=data.closure_reason or "In-home family preservation placement concluded.",
            entity_type="in_home_placement",
            entity_id=placement.id,
            case_id=placement.case_id,
            created_by=user.id,
        )
        return placement

    # ── Longitudinal Episodes Aggregate ──────────────────────────────
    async def get_child_longitudinal_episodes(
        self, user: User, child_id: uuid.UUID
    ) -> ChildLongitudinalEpisodesResponse:
        await self._require_perm(user.id, Permissions.PLACEMENT_READ)

        in_home = await self.repo.list_in_home_placements_by_child(child_id)
        removals = await self.repo.list_removal_episodes_by_child(child_id)
        placements = await self.repo.list_placement_episodes_by_child(child_id)
        permanency = await self.repo.list_permanency_plans_by_child(child_id)
        visitation = await self.repo.list_visitation_plans_by_child(child_id)
        court = await self.repo.list_court_events_by_child(child_id)

        return ChildLongitudinalEpisodesResponse(
            child_id=child_id,
            in_home_placements=in_home,  # type: ignore
            removal_episodes=removals,  # type: ignore
            placement_episodes=placements,  # type: ignore
            permanency_plans=permanency,  # type: ignore
            visitation_plans=visitation,  # type: ignore
            court_events=court,  # type: ignore
        )
