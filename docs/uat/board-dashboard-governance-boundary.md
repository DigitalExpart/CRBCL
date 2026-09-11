# CRBCL Board Dashboard — Governance Information Boundary & UAT Specification

## Executive Purpose

The **CRBCL Board of Governors Dashboard** provides a strictly governed, strategic oversight interface for members of the Board of Governors.

> [!IMPORTANT]
> **Fundamental Governance Principle**:
> The `board_member` role is **strictly a governance role**, not an operational, casework, or superuser role.
> In Indigenous child-welfare software handling highly sensitive customary care, child protection, family preservation, and clinical records, Board members must **never** receive operational casework access merely because they have organizational oversight responsibilities.

---

## 1. Information Boundary: CEO Dashboard vs. Board Dashboard

| Dimension | CEO Command Centre (`/ceo`) | Board Governance Dashboard (`/board`) | Governance Boundary Rationale |
| :--- | :--- | :--- | :--- |
| **Primary Audience** | Chief Executive Officer, Executive Director | Board of Governors | Strategic governance oversight vs. daily executive operations. |
| **Caseload Visibility** | Operational aggregates with high-risk caseload exception flags and department breakdowns. | Redacted service volume aggregates only (active files count, distinct children in active care). | **Zero client/child identifiers, clinical narratives, or case numbers.** |
| **Strategic Initiatives** | All internal initiatives, drafts, operational notes, and detailed tracking. | **Only Board-Published initiatives** (`is_board_visible == True`) with governance-safe summaries. | Protects sensitive preliminary operational negotiations and internal working notes. |
| **Department Updates** | Full monthly departmental submissions including raw operational narratives. | **Only Board-Published updates** (`is_board_visible == True`) approved by executive leadership. | Internal personnel, preliminary operational hurdles, and confidential casework narratives are withheld. |
| **Board Actions** | All submitted, draft, under-review, and resolved action requests across departments. | **Governance-ready Board Actions only** (`is_governance_ready == True` and status != "DRAFT"). | Board only considers formalized governance items ready for motion or decision. |
| **Workforce Data** | Detailed departmental headcount, recent hires, leave tracking, certification expiry warnings. | Aggregate active headcount and department distribution only. | **Zero employee personal info, compensation, disciplinary records, or medical/leave details.** |
| **Financial Data** | Approved budget, expenditures, service request commitments, active grants, program cost centres. | High-level approved budget allocations, expenditures, and remaining funds (`Decimal`). | **Zero client reimbursement, caregiver payment, vendor banking, or individual invoices.** |
| **Risk & Compliance** | Granular risk register: QA audit scores, home license alerts, major incidents by status. | High-level aggregate compliance counts and serious incident volume by severity. | **Zero incident narrative text, reporter identities, or victim/child identities.** |
| **Critical Dates** | Operational and governance deadlines (initiatives, licenses, QA ticklers, board actions). | High-level governance milestones and Board decision deadlines. | **Zero client court dates, family visits, or clinical appointments.** |

---

## 2. Board-Safe Data vs. Explicitly Prohibited Data

### A. Board-Safe Fields
The `/api/v1/board/*` API endpoints return only:
1. **Strategic Initiatives**: Title, originating department, status (`ON_TRACK`, `AT_RISK`, `DELAYED`, `COMPLETED`), priority, target date, progress percentage, `board_summary`, latest governance update.
2. **Board Actions**: Reference sequence (`BA-YYYY-NNNN`), originating department, title, background summary, requested Board action, required-by date, priority, status, decision/resolution notes, decision date, decided-by name, append-only decision audit history.
3. **Department Updates**: Originating department, reporting period (e.g. `2026-04`), headline summary, approved accomplishments narrative, strategic risks/issues, support/decision requested.
4. **Workforce Aggregates**: Total active staff count, staff on leave count, recent hires count, department staff distribution count.
5. **Financial Aggregates**: Total approved allocated budget, total expenditure, remaining budget, active funding grants count, pending purchase order count/total (strictly `Decimal`).
6. **Service Outcome Aggregates**: Active files count, distinct families served count, distinct children in active care placements count, active resource homes count, available bed capacity, caregiver recruitment pipeline count, cultural programs and enrollment counts.
7. **Risk & Compliance Aggregates**: Delayed initiatives count, expiring resource home licenses in 30 days count, serious incident count grouped by severity (`SEV-1`, `SEV-2`).
8. **Critical Governance Dates**: Board Action required-by dates, strategic initiative milestone target dates.

### B. Explicitly Prohibited Data
The following data domains are **fail-closed** and completely inaccessible to Board members (`403 Forbidden`):
- **Client & Family Records**: `client.read`, `client.identifiers.read`, `client.medical.read`, `family.read`, `/clients`, `/families`.
- **Casework & Files**: `case.read`, case notes, case plans, safety plans, `/cases`, `/plans`.
- **Intake & Referrals**: `intake.read`, `intake.reporter.read` (confidential reporter identity), `/intake`.
- **Clinical & Medical**: `clinical.note.read`, practitioner treatment notes, diagnoses, wellness plans, `/clinical-notes`.
- **Caregiver & Clearance Details**: `placement_home.background_check.read`, `resource_clearance.adjudicate`, caregiver criminal background records.
- **Sensitive Complaints**: `resource_complaint.sensitive.read`, caregiver investigation files.
- **Staff Personnel Files**: `hr.employee.read`, salaries, compensation, disciplinary records, medical leave reasons, `/employees`.
- **Transaction-Level Finance**: `finance.request.read`, `finance.invoice.read`, `finance.ledger.read`, individual vendor banking info, client service disbursements.
- **System Administration**: `admin.users.manage`, `admin.roles.manage`, `/admin`.
- **Full CEO Dashboard**: `executive_dashboard.read`, `/ceo`.

