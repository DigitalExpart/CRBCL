# ADR-021: Staffing Session Model & Facilitator Architecture

## Status
Accepted (Phase 9)

## Context
Child welfare staffing is a mandatory multi-disciplinary case review session where caseworkers, supervisors, cultural advisors, and specialists review case progression, risk mitigation, cultural connections, and permanency goals. 

Prior to Phase 9, staffings were recorded informally in narrative case notes or off-platform spreadsheets, leading to lost review cadences, unmonitored follow-up commitments, and lack of systematic compliance tracking for long-open or high-risk cases.

## Decision

### 1. Dedicated Staffing Domain Schema
- `staffing_sessions`: Top-level session record tracking date/time, facilitator, assigned team, cadence (`WEEKLY`, `BIWEEKLY`, `MONTHLY`, `AD_HOC`), status (`SCHEDULED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`), location, and general minutes.
- `staffing_attendees`: Tracks staff and partner attendance (`ATTENDED`, `ABSENT`, `EXCUSED`, `PENDING`) and individual contributions.
- `staffing_cases`: Associates cases reviewed during the session, capturing case-specific discussion summaries, review outcome (`PENDING`, `REVIEWED`, `DEFERRED`, `ESCALATED`), follow-up action flags, follow-up due dates, and assigned action owners.

### 2. Automatic Server-Side Staffing Buckets
To eliminate manual case searching and ensure high-priority cases receive supervisory review, the platform exposes server-side triage buckets:
1. **Not Staffed 90+ Days**: Active cases where the last completed staffing review is older than 90 days (or cases open > 90 days that have never been staffed).
2. **Open 12+ Months**: Active long-term cases open for 12 or more months.
3. **High Risk**: Active cases with safety alerts or high-intensity supervision.
4. **Missing Recent Notes**: Active cases with no progress notes recorded within the last 30 days.

### 3. Derived Last-Staffed Date
- Rather than relying on a fragile, manually edited timestamp on the `Case` record, the canonical **Last Staffed Date** is computed directly:
  `MAX(staffing_sessions.session_date) WHERE staffing_cases.case_id = :case_id AND staffing_cases.review_status = 'REVIEWED' AND staffing_sessions.status = 'COMPLETED'`.
- This ensures historical auditability and guarantees that marking a case reviewed in a completed staffing session automatically updates its compliance status.

### 4. Automatic Calendar Integration
- Creating a staffing session automatically materializes a `calendar_events` record of type `STAFFING` linked to the facilitator, team, and session attendees.

## Consequences
- **Positive**: Systematic, auditable case review cadences.
- **Positive**: Proactive triage buckets prevent high-risk cases from slipping through administrative cracks.
- **Positive**: Complete integration between staffing attendance, case reviews, and team calendars.
