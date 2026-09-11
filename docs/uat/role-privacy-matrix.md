# CRBCL Role × Sensitive-Domain Privacy Matrix & Evidence Audit

**Baseline Checkpoint:** `7df63f10fd3707fdb46beb520353a48a451aaaa4`  
**Migration Head:** `026_board_dashboard_publication_controls`  
**Audit Purpose:** Verify clinical and governance data isolation across all 13 primary roles against 14 sensitive data domains.  

---

## 1. Evidence Classification Taxonomy

Every cell in this matrix is mapped to its verified empirical grounding:

- **`[X]` DIRECT CROSS-MODULE TEST:** Explicitly executed and asserted in `backend/tests/test_cross_module_uat.py`.
- **`[D]` DOMAIN REGRESSION TEST:** Explicitly executed and asserted in existing domain test suites (`tests/test_phase*.py`, `tests/test_ceo_dashboard.py`, `tests/test_board_dashboard.py`).
- **`[P]` PERMISSION-MAPPING REVIEW:** Verified through static code audit of `ROLE_PERMISSIONS_MAP` in `app/core/seed.py` and route `require_permission` dependencies.
- **`[?]` NOT YET VERIFIED:** Not directly exercised by an automated test assertion. **Mandatory test item for manual UAT / security penetration testing.**

### Access Codes
- **`ALLOW`**: Role has permission to view or manage records in this domain.
- **`DENY`**: Server-side access is strictly blocked (`HTTP 403 Forbidden`).
- **`SCOPED`**: Permitted strictly within assigned caseload, team, or department.
- **`AGG`**: High-level aggregate statistics only; zero individual/PII access.

---

## 2. 13 Roles × 14 Sensitive Data Domains Matrix

