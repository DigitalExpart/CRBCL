"""Service business logic for Organizational Operations Sprint A."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_ops import (
    Donation,
    Donor,
    Employee,
    EmployeeCertification,
    Facility,
    FacilityWorkOrder,
    HousingOccupancy,
    HousingUnit,
    ITAsset,
    Volunteer,
    VolunteerHour,
)
from app.repositories.org_ops_repo import OrgOpsRepository


class OrgOpsService:
    """Business logic coordinator for organizational operational domains."""

    def __init__(self, session: AsyncSession):
        self.repo = OrgOpsRepository(session)

    # 1. HR / Employee
    async def create_employee(self, data: dict[str, Any]) -> Employee:
        emp = Employee(
            user_id=data.get("user_id"),
            employee_number=data["employee_number"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data.get("phone"),
            position=data["position"],
            department=data["department"],
            employment_status=data.get("employment_status", "ACTIVE"),
            hire_date=data["hire_date"],
            end_date=data.get("end_date"),
            supervisor_employee_id=data.get("supervisor_employee_id"),
            photo_url=data.get("photo_url"),
        )
        return await self.repo.create_employee(emp)

    async def list_employees(self) -> list[Employee]:
        return await self.repo.list_employees()

    async def add_certification(self, employee_id: uuid.UUID, data: dict[str, Any]) -> EmployeeCertification:
        cert = EmployeeCertification(
            employee_id=employee_id,
            cert_type=data["cert_type"],
            identifier=data.get("identifier"),
            issued_date=data["issued_date"],
            expiry_date=data.get("expiry_date"),
            status=data.get("status", "ACTIVE"),
        )
        return await self.repo.create_employee_certification(cert)

    # 2. Housing
    async def create_housing_unit(self, data: dict[str, Any]) -> HousingUnit:
        unit = HousingUnit(
            unit_number=data["unit_number"],
            name=data["name"],
            address=data["address"],
            unit_type=data.get("unit_type", "APARTMENT"),
            status=data.get("status", "AVAILABLE"),
            bedrooms=data.get("bedrooms", 1),
            capacity=data.get("capacity", 1),
            accessibility_features=data.get("accessibility_features"),
            notes=data.get("notes"),
        )
        return await self.repo.create_housing_unit(unit)

    async def list_housing_units(self) -> list[HousingUnit]:
        return await self.repo.list_housing_units()

    async def add_occupancy(self, data: dict[str, Any]) -> HousingOccupancy:
        occupancy = HousingOccupancy(
            unit_id=uuid.UUID(data["unit_id"]),
            person_id=uuid.UUID(data["person_id"]),
            start_date=data["start_date"],
            end_date=data.get("end_date"),
            status=data.get("status", "ACTIVE"),
            notes=data.get("notes"),
        )
        return await self.repo.create_housing_occupancy(occupancy)

    # 3. Facilities
    async def create_facility(self, data: dict[str, Any]) -> Facility:
        fac = Facility(
            name=data["name"],
            facility_type=data.get("facility_type", "OFFICE"),
            address=data["address"],
            status=data.get("status", "OPERATIONAL"),
            notes=data.get("notes"),
        )
        return await self.repo.create_facility(fac)

    async def list_facilities(self) -> list[Facility]:
        return await self.repo.list_facilities()

    async def create_work_order(self, data: dict[str, Any]) -> FacilityWorkOrder:
        wo = FacilityWorkOrder(
            facility_id=uuid.UUID(data["facility_id"]),
            reported_by_id=data.get("reported_by_id"),
            assigned_to_employee_id=data.get("assigned_to_employee_id"),
            category=data.get("category", "General Maintenance"),
            priority=data.get("priority", "MEDIUM"),
            description=data["description"],
            status=data.get("status", "OPEN"),
        )
        return await self.repo.create_work_order(wo)

    async def list_work_orders(self) -> list[FacilityWorkOrder]:
        return await self.repo.list_work_orders()

    # 4. IT Assets
    async def create_asset(self, data: dict[str, Any]) -> ITAsset:
        asset = ITAsset(
            asset_tag=data["asset_tag"],
            asset_type=data.get("asset_type", "LAPTOP"),
            manufacturer=data["manufacturer"],
            model=data["model"],
            serial_number=data["serial_number"],
            purchase_date=data.get("purchase_date"),
            warranty_expiry=data.get("warranty_expiry"),
            status=data.get("status", "AVAILABLE"),
            location=data.get("location"),
            notes=data.get("notes"),
        )
        return await self.repo.create_asset(asset)

    async def list_assets(self) -> list[ITAsset]:
        return await self.repo.list_assets()

    # 5. Donations
    async def create_donor(self, data: dict[str, Any]) -> Donor:
        donor = Donor(
            donor_type=data.get("donor_type", "INDIVIDUAL"),
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            organization_name=data.get("organization_name"),
            notes=data.get("notes"),
        )
        return await self.repo.create_donor(donor)

    async def list_donors(self) -> list[Donor]:
        return await self.repo.list_donors()

    async def create_donation(self, data: dict[str, Any]) -> Donation:
        donation = Donation(
            donor_id=uuid.UUID(data["donor_id"]),
            amount=data["amount"],
            donation_type=data.get("donation_type", "MONETARY"),
            payment_method=data.get("payment_method", "CHEQUE"),
            designation=data.get("designation", "General Fund"),
            status=data.get("status", "COMPLETED"),
            receipt_number=data.get("receipt_number"),
            receipt_issued=data.get("receipt_issued", False),
            issued_date=data.get("issued_date"),
            notes=data.get("notes"),
        )
        return await self.repo.create_donation(donation)

    async def list_donations(self) -> list[Donation]:
        return await self.repo.list_donations()

    # 6. Volunteers
    async def create_volunteer(self, data: dict[str, Any]) -> Volunteer:
        vol = Volunteer(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            phone=data.get("phone"),
            status=data.get("status", "APPLIED"),
            availability=data.get("availability"),
            skills=data.get("skills"),
            interests=data.get("interests"),
        )
        return await self.repo.create_volunteer(vol)

    async def list_volunteers(self) -> list[Volunteer]:
        return await self.repo.list_volunteers()

    async def log_volunteer_hours(self, data: dict[str, Any]) -> VolunteerHour:
        log = VolunteerHour(
            volunteer_id=uuid.UUID(data["volunteer_id"]),
            service_date=data["service_date"],
            hours=data["hours"],
            program_name=data["program_name"],
            description=data.get("description"),
        )
        return await self.repo.create_volunteer_hour_log(log)

    async def list_volunteer_hours(self) -> list[VolunteerHour]:
        return await self.repo.list_volunteer_hours()
