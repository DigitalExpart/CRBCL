"""Automated Test Suite for Sprint A — Organizational Operations & Domain Security Isolation."""

import uuid
from datetime import date

import pytest
from fastapi import HTTPException

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
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.services.org_ops_service import OrgOpsService


@pytest.mark.asyncio
async def test_employee_crud_and_certification(db_session):
    """Verify native Employee creation, listing, and certification attachment."""
    service = OrgOpsService(db_session)

    emp_data = {
        "employee_number": f"EMP-{uuid.uuid4().hex[:6].upper()}",
        "first_name": "Jane",
        "last_name": "Staff",
        "email": "jane.staff@crbcl.ca",
        "position": "Social Worker",
        "department": "Child & Family Services",
        "hire_date": date(2026, 1, 15),
    }
    emp = await service.create_employee(emp_data)
    assert emp.id is not None
    assert emp.employee_number == emp_data["employee_number"]

    cert_data = {
        "cert_type": "RSW License",
        "identifier": "RSW-998877",
        "issued_date": date(2026, 1, 1),
        "expiry_date": date(2027, 1, 1),
    }
    cert = await service.add_certification(emp.id, cert_data)
    assert cert.id is not None
    assert cert.cert_type == "RSW License"

    employees = await service.list_employees()
    assert len(employees) >= 1


@pytest.mark.asyncio
async def test_housing_units_and_facilities(db_session):
    """Verify HousingUnit and Facility work order lifecycle."""
    service = OrgOpsService(db_session)

    unit_data = {
        "unit_number": f"U-{uuid.uuid4().hex[:4].upper()}",
        "name": "CRBCL Transition Unit 4",
        "address": "123 Sacred Wolf Way",
        "bedrooms": 2,
        "capacity": 3,
    }
    unit = await service.create_housing_unit(unit_data)
    assert unit.id is not None
    assert unit.name == unit_data["name"]

    fac_data = {
        "name": "Meadow Lake Regional Office",
        "facility_type": "OFFICE",
        "address": "456 Community Drive",
    }
    fac = await service.create_facility(fac_data)
    assert fac.id is not None

    wo_data = {
        "facility_id": str(fac.id),
        "description": "HVAC filter replacement",
        "priority": "HIGH",
    }
    wo = await service.create_work_order(wo_data)
    assert wo.id is not None
    assert wo.status == "OPEN"


@pytest.mark.asyncio
async def test_it_assets_donations_and_volunteers(db_session):
    """Verify IT Assets, Donations (Decimal amount precision), and Volunteers."""
    service = OrgOpsService(db_session)

    # IT Asset
    asset_data = {
        "asset_tag": f"TAG-{uuid.uuid4().hex[:5].upper()}",
        "asset_type": "LAPTOP",
        "manufacturer": "Dell",
        "model": "Latitude 5540",
        "serial_number": f"SN-{uuid.uuid4().hex[:8].upper()}",
    }
    asset = await service.create_asset(asset_data)
    assert asset.id is not None

    # Donor & Donation
    donor_data = {
        "name": "Northern Foundation",
        "donor_type": "FOUNDATION",
        "email": "contact@northernfn.org",
    }
    donor = await service.create_donor(donor_data)

    donation_data = {
        "donor_id": str(donor.id),
        "amount": 12500.50,
        "designation": "Youth Cultural Program",
    }
    donation = await service.create_donation(donation_data)
    assert float(donation.amount) == 12500.50

    # Volunteer & Hours
    vol_data = {
        "first_name": "Alex",
        "last_name": "Volunteer",
        "email": f"alex.vol.{uuid.uuid4().hex[:4]}@crbcl.ca",
    }
    vol = await service.create_volunteer(vol_data)

    hour_data = {
        "volunteer_id": str(vol.id),
        "service_date": date(2026, 2, 1),
        "hours": 4.5,
        "program_name": "Sacred Wolf Mentorship",
    }
    log = await service.log_volunteer_hours(hour_data)
    assert float(log.hours) == 4.5


def test_org_ops_permission_constants():
    """Verify organizational domain permission strings are correctly bound."""
    assert Permissions.HR_EMPLOYEE_READ == "hr.employee.read"
    assert Permissions.HR_EMPLOYEE_CREATE == "hr.employee.create"
    assert Permissions.HOUSING_UNIT_READ == "housing.unit.read"
    assert Permissions.HOUSING_UNIT_MANAGE == "housing.unit.manage"
    assert Permissions.FACILITIES_READ == "facilities.facility.read"
    assert Permissions.FACILITIES_WORKORDER_MANAGE == "facilities.workorder.manage"
    assert Permissions.ASSET_ITEM_READ == "asset.item.read"
    assert Permissions.DONATION_DONOR_READ == "donation.donor.read"
    assert Permissions.VOLUNTEER_RECORD_READ == "volunteer.record.read"
