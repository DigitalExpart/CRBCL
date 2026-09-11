# CRBCL CEO Dashboard — April 2026 CEO Report UAT Requirements Mapping

## Executive Purpose

This document provides a comprehensive mapping of the CRBCL April 2026 CEO Report into the CRBCL Executive Command Centre architecture.

> [!IMPORTANT]
> **Anti-Silo Architecture Principle**:
> The CEO Dashboard does **not** duplicate data-entry or create another silo.
> Real-time workforce metrics derive directly from the native `Employee` module; case numbers from `Case` and `PlacementEpisode`; Resource capacity from the Resource Unit; finance from `BudgetLine` and `FundingGrant`.
> New persistence is strictly reserved for governance items without an existing operational source:
> 1. Strategic Organizational Initiatives (`ExecutiveInitiative` & append-only `ExecutiveInitiativeHistory`)
> 2. Board Attention & Decision Requests (`BoardAction` & append-only `BoardActionHistory`)
> 3. Periodic Department Executive Updates (`DepartmentExecutiveUpdate` & append-only `DepartmentExecutiveUpdateHistory`)

---

## 1. Governance & Executive Leadership

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Extension Agreement Negotiation** | Managed through Executive Initiative | `ExecutiveInitiative` record linked to Governance department; status `ON_TRACK`/`AT_RISK`; milestone tracking. | Multi-year agreement with Crown/Indigenous partners. |
| **C-92 Successor Agreement** | Managed through Executive Initiative | `ExecutiveInitiative` record with target dates and owner. | High-priority strategic milestone. |
| **CRBCL Act Amendments** | Managed through Executive Initiative | `ExecutiveInitiative` record with target delivery dates. | Legal and governance deliverable. |
| **Board Decisions & Approvals** | Managed through Board Action | Structured `BoardAction` records with reference numbers (e.g., `BA-2026-0001`), required-by dates, and immutable decision log. | Never exposes private client narratives. Governance-level summary only. |
| **Board Onboarding & Policy Reviews** | Managed through Board Action / Executive Initiative | Strategic initiatives for curriculum; Board action for formal onboarding approval. | Prepares future Board Dashboard boundary without premature exposure. |

---

## 2. Policy & Data

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Policy Development & Manuals** | Managed through Executive Initiative | Tracked via `ExecutiveInitiative` (e.g. HR Manual, Customary Care Standards). | Preserves audit trail of versions and approvals. |
| **Data Governance & OCAP Principles** | Automatically derivable now | Data access event logging via `AuditEvent` and `AccessEvent` models. | High-level compliance exceptions flagged on CEO dashboard. |
| **Periodic Department Progress Narrative** | Managed through Department Executive Update | `DepartmentExecutiveUpdate` record for reporting period (e.g., `2026-04`). | Narrative accomplishments, risks, and requests preserved across historical periods. |

---

## 3. Human Resources

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Total Active Staff** | Automatically derivable now | `Employee` where `employment_status == 'ACTIVE'` and `is_deleted == False`. | Authoritative live count across all departments. |
| **Permanent vs. Term Staff** | Not currently measurable / policy needed | Flagged as `is_available: false` with explicit explanation: *"HR contract type (permanent vs term) is not tracked in current Employee schema."* | **No guessing or artificial values.** Awaiting HR contract classification policy. |
| **Staff on Leave** | Automatically derivable now | `Employee` where `employment_status == 'ON_LEAVE'`. | Live leave tracking. |
| **New Hires in Period** | Automatically derivable now | `Employee` where `hire_date >= period_start`. | Computed for active reporting month. |
| **Resignations vs. Dismissals** | Not currently measurable / policy needed | Flagged as `is_available: false` with explicit explanation: *"Employee exit reason (resignation vs termination) is not tracked in current Employee schema."* | Total departures are measured reliably (`employment_status == 'TERMINATED'`), but sub-classification requires HR exit taxonomy policy. |
| **Department Staff Distribution** | Automatically derivable now | Group by `Employee.department` for all active staff. | Sourced dynamically from native Employee records. |
| **Staff Certifications & Compliance Warnings** | Automatically derivable now | `EmployeeCertification` expiry alerts (expiring within 30 days or past due). | Surfaces in Executive Compliance & Risk section. |

---

## 4. Growing Up Well (Protection Services)

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Active Protection Cases** | Automatically derivable now | `Case` where `status in ('OPEN', 'ACTIVE')` and `is_deleted == False`. | Filtered for protection / CFS casework. |
| **Children in Care / Placement** | Automatically derivable now | `PlacementEpisode` where `status == 'ACTIVE'`, `end_date is NULL`, and `is_deleted == False`. Counts distinct `child_id` across active placements. | Defensible operational measure of distinct children currently placed in active care episodes. |
| **Families Served** | Automatically derivable now | Count of distinct `family_id` from open/active cases (`Case.status in ('OPEN', 'ACTIVE')`). | Authoritative open caseload measure. Misleading total `Family` table fallback removed. |
| **High-Risk Caseload Exceptions** | Automatically derivable now | High-level exception aggregate count; sensitive case narratives withheld. | CEO sees volume/severity and drill-down; no clinical text exposed on main dashboard. |
| **Monthly Clinical & Caseload Narrative** | Managed through Department Executive Update | Submitted via `DepartmentExecutiveUpdate` by Protection Director. | Covers complex casework themes without client name exposure. |