---

## 3. Executive Publication & Approval Workflow

Internal operational records do **not** automatically appear on the Board Dashboard. They must go through deliberate executive review:

```
[Department Lead / Staff]
          │
          ▼
   Submits Update or
  Strategic Initiative
          │
          ▼
[Executive Leadership / CEO]
          │
          ├── Reviews operational content
          ├── Drafts governance-safe 'board_summary'
          ├── Sets 'is_board_visible = True'
          │
          ▼
[Board Dashboard]
  Visible to Board of Governors
```

### Publication Controls (Migration 026):
1. **`ExecutiveInitiative`**:
   - `is_board_visible`: Boolean flag (default `False`).
   - `board_summary`: Dedicated governance narrative written specifically for Board presentation.
   - `approved_for_board_at`: Timestamp of executive approval.
   - `approved_for_board_by_id`: User ID of approving executive.
2. **`DepartmentExecutiveUpdate`**:
   - `is_board_visible`: Boolean flag (default `False`).
   - `approved_for_board_at`: Timestamp of executive approval.
   - `approved_for_board_by_id`: User ID of approving executive.
3. **Audit Trail**: Every publication or unpublication action generates a tamper-evident `AuditEvent` recording actor, timestamp, and payload.

---

## 4. Role & Permissions Architecture

### A. Role Definition
- **Key**: `board_member`
- **Name**: `Board Member`
- **Description**: `Board of Governors member with governance oversight and board action review. NO operational child welfare, clinical, finance detail, or staff HR access.`
- **System Role**: Yes (`is_system = True`). Not self-assignable via public registration.

### B. Capabilities Assigned to `board_member`
- `board_dashboard.read`: View `/board` overview, performance aggregates, workforce, finances, and critical dates.
- `board_action.read`: View governance-ready Board Actions and historical decisions.
- `board_document.read`: View approved governance documents and policy attachments.
- `board_report.read`: View approved department executive reports and annual summaries.

### C. Capabilities Restricted to Executive Officers
- `board_publication.manage`: Publish or unpublish initiatives and department updates to the Board (assigned to `ceo` and `executive_director`).
- `board_decision.record`: Record formal Board motions, approvals, or declines (assigned to `ceo` and `executive_director` by default).

### D. IT Admin Separation
- `it_admin` manages user accounts, roles, and technical infrastructure.
- `it_admin` has **zero** Board dashboard permissions (`board_dashboard.read` is denied with `403 Forbidden`).

---

## 5. April 2026 CEO Report → Board Dashboard Mapping

| April 2026 CEO Report Domain | Board Dashboard Representation | Publication & Privacy Rule |
| :--- | :--- | :--- |
| **Governance & Leadership** | Board Actions table; Strategic Initiatives (e.g. C-92 Successor Agreement, Extension Agreement Negotiation). | Governance summaries only; individual partner negotiation details withheld. |
| **Policy & Data** | Policy development initiatives; high-level compliance indicators. | Raw audit events not exposed. |
| **Human Resources** | Aggregate workforce count; staff by department distribution; transparent unavailable metrics. | Zero employee names, salaries, medical details, or disciplinary notes. |
| **Growing Up Well** | Distinct children with active placements; open cases count; families served count. | Zero child names, family names, case IDs, or clinical narratives. |
| **Post-Majority** | Post-majority active cases count; strategic youth transition initiatives. | Client identity protected. |
| **Enhancement & Preservation** | Prevention cases count; active prevention programs count and enrollment. | Individual family support details excluded. |
| **Resource Team** | Approved resource homes count; available beds capacity; recruitment pipeline count. | Caregiver identities and home addresses excluded. |
| **Early Learning / Daycare** | Daycare facility construction initiative; operational capacity declared unavailable. | Capital project progress tracked without confidential contractor bids. |
| **Culture & Traditional Healing** | Cultural programs count; total participant enrollment; lodge capital initiatives. | Elder and participant identities protected. |
| **Finance** | Approved budget allocation, expenditures, remaining funds, active funding grants count. | Zero individual invoices, client purchase orders, or vendor banking details. |

---

## 6. Unresolved Governance Policy Decisions

1. **Board Decision Self-Recording Authority**:
   - *Current Design*: Recording a formal decision on a `BoardAction` requires `board_decision.record`, which is restricted to executive leadership (`ceo`, `executive_director`).
   - *Policy Question*: Should the Board Secretary or Board Chair have direct self-recording rights in the software, or should decisions continue to be recorded by executive governance staff following formal meetings?
2. **Fiscal Year Definition**:
   - *Current Design*: The system supports arbitrary reporting periods (e.g. `2026-04`, `2026-Q1`) and relies on native `BudgetLine` allocations.
   - *Policy Question*: When CRBCL formalizes its fiscal year convention (e.g. April 1 – March 31 vs. January 1 – December 31), should budget variance reporting enforce automated quarterly reconciliation?
3. **Board Document Retention & Watermarking**:
   - *Policy Question*: When Board report export/download is commissioned, should confidential watermarks (e.g. *"CONFIDENTIAL — FOR BOARD OF GOVERNORS REVIEW ONLY — [User Name]"*) be dynamically embedded into PDF exports?
