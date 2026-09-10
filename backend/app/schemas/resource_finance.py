"""Pydantic schemas for Resource Finance Integration (Sprint 3)."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResourceFinanceSummary(BaseModel):
    """Authorized financial roll-up for a Resource Home."""

    model_config = ConfigDict(from_attributes=True)

    placement_home_id: uuid.UUID
    home_name: str
    home_code: str
    current_fiscal_year: str
    active_rate: Decimal | None = None
    rate_band_label: str | None = None
    monthly_invoiced_total: Decimal = Decimal("0.00")
    year_to_date_invoiced_total: Decimal = Decimal("0.00")
    pending_service_requests_count: int = 0
    pending_service_requests_total: Decimal = Decimal("0.00")
    approved_service_requests_count: int = 0
    approved_service_requests_total: Decimal = Decimal("0.00")
    recent_invoices: list[dict[str, Any]] = Field(default_factory=list)
    recent_service_requests: list[dict[str, Any]] = Field(default_factory=list)