---

## 5. Post-Majority (Young Adults)

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Active Post-Majority Clients** | Automatically derivable now | `Case` with `case_type == 'POST_MAJORITY'` or linked to Post-Majority services. | Live count of young adults receiving transition support. |
| **Service & Support Volume** | Managed through Department Executive Update | Narrative summary of tuition, housing, and life skills supports. | Structured service records aggregated where recorded. |
| **Post-Majority Funding Agreements** | Managed through Executive Initiative | Strategic initiatives for federal/provincial transition agreements. | Target dates and funding milestones tracked. |

---

## 6. Enhancement & Preservation (Prevention Services)

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Prevention Cases & Families Supported** | Automatically derivable now | `Case` where `case_type == 'PREVENTION'` and `status in ('OPEN', 'ACTIVE')`. | Customary care and family preservation caseload. |
| **Active Prevention Programs** | Automatically derivable now | `Program` where `status == 'ACTIVE'` and category matches prevention/wellness. | Enrolled participant counts aggregated. |
| **Prevention Strategic Plan** | Managed through Executive Initiative | Tracked in `ExecutiveInitiative` with progress percentage. | Strategic organizational milestone. |

---

## 7. Resource Team

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Active Resource Homes** | Automatically derivable now | `PlacementHome` where `status == 'ACTIVE'` and `is_archived == False`. | Direct reuse of completed Resource Unit foundation. |
| **Available Bed Capacity** | Automatically derivable now | Sum of `total_capacity` minus children currently in active placement. | Live available bed computation. |
| **Recruitment Pipeline** | Automatically derivable now | `ResourceRecruitment` where `state not in ('APPROVED', 'WITHDRAWN', 'REJECTED')`. | Real-time intake & screening pipeline count. |
| **Expiring Home Licenses & Approvals** | Automatically derivable now | `PlacementHomeLicense` where `expiry_date <= today + 30 days`. | Exception alert in CEO Compliance & Risk. |

---

## 8. Early Learning / Daycare

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Daycare Facility Development** | Managed through Executive Initiative | Capital and licensing project tracked via `ExecutiveInitiative`. | Milestones for construction, licensing, and staffing. |
| **Daycare Operational Capacity** | Not currently measurable / policy needed | Flagged as `is_available: false` until Daycare management module is commissioned. | Narrative updates handled via `DepartmentExecutiveUpdate`. |

---

## 9. Culture & Traditional Healing

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Active Cultural Programs** | Automatically derivable now | `Program` where `category == 'Cultural Programs'` and `status == 'ACTIVE'`. | Cultural teachings, lodge events, language classes. |
| **Participation Volume** | Automatically derivable now | Sum of `enrolled_count` from active cultural programs. | Aggregated enrollment. |
| **Lodge Operations & Upgrades** | Managed through Executive Initiative | Sacred Wolf Lodge capital projects and facility initiatives. | Target completion dates and updates. |

---

## 10. Communications

| CEO Report Item / Requirement | Classification | Implementation Architecture | Notes & Policy Guardrails |
| :--- | :--- | :--- | :--- |
| **Annual Report & Branding Projects** | Managed through Executive Initiative | Tracked as deliverables in `ExecutiveInitiative`. | Deliverable status, owner, target dates. |
| **Website & Community Outreach** | Managed through Department Executive Update | Submitted in monthly narrative updates. | Periodic updates for executive visibility. |

---

## Summary of Architectural Commitments

1. **Zero Seed Pollution**: Historical April 2026 names and figures (such as 64 staff, 24 families, 81 children in care) are **never** seeded as synthetic production data.
2. **Defensible Unavailable Metrics**: When a metric cannot be measured from structured data with integrity (such as permanent vs. term staff or resignation vs. dismissal), the API returns `is_available: false` and `reason: str` rather than defaulting to `0` or fabricating estimates.
3. **Financial Precision**: All monetary allocations, expenditures, and remaining funds are computed exclusively using Python `Decimal`.
4. **Append-Only Governance Auditing**: All changes to `ExecutiveInitiative` status or progress and all `BoardAction` decisions generate unmodifiable history records (`ExecutiveInitiativeHistory` and `BoardActionHistory`).
5. **Strict RBAC & Privacy**: Only users with `executive_dashboard.read` can access the CEO Command Centre. IT Administrators possess zero access to executive summaries or client indicators.
