"""API Router for Sprint A Organizational Operations (HR, Housing, Facilities, IT Assets, Donations, Volunteers)."""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.permissions.constants import Permissions
from app.permissions.dependencies import require_permission
from app.services.org_ops_service import OrgOpsService

router = APIRouter()


# ==========================================
# 1. HR / EMPLOYEES
# ==========================================


class EmployeeCreate(BaseModel):
    employee_number: str
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    position: str
    department: str
    employment_status: str = "ACTIVE"
    hire_date: date
    end_date: date | None = None
    user_id: uuid.UUID | None = None
    supervisor_employee_id: uuid.UUID | None = None
    photo_url: str | None = None


class CertificationCreate(BaseModel):
    cert_type: str
    identifier: str | None = None
    issued_date: date
    expiry_date: date | None = None
    status: str = "ACTIVE"


@router.post("/employees", response_model=dict[str, Any])
async def create_employee(
    req: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HR_EMPLOYEE_CREATE)),
):
    service = OrgOpsService(db)
    emp = await service.create_employee(req.model_dump())
    return {"status": "SUCCESS", "id": str(emp.id), "employee_number": emp.employee_number}


@router.get("/employees", response_model=list[dict[str, Any]])
async def list_employees(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HR_EMPLOYEE_READ)),
):
    service = OrgOpsService(db)
    employees = await service.list_employees()
    return [
        {
            "id": str(e.id),
            "employee_number": e.employee_number,
            "first_name": e.first_name,
            "last_name": e.last_name,
            "email": e.email,
            "phone": e.phone,
            "position": e.position,
            "department": e.department,
            "employment_status": e.employment_status,
            "hire_date": e.hire_date.isoformat(),
        }
        for e in employees
    ]


@router.post("/employees/{employee_id}/certifications", response_model=dict[str, Any])
async def add_employee_certification(
    employee_id: uuid.UUID,
    req: CertificationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HR_CERTIFICATION_MANAGE)),
):
    service = OrgOpsService(db)
    cert = await service.add_certification(employee_id, req.model_dump())
    return {"status": "SUCCESS", "id": str(cert.id), "cert_type": cert.cert_type}


# ==========================================
# 2. HOUSING UNITS
# ==========================================


class HousingUnitCreate(BaseModel):
    unit_number: str
    name: str
    address: str
    unit_type: str = "APARTMENT"
    status: str = "AVAILABLE"
    bedrooms: int = 1
    capacity: int = 1
    accessibility_features: str | None = None
    notes: str | None = None


class HousingOccupancyCreate(BaseModel):
    unit_id: str
    person_id: str
    start_date: date
    end_date: date | None = None
    status: str = "ACTIVE"
    notes: str | None = None


@router.post("/housing/units", response_model=dict[str, Any])
async def create_housing_unit(
    req: HousingUnitCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HOUSING_UNIT_MANAGE)),
):
    service = OrgOpsService(db)
    unit = await service.create_housing_unit(req.model_dump())
    return {"status": "SUCCESS", "id": str(unit.id), "unit_number": unit.unit_number}


@router.get("/housing/units", response_model=list[dict[str, Any]])
async def list_housing_units(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HOUSING_UNIT_READ)),
):
    service = OrgOpsService(db)
    units = await service.list_housing_units()
    return [
        {
            "id": str(u.id),
            "unit_number": u.unit_number,
            "name": u.name,
            "address": u.address,
            "unit_type": u.unit_type,
            "status": u.status,
            "capacity": u.capacity,
        }
        for u in units
    ]


@router.post("/housing/occupancies", response_model=dict[str, Any])
async def create_housing_occupancy(
    req: HousingOccupancyCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.HOUSING_OCCUPANCY_MANAGE)),
):
    service = OrgOpsService(db)
    occ = await service.add_occupancy(req.model_dump())
    return {"status": "SUCCESS", "id": str(occ.id), "unit_id": str(occ.unit_id)}


# ==========================================
# 3. FACILITIES & WORK ORDERS
# ==========================================


class FacilityCreate(BaseModel):
    name: str
    facility_type: str = "OFFICE"
    address: str
    status: str = "OPERATIONAL"
    notes: str | None = None


class WorkOrderCreate(BaseModel):
    facility_id: str
    description: str
    category: str = "General Maintenance"
    priority: str = "MEDIUM"
    status: str = "OPEN"


@router.post("/facilities", response_model=dict[str, Any])
async def create_facility(
    req: FacilityCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.FACILITIES_MANAGE)),
):
    service = OrgOpsService(db)
    fac = await service.create_facility(req.model_dump())
    return {"status": "SUCCESS", "id": str(fac.id), "name": fac.name}


@router.get("/facilities", response_model=list[dict[str, Any]])
async def list_facilities(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.FACILITIES_READ)),
):
    service = OrgOpsService(db)
    facilities = await service.list_facilities()
    return [
        {
            "id": str(f.id),
            "name": f.name,
            "facility_type": f.facility_type,
            "address": f.address,
            "status": f.status,
        }
        for f in facilities
    ]


@router.post("/facilities/work-orders", response_model=dict[str, Any])
async def create_work_order(
    req: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.FACILITIES_WORKORDER_MANAGE)),
):
    service = OrgOpsService(db)
    wo = await service.create_work_order(req.model_dump())
    return {"status": "SUCCESS", "id": str(wo.id), "work_order_status": wo.status}


