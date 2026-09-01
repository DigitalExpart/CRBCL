# CRBCL Data Classification Framework

## 1. Classification Levels

Data within the CRBCL Family Wellness Case Management Platform is classified into four distinct levels based on sensitivity, legal obligations, and impact of unauthorized disclosure.

| Level | Classification | Description | Handling Rules |
| :--- | :--- | :--- | :--- |
| **L1** | **PUBLIC** | Information intended for public distribution (e.g. community event announcements, office hours). | May be published externally via Communications Hub. No encryption required. |
| **L2** | **INTERNAL** | System operational data (e.g. program lookup lists, vehicle lists, aggregated QA metrics). | Restricted to authenticated staff. Standard TLS in transit and AES-256 at rest. |
| **L3** | **CONFIDENTIAL** | Staff identity, financial ledgers, purchase orders, vehicle GPS coordinates. | Role-based access control (RBAC). Strict audit logging of access and modifications. |
| **L4** | **HIGHLY_SENSITIVE** | Client identity, health records, reporter identities, case notes, assessments, placement addresses, background checks, AI prompts. | **Maximum Protection**: Scope-based authorization, case restriction checks, PII redaction, encryption, log sanitization, and legal hold support. |

---

## 2. Domain Data Asset Inventory & Classification

| Data Asset | Classification | Primary Storage | Handling & Redaction Rules |
| :--- | :--- | :--- | :--- |
| **Client Name & DOB** | HIGHLY_SENSITIVE | `clients`, `persons` | Access requires `client.read`. Redacted in public/AI exports. |
| **Reporter Identity** | HIGHLY_SENSITIVE | `referrals` | **Strict Isolation**: Visible ONLY to Intake Workers (`intake.reporter.read`). Never exposed to IT Admin, AI, or general case views. |
| **Client Health Records** | HIGHLY_SENSITIVE | `client_medical_profiles` | Access requires `client.medical.read`. Stripped from AI prompt context. |
| **Case Notes & Narratives** | HIGHLY_SENSITIVE | `case_notes` | Immutable after creation. Case Restriction checks enforced before display. |
| **Assessments & Plans** | HIGHLY_SENSITIVE | `assessments`, `plans` | Versioned and locked upon completion. Re-opening requires Director unlock event. |
| **Placement Home Addresses** | HIGHLY_SENSITIVE | `placement_homes` | Restricted to Placement Workers and assigned Supervisors. Redacted on public maps. |
| **Background Check Details** | HIGHLY_SENSITIVE | `background_checks` | Visible only to HR/Placements Staff. |
| **Financial Ledger & Invoices** | CONFIDENTIAL | `financial_ledgers`, `invoices` | Requires `finance.read`. Self-approval of purchase orders prohibited. |
| **Vehicle GPS Coordinates** | CONFIDENTIAL | `vehicle_telematics_logs` | Speeding alerts logged; raw coordinates sanitized after 30 days. |
| **AI Queries & Audits** | HIGHLY_SENSITIVE | `ai_request_audits` | Prompts sanitized before external LLM transmission. Audit entry captures token cost and user ID. |
| **Audit Logs** | CONFIDENTIAL | `audit_events`, `access_events` | **Immutable**: No API or user can modify or delete audit rows. |

---

## 3. Data Storage & Residency Boundary

1. **Primary Database & Storage**: All L2, L3, and L4 data resides in Supabase PostgreSQL (`ca-central-1`, Montreal, Canada) with TLS 1.3 in transit and AES-256 at rest.
2. **Workstation Safety**: Workstations must never cache unencrypted L4 client records. Browser local storage stores JWT tokens only (or HttpOnly cookies in production).
