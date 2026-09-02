"""Sprint A — Organizational Operations SQLAlchemy Models (HR, Housing, Facilities, IT Assets, Donations, Volunteers)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import AuditMixin, Base, SoftDeleteMixin

# ==========================================
# 1. HUMAN RESOURCES (HR & CERTIFICATIONS)
# ==========================================


class Employee(Base, AuditMixin, SoftDeleteMixin):
    """Native Employee record linked optionally to User login."""

    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    employment_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, ON_LEAVE, TERMINATED
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    supervisor_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="joined")
    supervisor = relationship("Employee", remote_side=[id], lazy="selectin")
    certifications = relationship("EmployeeCertification", back_populates="employee", cascade="all, delete-orphan")


class EmployeeCertification(Base, AuditMixin):
    """Employee professional certification and license tracking."""

    __tablename__ = "employee_certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cert_type: Mapped[str] = mapped_column(String(100), nullable=False)  # CPR, Social Work License, First Aid
    identifier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    issued_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, EXPIRING, EXPIRED
    document_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )

    employee = relationship("Employee", back_populates="certifications")


# ==========================================
# 2. HOUSING (ORGANIZATIONAL HOUSING UNITS)
# ==========================================


class HousingUnit(Base, AuditMixin, SoftDeleteMixin):
    """Organizational housing unit or shelter facility."""

    __tablename__ = "housing_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    unit_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="APARTMENT"
    )  # APARTMENT, HOUSE, SHELTER_BED, SUITE
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AVAILABLE", index=True
    )  # AVAILABLE, OCCUPIED, MAINTENANCE, UNAVAILABLE
    bedrooms: Mapped[int] = mapped_column(nullable=False, default=1)
    capacity: Mapped[int] = mapped_column(nullable=False, default=1)
    accessibility_features: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    occupancies = relationship("HousingOccupancy", back_populates="unit", cascade="all, delete-orphan")


class HousingOccupancy(Base, AuditMixin):
    """Occupancy tracking linking Person/Family to HousingUnit."""

    __tablename__ = "housing_occupancies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("housing_units.id", ondelete="CASCADE"), nullable=False, index=True
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="ACTIVE", index=True
    )  # ACTIVE, COMPLETED, TERMINATED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    unit = relationship("HousingUnit", back_populates="occupancies")
    person = relationship("Person", foreign_keys=[person_id], lazy="joined")


# ==========================================
# 3. FACILITIES & MAINTENANCE WORK ORDERS
# ==========================================


class Facility(Base, AuditMixin, SoftDeleteMixin):
    """CRBCL building, office, or program site."""

    __tablename__ = "facilities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    facility_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OFFICE"
    )  # OFFICE, PROGRAM_SITE, SHELTER, RESIDENCE
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OPERATIONAL", index=True
    )  # OPERATIONAL, MAINTENANCE, CLOSED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    work_orders = relationship("FacilityWorkOrder", back_populates="facility", cascade="all, delete-orphan")
    inspections = relationship("FacilityInspection", back_populates="facility", cascade="all, delete-orphan")


class FacilityWorkOrder(Base, AuditMixin):
    """Facility maintenance work order."""

    __tablename__ = "facility_work_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reported_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_to_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="General Maintenance")
    priority: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MEDIUM", index=True
    )  # LOW, MEDIUM, HIGH, URGENT
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="OPEN", index=True
    )  # OPEN, ASSIGNED, IN_PROGRESS, ON_HOLD, COMPLETED, CANCELLED
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    facility = relationship("Facility", back_populates="work_orders")


class FacilityInspection(Base, AuditMixin):
    """Facility safety and structural inspection."""

    __tablename__ = "facility_inspections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    facility_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspection_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Fire Safety, HVAC, Structural, Routine
    inspection_date: Mapped[date] = mapped_column(Date, nullable=False)
    inspector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    result: Mapped[str] = mapped_column(String(50), nullable=False, default="PASSED")  # PASSED, NEEDS_ACTION, FAILED
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    facility = relationship("Facility", back_populates="inspections")


# ==========================================
# 4. IT ASSET MANAGEMENT
# ==========================================


class ITAsset(Base, AuditMixin, SoftDeleteMixin):
    """Hardware inventory item (laptop, desktop, phone, etc.)."""

    __tablename__ = "it_assets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_tag: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="LAPTOP"
    )  # LAPTOP, DESKTOP, MONITOR, TABLET, PRINTER
    manufacturer: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    warranty_expiry: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="AVAILABLE", index=True
    )  # AVAILABLE, ASSIGNED, REPAIR, LOST, RETIRED
    assigned_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True, index=True
    )
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    assigned_employee = relationship("Employee", foreign_keys=[assigned_employee_id], lazy="joined")
    assignments = relationship("AssetAssignment", back_populates="asset", cascade="all, delete-orphan")


class AssetAssignment(Base, AuditMixin):
    """Hardware asset assignment history."""

    __tablename__ = "asset_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("it_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    condition_on_assignment: Mapped[str | None] = mapped_column(String(100), nullable=True, default="NEW")
    condition_on_return: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    asset = relationship("ITAsset", back_populates="assignments")
    employee = relationship("Employee", foreign_keys=[employee_id], lazy="joined")


# ==========================================
# 5. DONATIONS & FUNDRAISING
# ==========================================


class Donor(Base, AuditMixin, SoftDeleteMixin):
    """Donor profile (Individual, Corporate, Foundation)."""

    __tablename__ = "donors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="INDIVIDUAL"
    )  # INDIVIDUAL, CORPORATE, FOUNDATION
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    organization_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    donations = relationship("Donation", back_populates="donor", cascade="all, delete-orphan")


class Donation(Base, AuditMixin):
    """Donation transaction record with exact Decimal precision."""

    __tablename__ = "donations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    donor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    donation_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="MONETARY"
    )  # MONETARY, IN_KIND, GRANT, CRYPTOCURRENCY_METADATA
    payment_method: Mapped[str] = mapped_column(
        String(50), nullable=False, default="CHEQUE"
    )  # CASH, CHEQUE, CARD, E_TRANSFER, OTHER
    designation: Mapped[str] = mapped_column(String(200), nullable=False, default="General Fund")
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="COMPLETED", index=True
    )  # PENDING, COMPLETED, REFUNDED
    receipt_number: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True, index=True)
    receipt_issued: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    donor = relationship("Donor", back_populates="donations")


class FundraisingCampaign(Base, AuditMixin):
    """Fundraising campaign or project target."""

    __tablename__ = "fundraising_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    target_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, COMPLETED, CANCELLED


# ==========================================
# 6. VOLUNTEER COORDINATION
# ==========================================


class Volunteer(Base, AuditMixin, SoftDeleteMixin):
    """Volunteer profile."""

    __tablename__ = "volunteers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"), nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="APPLIED", index=True
    )  # APPLIED, UNDER_REVIEW, APPROVED, DECLINED, INACTIVE
    availability: Mapped[str | None] = mapped_column(String(200), nullable=True)
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests: Mapped[str | None] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    background_check_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("background_checks.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    applications = relationship("VolunteerApplication", back_populates="volunteer", cascade="all, delete-orphan")
    assignments = relationship("VolunteerAssignment", back_populates="volunteer", cascade="all, delete-orphan")
    hours = relationship("VolunteerHour", back_populates="volunteer", cascade="all, delete-orphan")


class VolunteerApplication(Base, AuditMixin):
    """Volunteer application review process."""

    __tablename__ = "volunteer_applications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    volunteer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="UNDER_REVIEW")
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    volunteer = relationship("Volunteer", back_populates="applications")


class VolunteerAssignment(Base, AuditMixin):
    """Volunteer role assignment."""

    __tablename__ = "volunteer_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    volunteer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role_title: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    supervisor_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True
    )

    volunteer = relationship("Volunteer", back_populates="assignments")


class VolunteerHour(Base, AuditMixin):
    """Volunteer service hours log."""

    __tablename__ = "volunteer_hours"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    volunteer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("volunteers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    program_name: Mapped[str] = mapped_column(String(200), nullable=False)
    approved_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    volunteer = relationship("Volunteer", back_populates="hours")
