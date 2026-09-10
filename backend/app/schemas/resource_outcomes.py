"""Pydantic schemas for Resource Unit Strategic Outcomes (Sprint 3)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrategicOutcomesMetrics(BaseModel):
    """Authoritative strategic outcome indicators for the Resource Unit."""

    model_config = ConfigDict(from_attributes=True)

    # Operational scale
    active_resource_homes: int = 0
    total_licensed_capacity: int = 0
    occupied_beds: int = 0
    available_beds: int = 0

    # Growth & Retention
    resource_home_growth: dict[str, Any] = Field(
        default_factory=lambda: {
            "new_approvals_ytd": 0,
            "closures_ytd": None,
            "closures_available": False,
            "closures_reason": "Authoritative closure date tracking is not configured.",
            "net_growth": None,
        }
    )
    # Longitudinal retention requires cohort tracking: unavailable until configured
    caregiver_retention_rate_pct: float | None = None
    caregiver_retention_available: bool = False
    caregiver_retention_reason: str | None = (
        "Authoritative longitudinal cohort tracking is required to calculate true retention."
    )
    # Distinct factual operational longevity metric
    active_home_longevity_over_one_year_pct: float | None = None

    recruitment_conversion_rate_pct: float = 0.0
    average_days_inquiry_to_approval: float = 0.0

    # Placement Quality & Stability
    placement_stability_pct: float = 0.0
    average_placement_length_of_stay_days: float = 0.0
    sibling_placements_together_pct: float = 0.0

    # Strategic outcomes requiring authoritative tracking: unavailable when unmeasured
    family_connection_rate_pct: float | None = None
    family_connection_available: bool = False
    family_connection_reason: str | None = (
        "Authoritative family connection structured data tracking is not configured."
    )

    cultural_connection_rate_pct: float | None = None
    cultural_connection_available: bool = False
    cultural_connection_reason: str | None = (
        "Authoritative cultural connection plan data tracking is not configured."
    )

    # Trends
    compliance_trends: dict[str, int] = Field(default_factory=dict)
    complaint_trends: dict[str, int] = Field(default_factory=dict)