@router.get("/facilities/work-orders", response_model=list[dict[str, Any]])
async def list_work_orders(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.FACILITIES_READ)),
):
    service = OrgOpsService(db)
    orders = await service.list_work_orders()
    return [
        {
            "id": str(w.id),
            "facility_id": str(w.facility_id),
            "category": w.category,
            "priority": w.priority,
            "description": w.description,
            "status": w.status,
        }
        for w in orders
    ]


# ==========================================
# 4. IT ASSET MANAGEMENT
# ==========================================


class ITAssetCreate(BaseModel):
    asset_tag: str
    asset_type: str = "LAPTOP"
    manufacturer: str
    model: str
    serial_number: str
    purchase_date: date | None = None
    warranty_expiry: date | None = None
    status: str = "AVAILABLE"
    location: str | None = None


@router.post("/assets", response_model=dict[str, Any])
async def create_asset(
    req: ITAssetCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.ASSET_ITEM_MANAGE)),
):
    service = OrgOpsService(db)
    asset = await service.create_asset(req.model_dump())
    return {"status": "SUCCESS", "id": str(asset.id), "asset_tag": asset.asset_tag}


@router.get("/assets", response_model=list[dict[str, Any]])
async def list_assets(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.ASSET_ITEM_READ)),
):
    service = OrgOpsService(db)
    assets = await service.list_assets()
    return [
        {
            "id": str(a.id),
            "asset_tag": a.asset_tag,
            "asset_type": a.asset_type,
            "manufacturer": a.manufacturer,
            "model": a.model,
            "serial_number": a.serial_number,
            "status": a.status,
        }
        for a in assets
    ]


# ==========================================
# 5. DONATIONS & FUNDRAISING
# ==========================================


class DonorCreate(BaseModel):
    name: str
    donor_type: str = "INDIVIDUAL"
    email: str | None = None
    phone: str | None = None
    organization_name: str | None = None


class DonationCreate(BaseModel):
    donor_id: str
    amount: float
    donation_type: str = "MONETARY"
    payment_method: str = "CHEQUE"
    designation: str = "General Fund"
    status: str = "COMPLETED"
    receipt_number: str | None = None
    receipt_issued: bool = False
    issued_date: date | None = None


@router.post("/donations/donors", response_model=dict[str, Any])
async def create_donor(
    req: DonorCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.DONATION_DONOR_MANAGE)),
):
    service = OrgOpsService(db)
    donor = await service.create_donor(req.model_dump())
    return {"status": "SUCCESS", "id": str(donor.id), "name": donor.name}


@router.get("/donations/donors", response_model=list[dict[str, Any]])
async def list_donors(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.DONATION_DONOR_READ)),
):
    service = OrgOpsService(db)
    donors = await service.list_donors()
    return [
        {
            "id": str(d.id),
            "name": d.name,
            "donor_type": d.donor_type,
            "email": d.email,
            "organization_name": d.organization_name,
        }
        for d in donors
    ]


@router.post("/donations", response_model=dict[str, Any])
async def create_donation(
    req: DonationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.DONATION_RECORD_MANAGE)),
):
    service = OrgOpsService(db)
    donation = await service.create_donation(req.model_dump())
    return {"status": "SUCCESS", "id": str(donation.id), "amount": float(donation.amount)}


@router.get("/donations", response_model=list[dict[str, Any]])
async def list_donations(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.DONATION_DONOR_READ)),
):
    service = OrgOpsService(db)
    donations = await service.list_donations()
    return [
        {
            "id": str(d.id),
            "donor_id": str(d.donor_id),
            "amount": float(d.amount),
            "donation_type": d.donation_type,
            "payment_method": d.payment_method,
            "designation": d.designation,
            "status": d.status,
            "receipt_issued": d.receipt_issued,
        }
        for d in donations
    ]


# ==========================================
# 6. VOLUNTEER COORDINATION
# ==========================================


class VolunteerCreate(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    status: str = "APPLIED"
    availability: str | None = None
    skills: str | None = None
    interests: str | None = None


class VolunteerHourLogCreate(BaseModel):
    volunteer_id: str
    service_date: date
    hours: float
    program_name: str
    description: str | None = None


@router.post("/volunteers", response_model=dict[str, Any])
async def create_volunteer(
    req: VolunteerCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.VOLUNTEER_RECORD_MANAGE)),
):
    service = OrgOpsService(db)
    vol = await service.create_volunteer(req.model_dump())
    return {"status": "SUCCESS", "id": str(vol.id), "email": vol.email}


@router.get("/volunteers", response_model=list[dict[str, Any]])
async def list_volunteers(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.VOLUNTEER_RECORD_READ)),
):
    service = OrgOpsService(db)
    volunteers = await service.list_volunteers()
    return [
        {
            "id": str(v.id),
            "first_name": v.first_name,
            "last_name": v.last_name,
            "email": v.email,
            "status": v.status,
        }
        for v in volunteers
    ]


@router.post("/volunteers/hours", response_model=dict[str, Any])
async def log_volunteer_hours(
    req: VolunteerHourLogCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.VOLUNTEER_HOURS_MANAGE)),
):
    service = OrgOpsService(db)
    log = await service.log_volunteer_hours(req.model_dump())
    return {"status": "SUCCESS", "id": str(log.id), "hours": float(log.hours)}


@router.get("/volunteers/hours", response_model=list[dict[str, Any]])
async def list_volunteer_hours(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permissions.VOLUNTEER_RECORD_READ)),
):
    service = OrgOpsService(db)
    logs = await service.list_volunteer_hours()
    return [
        {
            "id": str(log.id),
            "volunteer_id": str(log.volunteer_id),
            "service_date": log.service_date.isoformat(),
            "hours": float(log.hours),
            "program_name": log.program_name,
        }
        for log in logs
    ]
