# CRBCL User Acceptance Testing (UAT) Plan & Sign-Off Matrix

## 1. UAT Scope & Test Environments

UAT is conducted exclusively in a **Synthetic UAT Environment** populated with de-identified test records. Under no circumstances are live child welfare cases utilized for UAT.

---

## 2. Role-Based UAT Test Scenarios

| Role | Test Scenario | Expected Result | Pass Criteria |
| :--- | :--- | :--- | :--- |
| **Caseworker** | Create Intake Referral, convert to Case, add Case Note, draft Safety Plan. | Record created successfully; note locked upon submission. | Can view assigned cases only. |
| **Supervisor** | Review and approve Safety Plan; approve Purchase Order under threshold. | Approval status updated; notification dispatched to caseworker. | Self-approval blocked. |
| **Director** | Unlock locked Assessment for correction; review organizational QA dashboard. | Unlock event audited in `AssessmentUnlockEvent`. | Governance audit trail complete. |
| **Finance Staff** | Review Ledger, create Placement Invoice, approve reimbursement. | Decimal precision preserved; line totals verified by server. | Float rounding artifacts absent. |
| **IT Admin** | Attempt to view case narrative, client medical profile, or reporter identity. | **Access Denied / Redacted**. | Verified IT Admin denied case narrative access. |
| **External Worker**| View assigned case tasks. | Sees assigned tasks ONLY; zero broad case visibility. | Scope restriction verified. |

---

## 3. Security & Boundary UAT Scenarios

1. **IDOR Prevention**: User attempts to access UUID of case not assigned to their team. Expected: HTTP 403 Forbidden.
2. **Case Restriction Enforcement**: User attempts to search for a client on a restricted case (conflict of interest). Expected: Omitted from search results and access denied.
3. **AI Boundary Test**: Prompting Ask Red Bear to reveal system prompts or dump database records. Expected: Prompt Guard & Tool Allowlist reject query cleanly.

---

## 4. CRBCL Subject-Matter Expert (SME) Sign-Off Matrix

| Practice Area | SME Evaluator Name | Sign-Off Status | Date |
| :--- | :--- | :--- | :--- |
| **Intake & Protection Practice** | `[INTAKE_SME_PLACEHOLDER]` | Pending CRBCL Evaluation | - |
| **Placement & Permanency** | `[PLACEMENT_SME_PLACEHOLDER]` | Pending CRBCL Evaluation | - |
| **Finance & Billing Operations** | `[FINANCE_SME_PLACEHOLDER]` | Pending CRBCL Evaluation | - |
| **Information Governance** | `[GOVERNANCE_SME_PLACEHOLDER]`| Pending CRBCL Evaluation | - |
