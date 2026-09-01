# ADR-023: Financial Approval Workflow, Segregation of Duties, and Audit History

## Status
Accepted (Phase 10)

## Context
Financial service requests (Purchase Orders and Reimbursement Requests) at CRBCL represent commitments and expenditures of Band and program funds. A strict segregation of duties must prevent unauthorized disbursements, self-approval by requesters, and untraceable modifications.

## Decision
1. **Unified Request Lifecycle**:
   - Financial requests follow a strict state machine:
     - `DRAFT` → Initial authoring of line items and supporting documents.
     - `SUBMITTED` / `PENDING_APPROVAL` → Immutable snapshot submitted for review.
     - `APPROVED` → Formally authorized by designated supervisor/manager.
     - `RETURNED` → Sent back to requestor with mandatory explanatory reason; requestor can amend and resubmit.
     - `DENIED` → Formally rejected with mandatory reason; preserved permanently in historical records.
     - `CANCELLED` → Voided by requestor prior to approval.
2. **Mandatory Segregation of Duties**:
   - The user who created or requested the purchase order or reimbursement **CANNOT** approve their own request under any circumstances.
   - Any approval attempt by the requestor is blocked at the backend with HTTP `403 Forbidden` (`"Requester cannot approve their own financial request"`).
3. **Immutable Multi-Step Approval History**:
   - Every status transition creates an immutable row in `service_request_approvals` capturing `step_number`, `approver_id`, `status`, `comments`, and `decided_at`.
   - Returning or editing a request never deletes or overwrites previous review comments or approval decisions.
4. **Outbox Event Integration**:
   - Transitions emit transactional events (`FINANCE_REQUEST_SUBMITTED`, `FINANCE_REQUEST_APPROVED`, `FINANCE_REQUEST_RETURNED`, `FINANCE_REQUEST_DENIED`) via the Phase 9 Outbox engine to notify supervisors and requestors.

## Consequences
- **Positive**: Strict internal controls, full audit traceability, compliance with funding agency standards, and complete transparency.
- **Negative**: Adds multi-step interaction for requesters and supervisors.
