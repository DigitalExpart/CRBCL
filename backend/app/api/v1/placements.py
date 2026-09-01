"""FastAPI Endpoints for Primary Placement Episodes, Respite, Discharge, In-Home Placements & Child Longitudinal History."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.placement import (
    ChildLongitudinalEpisodesResponse,
    DischargeEpisodeCreate,
    DischargeEpisodeResponse,
    InHomePlacementCreate,
    InHomePlacementEnd,
    InHomePlacementListResponse,
    InHomePlacementResponse,
    InHomePlacementUpdate,
    PlacementEpisodeCreate,
    PlacementEpisodeListResponse,
    PlacementEpisodeResponse,
    PlacementEpisodeUpdate,
    RespiteEpisodeCreate,
    RespiteEpisodeListResponse,
    RespiteEpisodeResponse,
    RespiteEpisodeUpdate,
)
from app.services.placement_service import PlacementService

router = APIRouter(tags=["Child Placements & Episodes"])


# ── Placement Episodes ───────────────────────────────────────────────
@router.post(
    "/cases/{case_id}/placements",
    response_model=PlacementEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_placement_episode(
    case_id: uuid.UUID,
    payload: PlacementEpisodeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlacementEpisodeResponse:
    service = PlacementService(db)
    placement = await service.create_placement_episode(current_user, case_id, payload)
    return PlacementEpisodeResponse.model_validate(placement)


@router.get("/cases/{case_id}/placements", response_model=PlacementEpisodeListResponse)
async def list_case_placements(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> PlacementEpisodeListResponse:
    service = PlacementService(db)
    items, total = await service.list_placement_episodes_by_case(current_user, case_id, page=page, page_size=page_size)
    return PlacementEpisodeListResponse(
        items=[PlacementEpisodeResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/placements/{placement_id}", response_model=PlacementEpisodeResponse)
async def get_placement_episode(
    placement_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlacementEpisodeResponse:
    service = PlacementService(db)
    placement = await service.get_placement_episode(current_user, placement_id)
    return PlacementEpisodeResponse.model_validate(placement)


@router.patch("/placements/{placement_id}", response_model=PlacementEpisodeResponse)
async def update_placement_episode(
    placement_id: uuid.UUID,
    payload: PlacementEpisodeUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PlacementEpisodeResponse:
    service = PlacementService(db)
    placement = await service.update_placement_episode(current_user, placement_id, payload)
    return PlacementEpisodeResponse.model_validate(placement)


@router.post("/placements/{placement_id}/disrupt", response_model=PlacementEpisodeResponse)
async def disrupt_placement_episode(
    placement_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    reason: str | None = Query(None),
) -> PlacementEpisodeResponse:
    service = PlacementService(db)
    placement = await service.disrupt_placement_episode(current_user, placement_id, reason=reason)
    return PlacementEpisodeResponse.model_validate(placement)


# ── Respite Episodes ─────────────────────────────────────────────────
@router.post(
    "/placements/{placement_id}/respite",
    response_model=RespiteEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_respite_episode(
    placement_id: uuid.UUID,
    payload: RespiteEpisodeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RespiteEpisodeResponse:
    service = PlacementService(db)
    respite = await service.create_respite_episode(current_user, placement_id, payload)
    return RespiteEpisodeResponse.model_validate(respite)


@router.get("/placements/{placement_id}/respite", response_model=RespiteEpisodeListResponse)
async def list_respite_episodes(
    placement_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RespiteEpisodeListResponse:
    service = PlacementService(db)
    items = await service.list_respite_episodes(current_user, placement_id)
    return RespiteEpisodeListResponse(
        items=[RespiteEpisodeResponse.model_validate(i) for i in items],
        total=len(items),
    )


@router.patch("/respite/{respite_id}", response_model=RespiteEpisodeResponse)
async def update_respite_episode(
    respite_id: uuid.UUID,
    payload: RespiteEpisodeUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RespiteEpisodeResponse:
    service = PlacementService(db)
    respite = await service.update_respite_episode(current_user, respite_id, payload)
    return RespiteEpisodeResponse.model_validate(respite)


# ── Discharge Episodes ───────────────────────────────────────────────
@router.post(
    "/placements/{placement_id}/discharge",
    response_model=DischargeEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def discharge_placement_episode(
    placement_id: uuid.UUID,
    payload: DischargeEpisodeCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DischargeEpisodeResponse:
    service = PlacementService(db)
    discharge = await service.create_discharge_episode(current_user, placement_id, payload)
    return DischargeEpisodeResponse.model_validate(discharge)


# ── In-Home Placements ───────────────────────────────────────────────
@router.post(
    "/cases/{case_id}/in-home-placements",
    response_model=InHomePlacementResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_in_home_placement(
    case_id: uuid.UUID,
    payload: InHomePlacementCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InHomePlacementResponse:
    service = PlacementService(db)
    placement = await service.create_in_home_placement(current_user, case_id, payload)
    return InHomePlacementResponse.model_validate(placement)


@router.get("/cases/{case_id}/in-home-placements", response_model=InHomePlacementListResponse)
async def list_case_in_home_placements(
    case_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
) -> InHomePlacementListResponse:
    service = PlacementService(db)
    items, total = await service.list_in_home_placements_by_case(current_user, case_id, page=page, page_size=page_size)
    return InHomePlacementListResponse(
        items=[InHomePlacementResponse.model_validate(i) for i in items],
        total=total,
    )


@router.get("/in-home-placements/{placement_id}", response_model=InHomePlacementResponse)
async def get_in_home_placement(
    placement_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InHomePlacementResponse:
    service = PlacementService(db)
    placement = await service.get_in_home_placement(current_user, placement_id)
    return InHomePlacementResponse.model_validate(placement)


@router.patch("/in-home-placements/{placement_id}", response_model=InHomePlacementResponse)
async def update_in_home_placement(
    placement_id: uuid.UUID,
    payload: InHomePlacementUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InHomePlacementResponse:
    service = PlacementService(db)
    placement = await service.update_in_home_placement(current_user, placement_id, payload)
    return InHomePlacementResponse.model_validate(placement)


@router.post("/in-home-placements/{placement_id}/end", response_model=InHomePlacementResponse)
async def end_in_home_placement(
    placement_id: uuid.UUID,
    payload: InHomePlacementEnd,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InHomePlacementResponse:
    service = PlacementService(db)
    placement = await service.end_in_home_placement(current_user, placement_id, payload)
    return InHomePlacementResponse.model_validate(placement)


# ── Child Longitudinal Episodes ──────────────────────────────────────
@router.get("/children/{child_id}/episodes", response_model=ChildLongitudinalEpisodesResponse)
async def get_child_episodes(
    child_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChildLongitudinalEpisodesResponse:
    service = PlacementService(db)
    return await service.get_child_longitudinal_episodes(current_user, child_id)
