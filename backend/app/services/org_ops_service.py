"""Service business logic for Organizational Operations Sprint A."""

import uuid
from datetime import date, timedelta
from typing import Any

from sqlalchemy import func, or_, select
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
from app.models.staffing import StaffingSession
from app.repositories.org_ops_repo import OrgOpsRepository
from app.schemas.hr_dashboard import (
    ExpiringCertificationSummary,
    HRDashboardSummaryResponse,
    MetricAvailability,
    RecentHireSummary,
)


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

    async def get_hr_dashboard_summary(self) -> HRDashboardSummaryResponse:
        today = date.today()
        ninety_days_ago = today - timedelta(days=90)
        thirty_days_future = today + timedelta(days=30)
        session = self.repo.session

        # 1. Total non-deleted employees
        total_emp_res = await session.execute(
            select(func.count(Employee.id)).where(Employee.deleted_at.is_(None))
        )
        total_employees = total_emp_res.scalar() or 0

        # 2. Active employees
        active_emp_res = await session.execute(
            select(func.count(Employee.id)).where(
                Employee.deleted_at.is_(None),
                func.upper(Employee.employment_status) == "ACTIVE",
            )
        )
        active_staff_count = active_emp_res.scalar() or 0

        # 3. On leave employees
        leave_emp_res = await session.execute(
            select(func.count(Employee.id)).where(
                Employee.deleted_at.is_(None),
                func.upper(Employee.employment_status) == "ON_LEAVE",
            )
        )
        on_leave_count = leave_emp_res.scalar() or 0

        # 4. Terminated / Departed employees
        term_emp_res = await session.execute(
            select(func.count(Employee.id)).where(
                Employee.deleted_at.is_(None),
                func.upper(Employee.employment_status) == "TERMINATED",
            )
        )
        terminated_count = term_emp_res.scalar() or 0

        # 5. Recent hires (last 90 days)
        recent_hires_count_res = await session.execute(
            select(func.count(Employee.id)).where(
                Employee.deleted_at.is_(None),
                Employee.hire_date >= ninety_days_ago,
            )
        )
        recent_hires_count = recent_hires_count_res.scalar() or 0

        # 6. Department distribution (active staff)
        dept_res = await session.execute(
            select(Employee.department, func.count(Employee.id))
            .where(
                Employee.deleted_at.is_(None),
                func.upper(Employee.employment_status) == "ACTIVE",
            )
            .group_by(Employee.department)
            .order_by(func.count(Employee.id).desc())
        )
        department_distribution = {dept or "Unassigned": count for dept, count in dept_res.fetchall()}

        # 7. Position distribution (active staff)
        pos_res = await session.execute(
            select(Employee.position, func.count(Employee.id))
            .where(
                Employee.deleted_at.is_(None),
                func.upper(Employee.employment_status) == "ACTIVE",
            )
            .group_by(Employee.position)
            .order_by(func.count(Employee.id).desc())
            .limit(10)
        )
        position_distribution = {pos or "Unassigned": count for pos, count in pos_res.fetchall()}

        # 8. Certifications summary
        total_cert_res = await session.execute(
            select(func.count(EmployeeCertification.id))
        )
        total_certifications = total_cert_res.scalar() or 0

        active_cert_res = await session.execute(
            select(func.count(EmployeeCertification.id)).where(
                func.upper(EmployeeCertification.status) == "ACTIVE",
                or_(EmployeeCertification.expiry_date.is_(None), EmployeeCertification.expiry_date >= today),
            )
        )
        active_certifications = active_cert_res.scalar() or 0

        expiring_soon_res = await session.execute(
            select(func.count(EmployeeCertification.id)).where(
                EmployeeCertification.expiry_date.isnot(None),
                EmployeeCertification.expiry_date >= today,
                EmployeeCertification.expiry_date <= thirty_days_future,
            )
        )
        expiring_soon_count = expiring_soon_res.scalar() or 0

        expired_cert_res = await session.execute(
            select(func.count(EmployeeCertification.id)).where(
                or_(
                    EmployeeCertification.expiry_date < today,
                    func.upper(EmployeeCertification.status) == "EXPIRED",
                )
            )
        )
        expired_certifications_count = expired_cert_res.scalar() or 0

        # Expiring or recently expired certifications with employee details
        exp_certs_query = (
            select(EmployeeCertification, Employee)
            .join(Employee, EmployeeCertification.employee_id == Employee.id)
            .where(
                EmployeeCertification.expiry_date.isnot(None),
                EmployeeCertification.expiry_date <= thirty_days_future,
            )
            .order_by(EmployeeCertification.expiry_date.asc())
            .limit(15)
        )
        exp_certs_rows = (await session.execute(exp_certs_query)).all()
        expiring_certifications = [
            ExpiringCertificationSummary(
                id=cert.id,
                employee_id=emp.id,
                employee_name=f"{emp.first_name} {emp.last_name}".strip(),
                department=emp.department,
                cert_type=cert.cert_type,
                identifier=cert.identifier,
                issued_date=cert.issued_date,
                expiry_date=cert.expiry_date,
                status="EXPIRED" if cert.expiry_date and cert.expiry_date < today else (
                    "EXPIRING" if cert.expiry_date and cert.expiry_date <= thirty_days_future else cert.status
                ),
                days_until_expiry=(cert.expiry_date - today).days if cert.expiry_date else None,
            )
            for cert, emp in exp_certs_rows
        ]

        # 9. Recent hires list
        recent_hires_query = (
            select(Employee)
            .where(Employee.deleted_at.is_(None))
            .order_by(Employee.hire_date.desc())
            .limit(10)
        )
        recent_hires_rows = (await session.execute(recent_hires_query)).scalars().all()
        recent_hires = [
            RecentHireSummary(
                id=emp.id,
                employee_number=emp.employee_number,
                first_name=emp.first_name,
                last_name=emp.last_name,
                position=emp.position,
                department=emp.department,
                hire_date=emp.hire_date,
                photo_url=emp.photo_url,
            )
            for emp in recent_hires_rows
        ]

        # 10. Staffing sessions summary
        try:
            total_staffing_res = await session.execute(
                select(func.count(StaffingSession.id)).where(StaffingSession.deleted_at.is_(None))
            )
            total_staffing_sessions = total_staffing_res.scalar() or 0

            recent_staffing_res = await session.execute(
                select(func.count(StaffingSession.id)).where(
                    StaffingSession.deleted_at.is_(None),
                    StaffingSession.session_date >= ninety_days_ago,
                )
            )
            recent_staffing_sessions_count = recent_staffing_res.scalar() or 0
        except Exception:
            total_staffing_sessions = 0
            recent_staffing_sessions_count = 0

        return HRDashboardSummaryResponse(
            total_employees=total_employees,
            active_staff_count=active_staff_count,
            on_leave_count=on_leave_count,
            terminated_count=terminated_count,
            recent_hires_count=recent_hires_count,
            department_distribution=department_distribution,
            position_distribution=position_distribution,
            total_certifications=total_certifications,
            active_certifications=active_certifications,
            expiring_soon_count=expiring_soon_count,
            expired_certifications_count=expired_certifications_count,
            expiring_certifications=expiring_certifications,
            recent_hires=recent_hires,
            total_staffing_sessions=total_staffing_sessions,
            recent_staffing_sessions_count=recent_staffing_sessions_count,
            fte_metrics=MetricAvailability(
                value=None,
                is_available=False,
                reason="Full-Time Equivalent (FTE) vs Part-Time contract hours are not modeled in current Employee schema.",
            ),
            turnover_rate=MetricAvailability(
                value=None,
                is_available=False,
                reason="Formal historical turnover rate methodology requires HR governance retention targets.",
            ),
            retention_targets=MetricAvailability(
                value=None,
                is_available=False,
                reason="Retention targets have not been established by CRBCL HR policy.",
            ),
            leave_balances=MetricAvailability(
                value=None,
                is_available=False,
                reason="Accrued vacation and sick leave bank balances are not stored in database.",
            ),
            formal_onboarding_pipeline=MetricAvailability(
                value=None,
                is_available=False,
                reason="Multi-stage employee onboarding/offboarding workflows are not yet modeled as state-machine tables.",
            ),
        )

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
