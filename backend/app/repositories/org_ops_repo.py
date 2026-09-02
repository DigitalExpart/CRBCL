"""Repositories for Sprint A Organizational Operations models."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.org_ops import (
    AssetAssignment,
    Donation,
    Donor,
    Employee,
    EmployeeCertification,
    Facility,
    FacilityInspection,
    FacilityWorkOrder,
    HousingOccupancy,
    HousingUnit,
    ITAsset,
    Volunteer,
    VolunteerHour,
)
from app.services.integrations.utils import db_commit, db_query_all, db_query_first


class OrgOpsRepository:
    """Unified repository for organizational operational domains."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # 1. HR / Employee Repository Methods
    async def create_employee(self, employee: Employee) -> Employee:
        self.session.add(employee)
        await db_commit(self.session)
        return employee

    async def get_employee_by_id(self, employee_id: uuid.UUID) -> Employee | None:
        return await db_query_first(self.session, Employee, Employee.id == employee_id)

    async def list_employees(self) -> list[Employee]:
        return await db_query_all(self.session, Employee)

    async def create_employee_certification(self, cert: EmployeeCertification) -> EmployeeCertification:
        self.session.add(cert)
        await db_commit(self.session)
        return cert

    # 2. Housing Repository Methods
    async def create_housing_unit(self, unit: HousingUnit) -> HousingUnit:
        self.session.add(unit)
        await db_commit(self.session)
        return unit

    async def list_housing_units(self) -> list[HousingUnit]:
        return await db_query_all(self.session, HousingUnit)

    async def create_housing_occupancy(self, occupancy: HousingOccupancy) -> HousingOccupancy:
        self.session.add(occupancy)
        await db_commit(self.session)
        return occupancy

    # 3. Facilities Repository Methods
    async def create_facility(self, facility: Facility) -> Facility:
        self.session.add(facility)
        await db_commit(self.session)
        return facility

    async def list_facilities(self) -> list[Facility]:
        return await db_query_all(self.session, Facility)

    async def create_work_order(self, work_order: FacilityWorkOrder) -> FacilityWorkOrder:
        self.session.add(work_order)
        await db_commit(self.session)
        return work_order

    async def list_work_orders(self) -> list[FacilityWorkOrder]:
        return await db_query_all(self.session, FacilityWorkOrder)

    async def create_facility_inspection(self, inspection: FacilityInspection) -> FacilityInspection:
        self.session.add(inspection)
        await db_commit(self.session)
        return inspection

    # 4. IT Assets Repository Methods
    async def create_asset(self, asset: ITAsset) -> ITAsset:
        self.session.add(asset)
        await db_commit(self.session)
        return asset

    async def list_assets(self) -> list[ITAsset]:
        return await db_query_all(self.session, ITAsset)

    async def assign_asset(self, assignment: AssetAssignment) -> AssetAssignment:
        self.session.add(assignment)
        await db_commit(self.session)
        return assignment

    # 5. Donations Repository Methods
    async def create_donor(self, donor: Donor) -> Donor:
        self.session.add(donor)
        await db_commit(self.session)
        return donor

    async def list_donors(self) -> list[Donor]:
        return await db_query_all(self.session, Donor)

    async def create_donation(self, donation: Donation) -> Donation:
        self.session.add(donation)
        await db_commit(self.session)
        return donation

    async def list_donations(self) -> list[Donation]:
        return await db_query_all(self.session, Donation)

    # 6. Volunteer Repository Methods
    async def create_volunteer(self, volunteer: Volunteer) -> Volunteer:
        self.session.add(volunteer)
        await db_commit(self.session)
        return volunteer

    async def list_volunteers(self) -> list[Volunteer]:
        return await db_query_all(self.session, Volunteer)

    async def create_volunteer_hour_log(self, hour_log: VolunteerHour) -> VolunteerHour:
        self.session.add(hour_log)
        await db_commit(self.session)
        return hour_log

    async def list_volunteer_hours(self) -> list[VolunteerHour]:
        return await db_query_all(self.session, VolunteerHour)
