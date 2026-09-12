"""Pydantic v2 schemas for canonical Person identity and comprehensive profiles."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ── Sub-resource Schemas ─────────────────────────────────────────

class PersonAddressBase(BaseModel):
    address_type: str = "Residential"
    address_line_1: str
    address_line_2: str | None = None
    city: str = "Regina"
    province: str = "Saskatchewan"
    postal_code: str | None = None
    country: str = "Canada"
    on_reserve: bool = False
    is_primary: bool = True
    valid_from: date | None = None
    valid_to: date | None = None


class PersonAddressCreate(PersonAddressBase):
    pass


class PersonAddressResponse(PersonAddressBase):
    id: uuid.UUID
    person_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonContactBase(BaseModel):
    contact_type: str = "Phone"  # Phone, Email, Social, Other
    value: str
    label: str = "Primary"
    is_primary: bool = False
    sms_consent: bool = False
    email_consent: bool = True
    preferred_contact_method: str | None = None


class PersonContactCreate(PersonContactBase):
    pass


class PersonContactResponse(PersonContactBase):
    id: uuid.UUID
    person_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PersonPhysicalDescriptionBase(BaseModel):
    eye_colour: str | None = None
    hair_colour: str | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    tattoos: str | None = None
    piercings: str | None = None
    birthmarks: str | None = None
    scars: str | None = None
    distinguishing_marks: str | None = None
    glasses: bool = False
    contact_lenses: bool = False
    notes: str | None = None


class PersonPhysicalDescriptionCreate(PersonPhysicalDescriptionBase):
    pass


class PersonPhysicalDescriptionUpdate(PersonPhysicalDescriptionBase):
    pass


class PersonPhysicalDescriptionResponse(PersonPhysicalDescriptionBase):
    id: uuid.UUID
    person_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PersonCulturalProfileBase(BaseModel):
    cultural_connections: str | None = None
    ceremonies: str | None = None
    elders_connected: str | None = None
    land_based_activities: str | None = None
    language_goals: str | None = None
    dietary_preferences: str | None = None
    extracurricular_activities: str | None = None
    notes: str | None = None


class PersonCulturalProfileCreate(PersonCulturalProfileBase):
    pass


class PersonCulturalProfileUpdate(PersonCulturalProfileBase):
    pass


class PersonCulturalProfileResponse(PersonCulturalProfileBase):
    id: uuid.UUID
    person_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PersonStrengthBase(BaseModel):
    name: str
    notes: str | None = None


class PersonStrengthCreate(PersonStrengthBase):
    pass


class PersonStrengthResponse(PersonStrengthBase):
    id: uuid.UUID
    person_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class PersonChallengeBase(BaseModel):
    name: str
    severity: str = "Moderate"
    is_active: bool = True
    notes: str | None = None


class PersonChallengeCreate(PersonChallengeBase):
    pass


class PersonChallengeResponse(PersonChallengeBase):
    id: uuid.UUID
    person_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# ── Canonical Person Base, Create & Update ───────────────────────

class PersonBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=200)
    middle_name: str | None = Field(default=None, max_length=200)
    last_name: str = Field(..., min_length=1, max_length=200)
    preferred_name: str | None = Field(default=None, max_length=200)
    aliases: str | None = Field(default=None, max_length=500)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    place_of_birth: str | None = Field(default=None, max_length=200)
    preferred_language: str = Field(default="English", max_length=100)
    languages_spoken: str | None = Field(default=None, max_length=300)

    treaty_number: str | None = Field(default=None, max_length=100)
    band_nation: str | None = Field(default=None, max_length=200)
    indigenous_identity: str | None = Field(default=None, max_length=100)
    health_card_number: str | None = Field(default=None, max_length=100)

    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=320)
    emergency_contact_name: str | None = Field(default=None, max_length=200)
    emergency_contact_phone: str | None = Field(default=None, max_length=50)

    source_of_income: str | None = Field(default=None, max_length=200)
    employment_status: str | None = Field(default=None, max_length=100)
    employer: str | None = Field(default=None, max_length=200)
    employment_details: str | None = None
    notes: str | None = None


class PersonCreate(PersonBase):
    # Optional nested components for comprehensive initial intake
    physical_description: PersonPhysicalDescriptionCreate | None = None
    address: PersonAddressCreate | None = None
    cultural_profile: PersonCulturalProfileCreate | None = None


class PersonUpdate(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None
    preferred_name: str | None = None
    aliases: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    photo_url: str | None = None
    place_of_birth: str | None = None
    preferred_language: str | None = None
    languages_spoken: str | None = None

    treaty_number: str | None = None
    band_nation: str | None = None
    indigenous_identity: str | None = None
    health_card_number: str | None = None

    phone: str | None = None
    email: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    source_of_income: str | None = None
    employment_status: str | None = None
    employer: str | None = None
    employment_details: str | None = None
    notes: str | None = None

    physical_description: PersonPhysicalDescriptionUpdate | None = None
    cultural_profile: PersonCulturalProfileUpdate | None = None


class PersonResponse(PersonBase):
    id: uuid.UUID
    person_id_number: str
    photo_url: str | None = None
    created_at: datetime
    updated_at: datetime

    addresses: list[PersonAddressResponse] = []
    contacts: list[PersonContactResponse] = []
    physical_description: PersonPhysicalDescriptionResponse | None = None
    cultural_profile: PersonCulturalProfileResponse | None = None
    strengths: list[PersonStrengthResponse] = []
    challenges: list[PersonChallengeResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PersonSearchResultResponse(BaseModel):
    """Limited disclosure schema for duplicate-prevention and case-linking search queries."""

    id: uuid.UUID
    person_id_number: str
    first_name: str
    middle_name: str | None = None
    last_name: str
    preferred_name: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ── Aggregated Domain Summary Schemas ────────────────────────────

class PersonCaseSummary(BaseModel):
    case_id: uuid.UUID
    case_number: str
    title: str
    case_type: str
    stage: str
    role_in_case: str
    relationship_to_subject: str | None = None
    is_primary: bool = False
    start_date: date | None = None
    notes: str | None = None


class PersonReferralSummary(BaseModel):
    referral_id: uuid.UUID
    referral_number: str
    status: str
    role: str
    relationship_to_child: str | None = None
    received_date: date | None = None


class PersonRelationshipSummary(BaseModel):
    relationship_id: uuid.UUID
    target_person_id: uuid.UUID
    target_person_id_number: str | None = None
    target_person_name: str
    relationship_type: str
    is_active: bool = True
    family_id: uuid.UUID | None = None
    family_name: str | None = None


class PersonHouseholdSummary(BaseModel):
    household_id: uuid.UUID
    household_name: str
    address: str
    city: str
    province: str
    is_active: bool = True


class PersonPlacementSummary(BaseModel):
    episode_id: uuid.UUID
    case_id: uuid.UUID
    case_number: str | None = None
    placement_type: str
    status: str
    start_date: date
    end_date: date | None = None
    provider_name: str


class PersonBackgroundCheckSummary(BaseModel):
    id: uuid.UUID
    check_type: str
    status: str
    request_date: date
    completion_date: date | None = None
    expiry_date: date | None = None
    is_eligible_for_placement: bool = False


class PersonTimelineSummary(BaseModel):
    id: uuid.UUID
    event_type: str
    title: str
    description: str
    occurred_at: datetime


class PersonDocumentSummary(BaseModel):
    id: uuid.UUID
    filename: str
    content_type: str
    size_bytes: int
    download_url: str
    created_at: datetime


class PersonMedicalSummary(BaseModel):
    dental_notes: str | None = None
    mental_health_notes: str | None = None
    chemical_dependency_history: str | None = None
    general_notes: str | None = None
    primary_physician_name: str | None = None
    primary_physician_phone: str | None = None
    allergies: list[dict[str, Any]] = []
    conditions: list[dict[str, Any]] = []
    medications: list[dict[str, Any]] = []


# ── Full Profile Aggregated Response ─────────────────────────────

class PersonProfileResponse(BaseModel):
    person: PersonResponse
    cases: list[PersonCaseSummary] = []
    referrals: list[PersonReferralSummary] = []
    relationships: list[PersonRelationshipSummary] = []
    households: list[PersonHouseholdSummary] = []
    placements: list[PersonPlacementSummary] = []
    background_checks: list[PersonBackgroundCheckSummary] = []
    timeline: list[PersonTimelineSummary] = []
    documents: list[PersonDocumentSummary] = []
    medical: PersonMedicalSummary | None = None
    schools: list[dict[str, Any]] = []
    providers: list[dict[str, Any]] = []
    client_id: uuid.UUID | None = None


# ── Duplicate Check Schemas ──────────────────────────────────────

class PersonDuplicateCheckRequest(BaseModel):
    first_name: str = ""
    last_name: str = ""
    date_of_birth: str | None = None
    person_id_number: str | None = None
    treaty_number: str | None = None
    health_card_number: str | None = None
    phone: str | None = None
    email: str | None = None


class PersonCandidateResponse(BaseModel):
    """Candidate match schema with minimal disclosure; raw identifier numbers are not exposed."""

    person_id: uuid.UUID
    person_id_number: str | None = None
    first_name: str
    last_name: str
    date_of_birth: str | None = None
    similarity_score: float
    matching_factors: list[str]


class PersonDuplicateCheckResponse(BaseModel):
    has_potential_duplicates: bool
    candidates: list[PersonCandidateResponse]
