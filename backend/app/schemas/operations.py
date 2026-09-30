"""Pydantic schemas for Office Coordinator operations (requests, reservations, keys, rooms, supplies)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


# ── Operations Requests ──────────────────────────────────────
class OperationsRequestCreate(BaseModel):
    category: str = Field("GENERAL", description="FACILITIES, FLEET, SUPPLIES, IT_SUPPORT, GENERAL")
    title: str = Field(..., min_length=2, max_length=255)
    description: str = Field(..., min_length=3)
    priority: str = Field("MEDIUM", description="LOW, MEDIUM, HIGH, URGENT")
    department: str | None = Field(None, max_length=100)


class OperationsRequestUpdate(BaseModel):
    status: str | None = Field(None, description="OPEN, IN_PROGRESS, PENDING_APPROVAL, COMPLETED, CANCELLED")
    priority: str | None = Field(None, description="LOW, MEDIUM, HIGH, URGENT")
    assigned_to_id: uuid.UUID | None = None
    resolution_notes: str | None = None


class OperationsRequestResponse(BaseModel):
    id: uuid.UUID
    request_number: str
    category: str
    title: str
    description: str
    priority: str
    status: str
    requester_id: uuid.UUID
    requester_name: str | None = None
    assigned_to_id: uuid.UUID | None = None
    assigned_to_name: str | None = None
    department: str | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime


# ── Vehicle Reservations ─────────────────────────────────────
class VehicleReservationCreate(BaseModel):
    vehicle_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    purpose: str = Field(..., min_length=3, max_length=255)
    destination: str | None = Field(None, max_length=255)
    passengers_count: int = Field(1, ge=1, le=50)
    notes: str | None = None


class VehicleReservationUpdate(BaseModel):
    status: str | None = Field(None, description="PENDING, CONFIRMED, CHECKED_OUT, COMPLETED, CANCELLED")
    notes: str | None = None


class VehicleReservationResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle_name: str | None = None
    licence_plate: str | None = None
    reserved_by_id: uuid.UUID
    reserved_by_name: str | None = None
    start_time: datetime
    end_time: datetime
    purpose: str
    destination: str | None = None
    passengers_count: int
    status: str
    notes: str | None = None
    created_at: datetime


# ── Vehicle Key Logs ─────────────────────────────────────────
class VehicleKeyCheckoutRequest(BaseModel):
    vehicle_id: uuid.UUID
    key_tag: str = Field(..., min_length=1, max_length=50)
    staff_id: uuid.UUID
    notes: str | None = None


class VehicleKeyReturnRequest(BaseModel):
    notes: str | None = None


class VehicleKeyLogResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    vehicle_name: str | None = None
    key_tag: str
    staff_id: uuid.UUID
    staff_name: str | None = None
    issued_by_id: uuid.UUID | None = None
    issued_by_name: str | None = None
    checked_out_at: datetime
    returned_at: datetime | None = None
    status: str
    notes: str | None = None


# ── Room Bookings ────────────────────────────────────────────
class RoomBookingCreate(BaseModel):
    room_name: str = Field(..., min_length=2, max_length=100)
    title: str = Field(..., min_length=2, max_length=255)
    start_time: datetime
    end_time: datetime
    attendees_count: int = Field(1, ge=1, le=500)
    notes: str | None = None


class RoomBookingResponse(BaseModel):
    id: uuid.UUID
    room_name: str
    booked_by_id: uuid.UUID
    booked_by_name: str | None = None
    title: str
    start_time: datetime
    end_time: datetime
    attendees_count: int
    status: str
    notes: str | None = None
    created_at: datetime


# ── Supply Items ─────────────────────────────────────────────
class SupplyItemCreate(BaseModel):
    item_name: str = Field(..., min_length=2, max_length=200)
    category: str = Field("OFFICE", description="OFFICE, CLEANING, FIRST_AID, EVENT, OTHER")
    quantity: int = Field(0, ge=0)
    unit: str = Field("units", max_length=50)
    location: str | None = Field(None, max_length=200)
    reorder_threshold: int = Field(5, ge=0)
    notes: str | None = None


class SupplyItemUpdate(BaseModel):
    quantity: int | None = Field(None, ge=0)
    location: str | None = None
    reorder_threshold: int | None = Field(None, ge=0)
    notes: str | None = None


class SupplyItemResponse(BaseModel):
    id: uuid.UUID
    item_name: str
    category: str
    quantity: int
    unit: str
    location: str | None = None
    reorder_threshold: int
    status: str
    notes: str | None = None
    created_at: datetime


# ── Overview ─────────────────────────────────────────────────
class OperationsOverviewResponse(BaseModel):
    open_requests_count: int
    active_reservations_count: int
    keys_checked_out_count: int
    available_vehicles_count: int
    low_stock_supplies_count: int
    today_room_bookings_count: int
