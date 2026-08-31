# ADR-009: Explicit Case Lifecycle State Machine and Closure Audit

## Status
Accepted

## Context
In the CRBCL Family Wellness Case Management Platform, cases represent active child safety investigations, family wellness prevention plans, or post-majority support files. Historically, cases were simple records where the status column could be updated arbitrarily via generic PATCH operations. 

For Indigenous child welfare and provincial compliance:
1. Case lifecycle transitions (e.g. from `OPEN` to `ACTIVE`, `ON_HOLD`, `CLOSING`, `CLOSED`, and `REOPENED`) carry significant legal, practice, and safety consequences.
2. Case closures require explicit reasons, resolution dates, supervisor sign-offs, and must prevent premature or unvalidated termination.
3. Case reopenings must preserve historical closure data (closed date, previous closure rationale) without overwriting past history.

## Decision
1. Implement a formal state machine for case statuses:
   - `OPEN`: Initial intake-routed or manually created investigation file.
   - `ACTIVE`: Ongoing active casework, investigation, or prevention service delivery.
   - `ON_HOLD`: Temporarily suspended (e.g. awaiting external jurisdiction or court determination).
   - `CLOSING`: Pending final supervisor closure review.
   - `CLOSED`: Formally closed with recorded resolution reason and closure date.
   - `REOPENED`: Formally reopened after previous closure, maintaining the full prior timeline.
2. Disallow arbitrary status modification through generic `PATCH /api/v1/cases/{id}`.
3. Provide dedicated command endpoints:
   - `POST /api/v1/cases/{id}/close`: Validates closure reason, sets `closed_date`, updates status to `CLOSED`, logs to `case_status_history`, `audit_events`, and `timeline_events`.
   - `POST /api/v1/cases/{id}/reopen`: Validates reopen reason, sets `reopened_at` and `reopened_by`, updates status to `REOPENED`, and records history.
4. Persist all transitions in a dedicated `case_status_history` table capturing `case_id`, `previous_status`, `new_status`, `reason`, `changed_by`, and `changed_at`.

## Consequences
- Prevents accidental or unauthorized case closures.
- Ensures total auditability for judicial inquiries, quality assurance, and community reporting.
- Enhances data integrity across cross-departmental teams.
