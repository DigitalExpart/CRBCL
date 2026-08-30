# ADR-007: Intake Referral State Machine & Workflow Transition Architecture

## Status
Approved

## Context
In the CRBCL Family Wellness Case Management Platform, a Referral represents the initial "front door" contact before a formal case is opened. In legacy child-welfare software, intake statuses were frequently modified arbitrarily via generic PATCH/UPDATE operations or lacked atomic supervisor approval workflows, leading to lost history, premature case opening, and unauthorized status tampering.

## Decision
1. **Explicit State Machine**:
   A referral must strictly transition through dedicated lifecycle states:
   - `DRAFT`: Intake worker is recording details; not yet received or formally submitted.
   - `RECEIVED`: Referral has been received and logged.
   - `IN_PROGRESS`: Information gathering, involved person identification, incident recording, and child dispositions are actively underway.
   - `PENDING_SUPERVISOR`: Intake worker has completed the assessment and formally submitted the referral for supervisor review.
   - `APPROVED`: Supervisor has reviewed and approved the referral and child dispositions.
   - `RETURNED`: Supervisor has reviewed and returned the referral to the intake worker with required revision comments.
   - `SCREENED_OUT`: Child/family does not meet protection/prevention criteria; no active case opened.
   - `REFERRED_EXTERNALLY`: Routed to an external First Nation, community agency, or jurisdiction.
   - `CANCELLED`: Voided/duplicate record.

2. **Command Endpoint Enforcement**:
   - Status cannot be changed via generic `PATCH /api/v1/referrals/{id}`.
   - Transitions must be invoked through dedicated command endpoints:
     - `POST /api/v1/referrals/{id}/submit`
     - `POST /api/v1/referrals/{id}/approve`
     - `POST /api/v1/referrals/{id}/return`
   - Every transition verifies prerequisites (e.g. at least one involved child, primary concern recorded, child dispositions defined).

3. **Workflow History & Audit**:
   - Each transition writes an entry to `workflow_actions` and an immutable record to `audit_events`.
   - On supervisor return, the return comments and previous submission history are permanently retained.

## Consequences
- Guarantees complete auditability and prevents unauthorized or accidental status bypasses.
- Ensures all intake approvals follow standardized two-person verification (worker + supervisor).
