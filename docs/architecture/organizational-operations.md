# CRBCL Architecture — Completion Sprint A (Organizational Operations)

**Date**: September 2, 2026  
**Status**: APPROVED & IMPLEMENTED  
**Revision**: `017_organizational_operations` (Alembic Head)

---

## 1. Domain Overview

Completion Sprint A establishes native FastAPI models, PostgreSQL schemas, RBAC permission boundaries, and React UI components for the 6 remaining organizational operational domains:
1. **Human Resources (HR)**: `employees`, `employee_certifications`
2. **Housing**: `housing_units`, `housing_occupancies`
3. **Facilities & Maintenance**: `facilities`, `facility_work_orders`, `facility_inspections`
4. **IT Asset Management**: `it_assets`, `asset_assignments`
5. **Donations & Fundraising**: `donors`, `donations` (Decimal precision), `fundraising_campaigns`
6. **Volunteer Coordination**: `volunteers`, `volunteer_applications`, `volunteer_assignments`, `volunteer_hours`

---

## 2. RBAC Permission Isolation Matrix

| Domain | Permission String | Description |
| :--- | :--- | :--- |
| **HR** | `hr.employee.read`, `hr.employee.create`, `hr.certification.manage` | Strict separation from Child Welfare cases |
| **Housing** | `housing.unit.read`, `housing.unit.manage`, `housing.occupancy.manage` | Minimal Person identity disclosure for unit management |
| **Facilities** | `facilities.facility.read`, `facilities.facility.manage`, `facilities.workorder.manage` | Separate from Fleet Vehicle Maintenance |
| **IT Assets** | `asset.item.read`, `asset.item.manage`, `asset.assignment.manage` | Hardware asset lifecycle separate from `MobileDevice` security |
| **Donations** | `donation.donor.read`, `donation.donor.manage`, `donation.record.manage` | Donor contact privacy protected from generic access |
| **Volunteers** | `volunteer.record.read`, `volunteer.record.manage`, `volunteer.hours.manage` | Application screening reuse via `background_checks` |

---

## 3. Database Schema Mapping (`017_organizational_operations`)

All 15 tables use UUID primary keys, default `gen_random_uuid()`, indexed foreign keys, and soft delete where applicable (`archived_at`).
- `donations.amount`: `NUMERIC(12, 2)` decimal precision.
- `volunteer_hours.hours`: `NUMERIC(5, 2)` decimal precision.
- `employees.user_id`: Nullable foreign key to `users.id` allowing employees without login accounts.
