"""Pydantic schemas for Placement Matching (Sprint 3)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ChildPlacementProfile(BaseModel):
    """Child placement search criteria and support needs."""

    model_config = ConfigDict(from_attributes=True)

    child_id: uuid.UUID | None = None
    age: int = Field(..., ge=0, le=25, description="Child current age")
    gender: str | None = None
    sibling_group_size: int = Field(default=1, ge=1, description="Number of siblings needing placement together")
    sibling_ids: list[uuid.UUID] = Field(default_factory=list)
    primary_language: str = "English"
    indigenous_community: str | None = None
    medical_complexity: bool = False
    medical_notes: str | None = None
    behavioural_needs: bool = False
    behavioural_notes: str | None = None
    accessibility_needs: bool = False
    accessibility_notes: str | None = None
    preferred_location: str | None = None
    service_area: str | None = None
    preferred_home_types: list[str] = Field(default_factory=list)


class PlacementMatchFactor(BaseModel):
    """Explainable compatibility factor for matching candidate evaluation."""

    factor_key: str
    name: str
    status: str = Field(..., description="PASS, WARNING, FAIL, INFO")
    explanation: str
    weight: float = 1.0


class PlacementMatchCandidate(BaseModel):
    """Evaluated candidate Resource Home with explainable factors."""

    home_id: uuid.UUID
    home_code: str
    home_name: str
    home_type: str
    status: str
    licensing_status: str
    total_capacity: int
    active_occupancy: int
    available_beds: int
    community: str | None = None
    city: str
    primary_caregiver_name: str | None = None
    compatibility_level: str = Field(..., description="HIGH, MODERATE, LOW, INELIGIBLE")
    is_eligible: bool
    factors: list[PlacementMatchFactor] = Field(default_factory=list)
    exclusion_reasons: list[str] = Field(default_factory=list)
    compatibility_notes: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PlacementMatchResponse(BaseModel):
    """Assistive decision-support matching response."""

    child_profile: ChildPlacementProfile
    total_homes_evaluated: int
    eligible_candidates: list[PlacementMatchCandidate]
    excluded_candidates: list[PlacementMatchCandidate]
    disclaimer: str = (
        "Assistive decision-support only. The software does not autonomously place children. "
        "Placement decisions remain a human professional determination via authorized PlacementEpisode workflows."
    )
