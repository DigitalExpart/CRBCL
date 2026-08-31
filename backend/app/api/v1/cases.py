"""Case management endpoints with Phase 4 extensions: Snapshot, Lifecycle, People, Assignments, External Workers, Sources, Links, Restrictions, Transfers, and Status History."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.permissions.service import PermissionService
from app.repositories.case_management_repo import (
    CaseAssignmentRepository,
    CaseExternalWorkerRepository,
    CaseLinkRepository,
    CasePersonRepository,
    CaseRestrictionRepository,
    CaseSourceRepository,
    CaseStatusHistoryRepository,
    CaseTransferRepository,
)
from app.repositories.case_repo import CaseRepository
from app.schemas.case_management import (
    CaseAssignmentCreate,
    CaseAssignmentResponse,
    CaseCloseRequest,
    CaseCreate,
    CaseExternalWorkerCreate,
    CaseExternalWorkerResponse,
    CaseLinkCreate,
    CaseLinkResponse,
    CasePersonCreate,
    CasePersonResponse,
    CaseReopenRequest,
    CaseResponse,
    CaseRestrictionCreate,
    CaseRestrictionRemoval,
    CaseRestrictionResponse,
    CaseSnapshotResponse,
    CaseSourceCreate,
    CaseSourceResponse,
    CaseStatusHistoryResponse,
    CaseTransferCreate,
    CaseTransferResponse,
    CaseTransferReview,
    CaseUpdate,
)
from app.schemas.common import PaginatedResponse, PaginationMeta
from app.services.case_service import CaseService
from app.services.case_transfer_service import CaseTransferService

router = APIRouter(tags=["Cases"])


# ── Core Cases & Search ───────────────────────────────────────
@router.get("/cases", response_model=PaginatedResponse[CaseResponse])
async def list_cases(
    request: Request,
    query: str | None = Query(default=None, description="Search case #, title, worker, description"),
    status_filter: str | None = Query(default=None, alias="status"),
    stage: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    case_type: str | None = Query(default=None),
    client_id: uuid.UUID | None = Query(default=None),
    family_id: uuid.UUID | None = Query(default=None),
    assigned_worker_id: uuid.UUID | None = Query(default=None),
    assigned_team_id: uuid.UUID | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    sort: str | None = Query(default=None),
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    perm_service = PermissionService(db)
    accessible_team_ids = await perm_service.get_user_accessible_team_ids(user.id)

    repo = CaseRepository(db)
    cases, total = await repo.search(
        query_text=query,
        status=status_filter,
        stage=stage,
        priority=priority,
        risk_level=risk_level,
        case_type=case_type,
        client_id=client_id,
        family_id=family_id,
        assigned_worker_id=assigned_worker_id,
        assigned_team_id=assigned_team_id,
        accessible_team_ids=accessible_team_ids,
        start_date=start_date,
        end_date=end_date,
        offset=offset,
        limit=limit,
        sort_by=sort,
    )

    return PaginatedResponse[CaseResponse](
        items=[CaseResponse.model_validate(c) for c in cases],
        pagination=PaginationMeta(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total,
        ),
    )


@router.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    user: User = Depends(require_permission(Permissions.CASE_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    case = await service.create_case(
        title=payload.title,
        case_type=payload.case_type,
        priority=payload.priority,
        risk_level=payload.risk_level,
        stage=payload.stage,
        description=payload.description,
        client_id=payload.client_id,
        family_id=payload.family_id,
        assigned_worker_id=payload.assigned_worker_id,
        assigned_team_id=payload.assigned_team_id,
        intake_date=payload.intake_date,
        current_user=user,
    )
    return CaseResponse.model_validate(case)


@router.get("/cases/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    case = await service.get_case_or_404(case_id, user)
    return CaseResponse.model_validate(case)


@router.patch("/cases/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdate,
    user: User = Depends(require_permission(Permissions.CASE_UPDATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    updated_case = await service.update_case(
        case_id=case_id,
        update_data=payload.model_dump(exclude_unset=True),
        current_user=user,
    )
    return CaseResponse.model_validate(updated_case)


# ── Snapshot & Lifecycle Commands ─────────────────────────────
@router.get("/cases/{case_id}/snapshot", response_model=CaseSnapshotResponse)
async def get_case_snapshot(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    snapshot = await service.get_case_snapshot(case_id, user)
    return CaseSnapshotResponse(**snapshot)


@router.post("/cases/{case_id}/close", response_model=CaseResponse)
async def close_case(
    case_id: uuid.UUID,
    payload: CaseCloseRequest,
    user: User = Depends(require_permission(Permissions.CASE_CLOSE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    closed = await service.close_case(
        case_id=case_id,
        closed_reason=payload.closed_reason,
        closed_date=payload.closed_date,
        current_user=user,
    )
    return CaseResponse.model_validate(closed)


@router.post("/cases/{case_id}/reopen", response_model=CaseResponse)
async def reopen_case(
    case_id: uuid.UUID,
    payload: CaseReopenRequest,
    user: User = Depends(require_permission(Permissions.CASE_REOPEN)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    reopened = await service.reopen_case(
        case_id=case_id,
        reopen_reason=payload.reopened_reason,
        current_user=user,
    )
    return CaseResponse.model_validate(reopened)


# ── Case People ───────────────────────────────────────────────
@router.get("/cases/{case_id}/people", response_model=list[CasePersonResponse])
async def list_case_people(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_PEOPLE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    people_repo = CasePersonRepository(db)
    people = await people_repo.get_by_case(case_id)
    return [
        CasePersonResponse(
            id=p.id,
            case_id=p.case_id,
            person_id=p.person_id,
            role=p.role,
            relationship_to_subject=p.relationship_to_subject,
            is_primary=p.is_primary,
            start_date=p.start_date,
            end_date=p.end_date,
            notes=p.notes,
            person_first_name=p.person.first_name if p.person else None,
            person_last_name=p.person.last_name if p.person else None,
            created_at=p.created_at,
        )
        for p in people
    ]


@router.post("/cases/{case_id}/people", response_model=CasePersonResponse, status_code=status.HTTP_201_CREATED)
async def add_case_person(
    case_id: uuid.UUID,
    payload: CasePersonCreate,
    user: User = Depends(require_permission(Permissions.CASE_PEOPLE_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    person = await service.add_person_to_case(
        case_id=case_id,
        person_id=payload.person_id,
        role=payload.role,
        relationship_to_subject=payload.relationship_to_subject,
        is_primary=payload.is_primary,
        notes=payload.notes,
        current_user=user,
    )
    people_repo = CasePersonRepository(db)
    loaded_p = await people_repo.get_by_id_with_person(person.id)
    return CasePersonResponse(
        id=loaded_p.id,
        case_id=loaded_p.case_id,
        person_id=loaded_p.person_id,
        role=loaded_p.role,
        relationship_to_subject=loaded_p.relationship_to_subject,
        is_primary=loaded_p.is_primary,
        start_date=loaded_p.start_date,
        end_date=loaded_p.end_date,
        notes=loaded_p.notes,
        person_first_name=loaded_p.person.first_name if loaded_p.person else None,
        person_last_name=loaded_p.person.last_name if loaded_p.person else None,
        created_at=loaded_p.created_at,
    )


@router.delete("/cases/{case_id}/people/{person_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_case_person(
    case_id: uuid.UUID,
    person_link_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_PEOPLE_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    people_repo = CasePersonRepository(db)
    p = await people_repo.get(person_link_id)
    if p:
        await people_repo.soft_delete(p, deleted_by=user.id)
        await db.commit()


# ── Worker Assignments ─────────────────────────────────────────
@router.get("/cases/{case_id}/assignments", response_model=list[CaseAssignmentResponse])
async def list_case_assignments(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_ASSIGNMENT_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseAssignmentRepository(db)
    assignments = await repo.get_by_case(case_id)
    return [
        CaseAssignmentResponse(
            id=a.id,
            case_id=a.case_id,
            user_id=a.user_id,
            user_name=a.user.full_name if a.user else None,
            user_email=a.user.email if a.user else None,
            role=a.role,
            is_active=a.is_active,
            assigned_at=a.assigned_at,
            unassigned_at=a.unassigned_at,
            notes=a.notes,
        )
        for a in assignments
    ]


@router.post("/cases/{case_id}/assignments", response_model=CaseAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_case_worker(
    case_id: uuid.UUID,
    payload: CaseAssignmentCreate,
    user: User = Depends(require_permission(Permissions.CASE_ASSIGNMENT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    assignment = await service.assign_worker(
        case_id=case_id,
        user_id=payload.user_id,
        role=payload.role,
        notes=payload.notes,
        current_user=user,
    )
    assign_repo = CaseAssignmentRepository(db)
    loaded_a = await assign_repo.get_by_id_with_user(assignment.id)
    return CaseAssignmentResponse(
        id=loaded_a.id,
        case_id=loaded_a.case_id,
        user_id=loaded_a.user_id,
        user_name=loaded_a.user.full_name if loaded_a.user else None,
        user_email=loaded_a.user.email if loaded_a.user else None,
        role=loaded_a.role,
        is_active=loaded_a.is_active,
        assigned_at=loaded_a.assigned_at,
        unassigned_at=loaded_a.unassigned_at,
        notes=loaded_a.notes,
    )


@router.delete("/cases/{case_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def end_worker_assignment(
    case_id: uuid.UUID,
    assignment_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_ASSIGNMENT_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    await service.unassign_worker(assignment_id, current_user=user)


# ── Case External Workers ─────────────────────────────────────
@router.get("/cases/{case_id}/external-workers", response_model=list[CaseExternalWorkerResponse])
async def list_case_external_workers(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_EXTERNAL_WORKER_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseExternalWorkerRepository(db)
    workers = await repo.get_by_case(case_id)
    return [CaseExternalWorkerResponse.model_validate(w) for w in workers]


@router.post("/cases/{case_id}/external-workers", response_model=CaseExternalWorkerResponse, status_code=status.HTTP_201_CREATED)
async def add_case_external_worker(
    case_id: uuid.UUID,
    payload: CaseExternalWorkerCreate,
    user: User = Depends(require_permission(Permissions.CASE_EXTERNAL_WORKER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    case = await service.get_case_or_404(case_id, user)
    repo = CaseExternalWorkerRepository(db)
    worker = await repo.create(
        case_id=case.id,
        name=payload.name,
        organization=payload.organization,
        role=payload.role,
        phone=payload.phone,
        email=payload.email,
        notes=payload.notes,
        start_date=payload.start_date,
        end_date=payload.end_date,
        created_by=user.id,
    )
    await db.commit()
    return CaseExternalWorkerResponse.model_validate(worker)


@router.delete("/cases/{case_id}/external-workers/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_case_external_worker(
    case_id: uuid.UUID,
    worker_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_EXTERNAL_WORKER_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseExternalWorkerRepository(db)
    w = await repo.get(worker_id)
    if w:
        await repo.soft_delete(w, deleted_by=user.id)
        await db.commit()


# ── Case Sources (Other & Collateral) ──────────────────────────
@router.get("/cases/{case_id}/sources", response_model=list[CaseSourceResponse])
async def list_case_sources(
    case_id: uuid.UUID,
    category: str | None = Query(default=None),
    user: User = Depends(require_permission(Permissions.CASE_SOURCE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseSourceRepository(db)
    sources = await repo.get_by_case(case_id, category=category)
    return [CaseSourceResponse.model_validate(s) for s in sources]


@router.post("/cases/{case_id}/sources", response_model=CaseSourceResponse, status_code=status.HTTP_201_CREATED)
async def add_case_source(
    case_id: uuid.UUID,
    payload: CaseSourceCreate,
    user: User = Depends(require_permission(Permissions.CASE_SOURCE_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    case = await service.get_case_or_404(case_id, user)
    repo = CaseSourceRepository(db)
    src = await repo.create(
        case_id=case.id,
        category=payload.category,
        name=payload.name,
        relationship_or_role=payload.relationship_or_role,
        organization=payload.organization,
        person_id=payload.person_id,
        provider_id=payload.provider_id,
        phone=payload.phone,
        email=payload.email,
        notes=payload.notes,
        created_by=user.id,
    )
    await db.commit()
    return CaseSourceResponse.model_validate(src)


@router.delete("/cases/{case_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_case_source(
    case_id: uuid.UUID,
    source_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_SOURCE_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseSourceRepository(db)
    src = await repo.get(source_id)
    if src:
        await repo.soft_delete(src, deleted_by=user.id)
        await db.commit()


# ── Case Links ────────────────────────────────────────────────
@router.get("/cases/{case_id}/links", response_model=list[CaseLinkResponse])
async def list_case_links(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_LINK_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseLinkRepository(db)
    links = await repo.get_by_case(case_id)
    return [
        CaseLinkResponse(
            id=link.id,
            source_case_id=link.source_case_id,
            target_case_id=link.target_case_id,
            target_case_number=link.target_case.case_number if link.target_case else None,
            target_case_title=link.target_case.title if link.target_case else None,
            link_type=link.link_type,
            reason=link.reason,
            linked_at=link.linked_at,
        )
        for link in links
    ]


@router.post("/cases/{case_id}/links", response_model=CaseLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_case_link(
    case_id: uuid.UUID,
    payload: CaseLinkCreate,
    user: User = Depends(require_permission(Permissions.CASE_LINK_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    link = await service.create_case_link(
        source_case_id=case_id,
        target_case_id=payload.target_case_id,
        link_type=payload.link_type,
        reason=payload.reason,
        current_user=user,
    )
    link_repo = CaseLinkRepository(db)
    loaded_link = await link_repo.get_by_id_with_cases(link.id)
    return CaseLinkResponse(
        id=loaded_link.id,
        source_case_id=loaded_link.source_case_id,
        source_case_number=loaded_link.source_case.case_number if loaded_link.source_case else None,
        target_case_id=loaded_link.target_case_id,
        target_case_number=loaded_link.target_case.case_number if loaded_link.target_case else None,
        target_case_title=loaded_link.target_case.title if loaded_link.target_case else None,
        link_type=loaded_link.link_type,
        reason=loaded_link.reason,
        linked_at=loaded_link.linked_at,
    )


@router.delete("/cases/{case_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_case_link(
    case_id: uuid.UUID,
    link_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_LINK_WRITE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseLinkRepository(db)
    link = await repo.get(link_id)
    if link:
        await repo.delete(link)
        await db.commit()


# ── Case Restrictions (Conflict of Interest) ───────────────────
@router.get("/cases/{case_id}/restrictions", response_model=list[CaseRestrictionResponse])
async def list_case_restrictions(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_RESTRICTION_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseRestrictionRepository(db)
    restrictions = await repo.get_by_case(case_id)
    return [
        CaseRestrictionResponse(
            id=r.id,
            case_id=r.case_id,
            user_id=r.user_id,
            user_name=r.user.full_name if r.user else None,
            restriction_type=r.restriction_type,
            reason=r.reason,
            is_active=r.is_active,
            created_at=r.created_at,
            expires_at=r.expires_at,
            removed_at=r.removed_at,
            removal_reason=r.removal_reason,
        )
        for r in restrictions
    ]


@router.post("/cases/{case_id}/restrictions", response_model=CaseRestrictionResponse, status_code=status.HTTP_201_CREATED)
async def add_case_restriction(
    case_id: uuid.UUID,
    payload: CaseRestrictionCreate,
    user: User = Depends(require_permission(Permissions.CASE_RESTRICTION_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    restriction = await service.add_case_restriction(
        case_id=case_id,
        user_id=payload.user_id,
        restriction_type=payload.restriction_type,
        reason=payload.reason,
        current_user=user,
    )
    restr_repo = CaseRestrictionRepository(db)
    loaded_r = await restr_repo.get_by_id_with_user(restriction.id)
    return CaseRestrictionResponse(
        id=loaded_r.id,
        case_id=loaded_r.case_id,
        user_id=loaded_r.user_id,
        user_name=loaded_r.user.full_name if loaded_r.user else None,
        restriction_type=loaded_r.restriction_type,
        reason=loaded_r.reason,
        is_active=loaded_r.is_active,
        created_at=loaded_r.created_at,
        expires_at=loaded_r.expires_at,
        removed_at=loaded_r.removed_at,
        removal_reason=loaded_r.removal_reason,
    )


@router.post("/cases/{case_id}/restrictions/{restriction_id}/remove", response_model=CaseRestrictionResponse)
async def remove_case_restriction(
    case_id: uuid.UUID,
    restriction_id: uuid.UUID,
    payload: CaseRestrictionRemoval,
    user: User = Depends(require_permission(Permissions.CASE_RESTRICTION_MANAGE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    restriction = await service.remove_case_restriction(
        restriction_id=restriction_id,
        removal_reason=payload.removal_reason,
        current_user=user,
    )
    restr_repo = CaseRestrictionRepository(db)
    loaded_r = await restr_repo.get_by_id_with_user(restriction.id)
    return CaseRestrictionResponse(
        id=loaded_r.id,
        case_id=loaded_r.case_id,
        user_id=loaded_r.user_id,
        user_name=loaded_r.user.full_name if loaded_r.user else None,
        restriction_type=loaded_r.restriction_type,
        reason=loaded_r.reason,
        is_active=loaded_r.is_active,
        created_at=loaded_r.created_at,
        expires_at=loaded_r.expires_at,
        removed_at=loaded_r.removed_at,
        removal_reason=loaded_r.removal_reason,
    )


# ── Case Transfers & Supervisor Queue ─────────────────────────
@router.get("/cases/{case_id}/transfers", response_model=list[CaseTransferResponse])
async def list_case_transfers(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseTransferRepository(db)
    transfers = await repo.get_by_case(case_id)
    return [
        CaseTransferResponse(
            id=t.id,
            case_id=t.case_id,
            case_number=t.case.case_number if t.case else None,
            child_id=t.child_id,
            child_name=f"{t.child.first_name} {t.child.last_name}" if t.child else None,
            source_team_id=t.source_team_id,
            source_team_name=t.source_team.name if t.source_team else None,
            destination_team_id=t.destination_team_id,
            destination_team_name=t.destination_team.name if t.destination_team else None,
            reason=t.reason,
            status=t.status,
            requested_by=t.requested_by,
            requester_name=t.requester.full_name if t.requester else None,
            requested_at=t.requested_at,
            reviewed_by=t.reviewed_by,
            reviewed_at=t.reviewed_at,
            review_notes=t.review_notes,
            created_at=t.created_at,
        )
        for t in transfers
    ]


@router.post("/cases/{case_id}/transfers", response_model=CaseTransferResponse, status_code=status.HTTP_201_CREATED)
async def create_case_transfer(
    case_id: uuid.UUID,
    payload: CaseTransferCreate,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseTransferService(db)
    transfer = await service.create_transfer_request(
        case_id=case_id,
        destination_team_id=payload.destination_team_id,
        reason=payload.reason,
        child_id=payload.child_id,
        is_submitted=payload.submit_immediately,
        current_user=user,
    )
    transfer_repo = CaseTransferRepository(db)
    loaded_t = await transfer_repo.get_by_id_with_details(transfer.id)
    return CaseTransferResponse(
        id=loaded_t.id,
        case_id=loaded_t.case_id,
        case_number=loaded_t.case.case_number if loaded_t.case else None,
        child_id=loaded_t.child_id,
        child_name=f"{loaded_t.child.first_name} {loaded_t.child.last_name}" if loaded_t.child else None,
        source_team_id=loaded_t.source_team_id,
        source_team_name=loaded_t.source_team.name if loaded_t.source_team else None,
        destination_team_id=loaded_t.destination_team_id,
        destination_team_name=loaded_t.destination_team.name if loaded_t.destination_team else None,
        reason=loaded_t.reason,
        status=loaded_t.status,
        requested_by=loaded_t.requested_by,
        requester_name=loaded_t.requester.full_name if loaded_t.requester else None,
        requested_at=loaded_t.requested_at,
        reviewed_by=loaded_t.reviewed_by,
        reviewed_at=loaded_t.reviewed_at,
        review_notes=loaded_t.review_notes,
        created_at=loaded_t.created_at,
    )


@router.post("/transfers/{transfer_id}/submit", response_model=CaseTransferResponse)
async def submit_case_transfer(
    transfer_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_CREATE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseTransferService(db)
    transfer = await service.submit_transfer_request(transfer_id=transfer_id, current_user=user)
    transfer_repo = CaseTransferRepository(db)
    loaded_t = await transfer_repo.get_by_id_with_details(transfer.id)
    return CaseTransferResponse(
        id=loaded_t.id,
        case_id=loaded_t.case_id,
        case_number=loaded_t.case.case_number if loaded_t.case else None,
        child_id=loaded_t.child_id,
        child_name=f"{loaded_t.child.first_name} {loaded_t.child.last_name}" if loaded_t.child else None,
        source_team_id=loaded_t.source_team_id,
        source_team_name=loaded_t.source_team.name if loaded_t.source_team else None,
        destination_team_id=loaded_t.destination_team_id,
        destination_team_name=loaded_t.destination_team.name if loaded_t.destination_team else None,
        reason=loaded_t.reason,
        status=loaded_t.status,
        requested_by=loaded_t.requested_by,
        requester_name=loaded_t.requester.full_name if loaded_t.requester else None,
        requested_at=loaded_t.requested_at,
        reviewed_by=loaded_t.reviewed_by,
        reviewed_at=loaded_t.reviewed_at,
        review_notes=loaded_t.review_notes,
        created_at=loaded_t.created_at,
    )


@router.post("/transfers/{transfer_id}/approve", response_model=CaseTransferResponse)
async def approve_case_transfer(
    transfer_id: uuid.UUID,
    payload: CaseTransferReview,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseTransferService(db)
    transfer = await service.approve_transfer(
        transfer_id=transfer_id,
        review_notes=payload.review_notes,
        current_user=user,
    )
    transfer_repo = CaseTransferRepository(db)
    loaded_t = await transfer_repo.get_by_id_with_details(transfer.id)
    return CaseTransferResponse(
        id=loaded_t.id,
        case_id=loaded_t.case_id,
        case_number=loaded_t.case.case_number if loaded_t.case else None,
        child_id=loaded_t.child_id,
        child_name=f"{loaded_t.child.first_name} {loaded_t.child.last_name}" if loaded_t.child else None,
        source_team_id=loaded_t.source_team_id,
        source_team_name=loaded_t.source_team.name if loaded_t.source_team else None,
        destination_team_id=loaded_t.destination_team_id,
        destination_team_name=loaded_t.destination_team.name if loaded_t.destination_team else None,
        reason=loaded_t.reason,
        status=loaded_t.status,
        requested_by=loaded_t.requested_by,
        requester_name=loaded_t.requester.full_name if loaded_t.requester else None,
        requested_at=loaded_t.requested_at,
        reviewed_by=loaded_t.reviewed_by,
        reviewed_at=loaded_t.reviewed_at,
        review_notes=loaded_t.review_notes,
        created_at=loaded_t.created_at,
    )


@router.post("/transfers/{transfer_id}/return", response_model=CaseTransferResponse)
async def return_case_transfer(
    transfer_id: uuid.UUID,
    payload: CaseTransferReview,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    if not payload.review_notes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review notes required when returning transfer.")
    service = CaseTransferService(db)
    transfer = await service.return_transfer(
        transfer_id=transfer_id,
        review_notes=payload.review_notes,
        current_user=user,
    )
    transfer_repo = CaseTransferRepository(db)
    loaded_t = await transfer_repo.get_by_id_with_details(transfer.id)
    return CaseTransferResponse(
        id=loaded_t.id,
        case_id=loaded_t.case_id,
        case_number=loaded_t.case.case_number if loaded_t.case else None,
        child_id=loaded_t.child_id,
        child_name=f"{loaded_t.child.first_name} {loaded_t.child.last_name}" if loaded_t.child else None,
        source_team_id=loaded_t.source_team_id,
        source_team_name=loaded_t.source_team.name if loaded_t.source_team else None,
        destination_team_id=loaded_t.destination_team_id,
        destination_team_name=loaded_t.destination_team.name if loaded_t.destination_team else None,
        reason=loaded_t.reason,
        status=loaded_t.status,
        requested_by=loaded_t.requested_by,
        requester_name=loaded_t.requester.full_name if loaded_t.requester else None,
        requested_at=loaded_t.requested_at,
        reviewed_by=loaded_t.reviewed_by,
        reviewed_at=loaded_t.reviewed_at,
        review_notes=loaded_t.review_notes,
        created_at=loaded_t.created_at,
    )


@router.post("/transfers/{transfer_id}/deny", response_model=CaseTransferResponse)
async def deny_case_transfer(
    transfer_id: uuid.UUID,
    payload: CaseTransferReview,
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    if not payload.review_notes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Review notes required when denying transfer.")
    service = CaseTransferService(db)
    transfer = await service.deny_transfer(
        transfer_id=transfer_id,
        review_notes=payload.review_notes,
        current_user=user,
    )
    transfer_repo = CaseTransferRepository(db)
    loaded_t = await transfer_repo.get_by_id_with_details(transfer.id)
    return CaseTransferResponse(
        id=loaded_t.id,
        case_id=loaded_t.case_id,
        case_number=loaded_t.case.case_number if loaded_t.case else None,
        child_id=loaded_t.child_id,
        child_name=f"{loaded_t.child.first_name} {loaded_t.child.last_name}" if loaded_t.child else None,
        source_team_id=loaded_t.source_team_id,
        source_team_name=loaded_t.source_team.name if loaded_t.source_team else None,
        destination_team_id=loaded_t.destination_team_id,
        destination_team_name=loaded_t.destination_team.name if loaded_t.destination_team else None,
        reason=loaded_t.reason,
        status=loaded_t.status,
        requested_by=loaded_t.requested_by,
        requester_name=loaded_t.requester.full_name if loaded_t.requester else None,
        requested_at=loaded_t.requested_at,
        reviewed_by=loaded_t.reviewed_by,
        reviewed_at=loaded_t.reviewed_at,
        review_notes=loaded_t.review_notes,
        created_at=loaded_t.created_at,
    )


@router.get("/transfers/pending", response_model=list[CaseTransferResponse])
async def list_pending_transfers(
    user: User = Depends(require_permission(Permissions.CASE_TRANSFER_APPROVE)),
    db: AsyncSession = Depends(get_db),
):
    perm_service = PermissionService(db)
    accessible_team_ids = await perm_service.get_user_accessible_team_ids(user.id)
    repo = CaseTransferRepository(db)
    transfers = await repo.get_pending_transfers(team_ids=accessible_team_ids)
    return [
        CaseTransferResponse(
            id=t.id,
            case_id=t.case_id,
            case_number=t.case.case_number if t.case else None,
            child_id=t.child_id,
            child_name=f"{t.child.first_name} {t.child.last_name}" if t.child else None,
            source_team_id=t.source_team_id,
            source_team_name=t.source_team.name if t.source_team else None,
            destination_team_id=t.destination_team_id,
            destination_team_name=t.destination_team.name if t.destination_team else None,
            reason=t.reason,
            status=t.status,
            requested_by=t.requested_by,
            requester_name=t.requester.full_name if t.requester else None,
            requested_at=t.requested_at,
            reviewed_by=t.reviewed_by,
            reviewed_at=t.reviewed_at,
            review_notes=t.review_notes,
            created_at=t.created_at,
        )
        for t in transfers
    ]


# ── Case Status History ───────────────────────────────────────
@router.get("/cases/{case_id}/status-history", response_model=list[CaseStatusHistoryResponse])
async def get_case_status_history(
    case_id: uuid.UUID,
    user: User = Depends(require_permission(Permissions.CASE_READ)),
    db: AsyncSession = Depends(get_db),
):
    service = CaseService(db)
    await service.get_case_or_404(case_id, user)
    repo = CaseStatusHistoryRepository(db)
    history = await repo.get_by_case(case_id)
    return [
        CaseStatusHistoryResponse(
            id=h.id,
            case_id=h.case_id,
            previous_status=h.previous_status,
            new_status=h.new_status,
            reason=h.reason,
            changed_by=h.changed_by,
            changer_name=h.changer.full_name if h.changer else None,
            changed_at=h.changed_at,
            notes=h.notes,
        )
        for h in history
    ]
