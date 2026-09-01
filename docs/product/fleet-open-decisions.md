# CRBCL Fleet Management — Open Product & Policy Decisions

## Overview
This document tracks agency-level policy questions and operational configurations requiring formal decision from CRBCL leadership before final Phase 13 production lock.

| Policy ID | Decision Domain | Default Phase 12 Implementation | Decision Needed From CRBCL |
| :--- | :--- | :--- | :--- |
| **POL-FLEET-001** | **GPS History Retention Period** | 90 days online retention before archival. | Confirm if 90 days meets insurance and agency audit compliance requirements. |
| **POL-FLEET-002** | **Driver Licensing Verification** | System checks `employee.is_active` and driver authorization flag. | Define whether explicit driver's licence expiry date tracking and MVR (Motor Vehicle Record) checks should be required prior to checkout. |
| **POL-FLEET-003** | **Maintenance Interval Thresholds** | Configured per vehicle type (e.g. 5,000 km or 6 months for oil change). | Approve standardized agency maintenance intervals. |
| **POL-FLEET-004** | **Insurance Alert Schedule** | Notifications dispatched at 60, 30, and 7 days prior to expiry. | Confirm lead time preference for insurance renewal workflows. |
| **POL-FLEET-005** | **Overdue Trip Threshold** | Trips flagged overdue 30 minutes after expected return time. | Confirm grace period before dispatching overdue alerts to supervisors. |
| **POL-FLEET-006** | **Service Area & Geofence Boundaries** | Configurable circular radius around CRBCL facilities and Cowessess reserve area. | Provide exact GPS polygon boundaries for service areas and restricted zones. |
| **POL-FLEET-007** | **Telematics Vendor Selection** | Provider abstraction built with Samsara and Easy Fleet compatibility. | Select final vendor when hardware deployment is funded. |