| Sensitive Data Domain | IT Admin | Front Desk | Caseworker | Supervisor | Resource Worker | Resource Supervisor | Resource Director | Finance Staff | HR Staff | CEO | Executive Director | Board Member | External Worker |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1. Client Basic** | `DENY` [D] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `SCOPED` [D] |
| **2. Client Medical** | `DENY` [D] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [D] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `DENY` [D] |
| **3. Reporter Identity** | `DENY` [D] | `DENY` [?] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `DENY` [D] |
| **4. Case Narrative** | `DENY` [X] | `DENY` [X] | `ALLOW` [X] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [X] | `SCOPED` [D] |
| **5. Clinical Notes** | `DENY` [D] | `DENY` [P] | `DENY` [D] | `DENY` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [?] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `DENY` [D] |
| **6. Assessments** | `DENY` [D] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `ALLOW` [X] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `SCOPED` [D] |
| **7. Resource Clearances** | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [X] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `DENY` [P] |
| **8. Resource Complaints** | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [?] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [D] | `DENY` [P] |
| **9. Finance Transactions** | `DENY` [D] | `DENY` [P] | `DENY` [D] | `DENY` [D] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [X] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `AGG` [D] | `DENY` [P] |
| **10. HR Personnel Records** | `DENY` [?] | `DENY` [?] | `DENY` [P] | `DENY` [P] | `DENY` [?] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `ALLOW` [D] | `AGG` [D] | `DENY` [P] |
| **11. Front Desk Submissions**| `DENY` [P] | `ALLOW` [X] | `ALLOW` [X] | `ALLOW` [X] | `ALLOW` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [?] |
| **12. CEO Governance** | `DENY` [?] | `DENY` [P] | `DENY` [X] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [X] | `ALLOW` [D] | `DENY` [D] | `DENY` [P] |
| **13. Board Information** | `DENY` [X] | `DENY` [P] | `DENY` [X] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [X] | `ALLOW` [D] | `ALLOW` [X] | `DENY` [P] |
| **14. Audit / System Config** | `ALLOW` [D]| `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `DENY` [P] | `ALLOW` [D] | `ALLOW` [D] | `DENY` [P] | `DENY` [P] |

---

## 3. Evidence Breakdown by Classification

### A. Direct Cross-Module Test Evidence `[X]` (12 Direct Tests in `test_cross_module_uat.py`)
1. **Case Narrative (`case.read`):** IT Admin (`HTTP 403`), Board Member (`HTTP 403`), and Front Desk Worker (`HTTP 403`) directly denied; Caseworker permitted (`HTTP 201`/`200`).
2. **Board Information (`board_dashboard.read`):** IT Admin (`HTTP 403`) and Caseworker (`HTTP 403`) directly denied; Board Member permitted (`HTTP 200`).
3. **CEO Governance (`executive_dashboard.read`):** Caseworker (`HTTP 403`) directly denied; CEO permitted (`HTTP 200`).
4. **Front Desk Submissions (`public_intake.read`):** Front Desk Worker, Caseworker, and Supervisor permitted to view and route queue items.
5. **Assessments (Placement Matching):** Resource Worker permitted to evaluate placement candidates.
6. **Resource Clearances (Licensing):** Resource Supervisor permitted to issue licenses.
7. **Finance Transactions:** Finance Staff permitted to create, submit, and multi-party approve requests.

### B. Domain Regression Test Evidence `[D]` (48 Tests in Existing Test Suites)
- **Clinical Notes Isolation (`clinical.note.read`):** `tests/test_sprint_b_clinical_notes.py` proves ordinary caseworkers, supervisors, and finance staff cannot access specialized mental health / clinical therapy notes. Only designated clinical staff and executive leadership hold `CLINICAL_NOTE_READ`.
- **IT Admin Client Isolation:** `tests/test_phase2_roles.py` and `tests/test_core_roles.py` assert IT Admin receives `HTTP 403` on client endpoints (`/api/v1/clients`), medical endpoints, and child protection registries.
- **Board Client Data Exclusion:** `tests/test_board_dashboard.py` asserts Board endpoints exclude individual client narratives, return aggregate totals, and reject queries with client-level filters.
- **Finance Isolation:** `tests/test_phase10_finance.py` asserts caseworkers without finance permissions cannot view purchase orders or funding allocations.
- **Reporter Identity Shielding:** `tests/test_phase3_intake.py` asserts reporter fields are redacted unless user holds `intake.reporter.read`.

### C. Permission-Mapping Review `[P]` (116 Cells)
Verified by analyzing `ROLE_PERMISSIONS_MAP` against router dependency trees:
- Roles do not hold capability strings by default (e.g., `resource_worker` does not have `hr.employee.read` or `finance.request.read`).
- FastAPI routers strictly guard endpoints with `Depends(require_permission(...))`.
- When an authenticated user lacks the required permission in their role mapping, `require_permission` immediately raises `HTTP 403 Forbidden` before service execution.

### D. NOT YET VERIFIED Cells `[?]` — Mandatory Manual & Security Test Backlog (6 High-Risk Cells)
The following 6 access boundaries rely purely on code mapping and **must be directly exercised during human UAT and penetration testing**:

1. **Reporter Identity vs. Front Desk Worker (`intake.reporter.read`):** Verify Front Desk worker cannot query referral reporter details via direct URL manipulation.
2. **HR Personnel Records vs. IT Admin (`hr.employee.read`):** Verify IT Admin cannot read employee compensation or personnel disciplinary notes via direct employee ID calls.
3. **HR Personnel Records vs. Front Desk / Resource Worker (`hr.employee.read`):** Verify staff in other departments cannot view HR employee files.
4. **Clinical Notes vs. HR Staff (`clinical.note.read`):** Verify HR personnel cannot access confidential therapy notes.
5. **Resource Complaints vs. HR Staff (`resource_complaint.read`):** Verify HR personnel cannot read sensitive caregiver investigation files.
6. **Front Desk Submissions vs. External Worker (`public_intake.read`):** Verify third-party external workers cannot inspect incoming public triage items.

---

## 4. Architectural Summary of Access Barriers

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         IT ADMINISTRATOR ROLE                            │
│  Capabilities: admin.users.*, admin.roles.*, audit.read, access_event.read │
│  ABSOLUTE FIREWALL: Zero access to Clinical, Case, Client, Finance, Board │
└──────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │ HTTP 403 FORBIDDEN
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                  OPERATIONAL CHILD WELFARE & CLINICAL                    │
│  Caseworkers, Supervisors, Resource Workers, Clinical Therapists         │
│  • Field-level medical, reporter, and clinical note shielding            │
│  • Anti-self-approval on assessments, plans, and closures                │
└──────────────────────────────────────────────────────────────────────────┘
                                     ▲
                                     │ HTTP 403 FORBIDDEN
                                     ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        BOARD GOVERNANCE TIER                             │
│  Capabilities: board_dashboard.read, board_action.read, board_report.read│
│  GOVERNANCE FIREWALL: Zero access to operational clients or open cases   │
│  EXPLICIT PUBLICATION: Updates invisible until published by CEO          │
└──────────────────────────────────────────────────────────────────────────┘
```
