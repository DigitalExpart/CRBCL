"""REST API router for Placement Homes, Licensing, Members, Visits, Contacts, and History."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.schemas.assessment import AssessmentCreate, AssessmentResponse
from app.schemas.caregiver_training import (
    CaregiverTrainingCreate,
    CaregiverTrainingResponse,
    HomeTrainingComplianceSummary,
)
from app.schemas.placement import BackgroundCheckCreate, BackgroundCheckResponse
from app.schemas.placement_home import (
    CorrectiveActionUpdate,
    HomeBackgroundCheckSummary,
    HomeClearanceItem,
    PlacementHistoryItemRead,
    PlacementHomeContactLogCreate,
    PlacementHomeContactLogRead,
    PlacementHomeCreate,
    PlacementHomeFilter,
    PlacementHomeLicenseCreate,
    PlacementHomeLicenseRead,
    PlacementHomeLicenseRenew,
    PlacementHomeMapMarkerRead,
    PlacementHomeMemberCreate,
    PlacementHomeMemberRead,
    PlacementHomeMemberUpdate,
    PlacementHomeMetricsRead,
    PlacementHomeRead,
    PlacementHomeUpdate,
    PlacementHomeVisitCreate,
    PlacementHomeVisitRead,
)
from app.services.assessment_service import AssessmentService
from app.services.background_check_service import BackgroundCheckService
from app.services.caregiver_training_service import CaregiverTrainingService
from app.services.placement_home_service import PlacementHomeService

router = APIRouter(prefix="/placement-homes", tags=["Placement Homes"])


@router.get("", response_model=dict[str, Any])
async def list_placement_homes(
    search: str | None = Query(None),
    home_type: str | None = Query(None),
    status: str | None = Query(None),
    licensing_status: str | None = Query(None),
    community: str | None = Query(None),
    available_only: bool = Query(False),
    is_archived: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_READ)),
):
    """List and search placement homes with live occupancy counts."""
    service = PlacementHomeService(db)
    filters = PlacementHomeFilter(
        search=search,
        home_type=home_type,
        status=status,
        licensing_status=licensing_status,
        community=community,
        available_only=available_only,
        is_archived=is_archived,
        page=page,
        page_size=page_size,
    )
    items, total = await service.repo.list_homes(filters)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=PlacementHomeRead, status_code=status.HTTP_201_CREATED)
async def create_placement_home(
    payload: PlacementHomeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_CREATE)),
):
    """Create a new placement home or facility."""
    service = PlacementHomeService(db)
    home = await service.create_home(payload, current_user.id)
    detail = await service.get_home_detail(home.id)
    return detail


@router.get("/metrics", response_model=PlacementHomeMetricsRead)
async def get_placement_home_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_READ)),
):
    """Compute aggregate placement home metrics for the operational dashboard."""
    service = PlacementHomeService(db)
    return await service.repo.get_metrics()


@router.get("/map", response_model=list[PlacementHomeMapMarkerRead])
async def get_placement_home_map_markers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_MAP_READ)),
):
    """Retrieve non-confidential map markers and availability indicators for active homes."""
    service = PlacementHomeService(db)
    return await service.repo.get_map_markers()


@router.get("/{home_id}", response_model=PlacementHomeRead)
async def get_placement_home(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_READ)),
):
    """Get full details of a placement home."""
    service = PlacementHomeService(db)
    return await service.get_home_detail(home_id)


@router.patch("/{home_id}", response_model=PlacementHomeRead)
async def update_placement_home(
    home_id: uuid.UUID,
    payload: PlacementHomeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_UPDATE)),
):
    """Update placement home attributes."""
    service = PlacementHomeService(db)
    await service.update_home(home_id, payload, current_user.id)
    return await service.get_home_detail(home_id)


@router.post("/{home_id}/archive", response_model=PlacementHomeRead)
async def archive_placement_home(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_ARCHIVE)),
):
    """Archive / close a placement home."""
    service = PlacementHomeService(db)
    await service.archive_home(home_id, current_user.id)
    return await service.get_home_detail(home_id)


# ── Members Endpoints ─────────────────────────────────────────
@router.post("/{home_id}/members", response_model=PlacementHomeMemberRead, status_code=status.HTTP_201_CREATED)
async def add_home_member(
    home_id: uuid.UUID,
    payload: PlacementHomeMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_MEMBER_MANAGE)),
):
    """Add a household member or caregiver to a placement home."""
    service = PlacementHomeService(db)
    member = await service.add_member(home_id, payload, current_user.id)
    person_name = f"{member.person.first_name} {member.person.last_name}" if member.person else None
    return {
        "id": member.id,
        "placement_home_id": member.placement_home_id,
        "person_id": member.person_id,
        "person_name": person_name,
        "role": member.role,
        "start_date": member.start_date,
        "end_date": member.end_date,
        "is_active": member.is_active,
        "notes": member.notes,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }


@router.patch("/{home_id}/members/{member_id}", response_model=PlacementHomeMemberRead)
async def update_home_member(
    home_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: PlacementHomeMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_MEMBER_MANAGE)),
):
    """Update household member role or active status."""
    service = PlacementHomeService(db)
    member = await service.update_member(home_id, member_id, payload, current_user.id)
    person_name = f"{member.person.first_name} {member.person.last_name}" if member.person else None
    return {
        "id": member.id,
        "placement_home_id": member.placement_home_id,
        "person_id": member.person_id,
        "person_name": person_name,
        "role": member.role,
        "start_date": member.start_date,
        "end_date": member.end_date,
        "is_active": member.is_active,
        "notes": member.notes,
        "created_at": member.created_at,
        "updated_at": member.updated_at,
    }


@router.delete("/{home_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_home_member(
    home_id: uuid.UUID,
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_MEMBER_MANAGE)),
):
    """Remove a household member from a placement home."""
    service = PlacementHomeService(db)
    await service.remove_member(home_id, member_id, current_user.id)


# ── Licensing Endpoints ───────────────────────────────────────
@router.post("/{home_id}/licenses", response_model=PlacementHomeLicenseRead, status_code=status.HTTP_201_CREATED)
async def create_home_license(
    home_id: uuid.UUID,
    payload: PlacementHomeLicenseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_LICENSE_MANAGE)),
):
    """Create an initial license record."""
    service = PlacementHomeService(db)
    return await service.create_license(home_id, payload, current_user.id)


@router.post("/{home_id}/licenses/renew", response_model=PlacementHomeLicenseRead, status_code=status.HTTP_201_CREATED)
async def renew_home_license(
    home_id: uuid.UUID,
    payload: PlacementHomeLicenseRenew,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_LICENSE_MANAGE)),
):
    """Renew placement home license (preserves prior licensing history)."""
    service = PlacementHomeService(db)
    return await service.renew_license(home_id, payload, current_user.id)


@router.post("/{home_id}/visits", response_model=PlacementHomeVisitRead, status_code=status.HTTP_201_CREATED)
async def create_home_visit(
    home_id: uuid.UUID,
    payload: PlacementHomeVisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_VISIT_CREATE)),
):
    """Log an inspection or support visit to a placement home."""
    service = PlacementHomeService(db)
    visit = await service.create_visit(home_id, payload, current_user.id)
    return PlacementHomeVisitRead.model_validate(visit)


# ── Contact Logs Endpoints ─────────────────────────────────────
@router.post("/{home_id}/contact-logs", response_model=PlacementHomeContactLogRead, status_code=status.HTTP_201_CREATED)
async def create_home_contact_log(
    home_id: uuid.UUID,
    payload: PlacementHomeContactLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_CONTACT_CREATE)),
):
    """Log communication with placement home caregivers."""
    service = PlacementHomeService(db)
    contact = await service.create_contact_log(home_id, payload, current_user.id)
    worker_name = (
        contact.worker.display_name or contact.worker.full_name or contact.worker.email if contact.worker else None
    )
    person_name = f"{contact.person.first_name} {contact.person.last_name}" if contact.person else None
    return {
        "id": contact.id,
        "placement_home_id": contact.placement_home_id,
        "person_id": contact.person_id,
        "worker_id": contact.worker_id,
        "worker_name": worker_name,
        "person_name": person_name,
        "contact_type": contact.contact_type,
        "contact_date": contact.contact_date,
        "duration_minutes": contact.duration_minutes,
        "subject": contact.subject,
        "notes": contact.notes,
        "follow_up_action": contact.follow_up_action,
        "created_at": contact.created_at,
        "updated_at": contact.updated_at,
    }


# ── Background Checks Summary ──────────────────────────────────


@router.get("/{home_id}/background-checks", response_model=list[HomeBackgroundCheckSummary])
async def get_home_background_checks(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ)),
):
    """Retrieve background screening summary for all household members with eligibility indicators."""
    service = PlacementHomeService(db)
    return await service.get_background_checks_summary(home_id, current_user)


# ── Placement History with Case Restriction Privacy ────────────
@router.get("/{home_id}/placements", response_model=list[PlacementHistoryItemRead])
async def get_home_placements_history(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_READ)),
):
    """Retrieve placement history. Redacts sensitive child/case identities if the requesting user is restricted."""
    service = PlacementHomeService(db)
    return await service.get_placement_history(home_id, current_user.id)


# ── Sprint 2: Inspections & Corrective Actions ──────────────────
@router.patch("/{home_id}/visits/{visit_id}/corrective-action", response_model=PlacementHomeVisitRead)
async def update_home_corrective_action(
    home_id: uuid.UUID,
    visit_id: uuid.UUID,
    payload: CorrectiveActionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_VISIT_CREATE)),
):
    """Update inspection findings, deficiencies, and corrective action resolution status."""
    service = PlacementHomeService(db)
    visit = await service.update_corrective_action(home_id, visit_id, payload, current_user.id)
    return PlacementHomeVisitRead.model_validate(visit)


# ── Sprint 2: Screenings & Clearances ───────────────────────────
@router.get("/{home_id}/clearances", response_model=list[HomeClearanceItem])
async def list_home_clearances(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.PLACEMENT_HOME_BACKGROUND_CHECK_READ)),
):
    """List all background clearances for members of a Resource Home."""
    service = PlacementHomeService(db)
    return await service.list_home_clearances(home_id)


@router.post("/{home_id}/clearances", response_model=BackgroundCheckResponse, status_code=status.HTTP_201_CREATED)
async def create_home_clearance(
    home_id: uuid.UUID,
    payload: BackgroundCheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.BACKGROUND_CHECK_WRITE)),
):
    """Record a screening/clearance check for a member of this Resource Home."""
    payload.placement_home_id = home_id
    service = BackgroundCheckService(db)
    check = await service.create_background_check(current_user, payload)
    return BackgroundCheckResponse.model_validate(check)


# ── Sprint 2: Caregiver Assessments ─────────────────────────────
@router.get("/{home_id}/assessments", response_model=list[AssessmentResponse])
async def list_home_assessments(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.ASSESSMENT_READ)),
):
    """List historical caregiver and home study assessments for a Resource Home."""
    service = AssessmentService(db)
    items, _ = await service.list_placement_home_assessments(home_id, current_user)
    return [AssessmentResponse.model_validate(a) for a in items]


@router.post("/{home_id}/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_home_assessment(
    home_id: uuid.UUID,
    body: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.ASSESSMENT_CREATE)),
):
    """Initiate a caregiver or home assessment under this Resource Home."""
    # Inject placement_home_id from path before Pydantic validates the payload,
    # so the model_validator (which requires case_id OR placement_home_id) passes.
    body["placement_home_id"] = str(home_id)
    payload = AssessmentCreate.model_validate(body)
    service = AssessmentService(db)
    assessment = await service.create_assessment(payload, current_user)
    return AssessmentResponse.model_validate(assessment)


# ── Sprint 2: Caregiver Training Compliance ────────────────────
@router.get("/{home_id}/training", response_model=list[CaregiverTrainingResponse])
async def list_home_trainings(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CAREGIVER_TRAINING_READ)),
):
    """List all training records for caregivers belonging to this Resource Home."""
    service = CaregiverTrainingService(db)
    items, _ = await service.list_trainings(current_user, placement_home_id=home_id)
    return [CaregiverTrainingResponse.model_validate(item) for item in items]


@router.get("/{home_id}/training/compliance", response_model=HomeTrainingComplianceSummary)
async def get_home_training_compliance(
    home_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CAREGIVER_TRAINING_READ)),
):
    """Get training compliance breakdown and mandatory course status for a Resource Home."""
    service = CaregiverTrainingService(db)
    return await service.get_home_training_summary(current_user, home_id)


@router.post("/{home_id}/training", response_model=CaregiverTrainingResponse, status_code=status.HTTP_201_CREATED)
async def create_home_caregiver_training(
    home_id: uuid.UUID,
    payload: CaregiverTrainingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permissions.CAREGIVER_TRAINING_WRITE)),
):
    """Record caregiver training completion associated with this Resource Home."""
    payload.placement_home_id = home_id
    service = CaregiverTrainingService(db)
    training = await service.create_training(current_user, payload)
    return CaregiverTrainingResponse.model_validate(training)

