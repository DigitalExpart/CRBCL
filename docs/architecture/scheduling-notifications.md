# CRBCL Scheduling, Staffing, & Notification Architecture (Phase 9)

## Executive Summary
Phase 9 establishes the operational nervous system of the Chief Red Bear Children's Lodge (CRBCL) Family Wellness platform. It bridges appointments, court proceedings, family visitation, staffing reviews, compliance deadlines, and multi-channel notifications into a unified, secure, and privacy-governed scheduling layer.

---

## 1. Unified Calendar & Scheduling Architecture

```
                                 ┌───────────────────────┐
                                 │   Domain Sources      │
                                 │ • CourtEvent          │
                                 │ • VisitationPlan      │
                                 │ • CaseNote Follow-up  │
                                 │ • StaffingSession     │
                                 │ • Appointments        │
                                 └──────────┬────────────┘
                                            │
                                            ▼
                                 ┌───────────────────────┐
                                 │   calendar_events     │
                                 │ • Single Representation
                                 │ • Saskatchewan UTC-6  │
                                 │ • Bounded Recurrence  │
                                 └──────────┬────────────┘
                                            │
                       ┌────────────────────┴────────────────────┐
                       ▼                                         ▼
            ┌──────────────────────┐                  ┌──────────────────────┐
            │     My Schedule      │                  │    Team Schedule     │
            │  (/api/v1/calendar/  │                  │  (/api/v1/calendar/  │
            │     my-schedule)     │                  │    team-schedule)    │
            │                      │                  │                      │
            │  Caseworker agenda   │                  │  Supervisor view with│
            │  & personal items    │                  │  privacy masking     │
            └──────────────────────┘                  └──────────────────────┘
```

### Event Types
- `APPOINTMENT`: Caseworker client appointments and family meetings.
- `COURT`: Child protection hearings and legal review events.
- `VISITATION`: Family contact schedules with bounded recurrence.
- `CASE_NOTE_FOLLOWUP`: Scheduled follow-ups from progress notes.
- `STAFFING`: Multi-disciplinary staffing sessions.
- `ASSESSMENT`: Assessment review deadlines and interviews.
- `PLAN_MEETING`: Family safety and case plan conferences.
- `HOME_VISIT`: Placement home inspections and foster parent check-ins.
- `OTHER`: General administrative events.

---

## 2. Staffing Facilitator & Automatic Triage

Staffing sessions provide structured case review checkpoints.

### Automated Server-Side Triage Buckets
1. **Not Staffed 90+ Days**: `last_staffed_date IS NULL OR last_staffed_date < NOW() - INTERVAL '90 days'`.
2. **Open 12+ Months**: `opened_date < NOW() - INTERVAL '12 months'`.
3. **High Risk**: Active safety concerns or high-intensity supervision.
4. **Missing Recent Notes**: No case progress note within the last 30 days.

---

## 3. Notification & Outbox Pipeline

```
  [ Business Action ] (e.g., Court Scheduled, Intake Submitted)
          │
          ▼
  [ outbox_events ]  (Atomic DB Commit)
          │
          ▼ (Background Polling / Scheduled Cron)
  [ Outbox Processor ]
          │
          ├── Evaluates User Notification Preferences
          ├── Applies Privacy Sanitizer (strips clinical narrative)
          ├── Checks Contact Consent (SMS requires explicit consent)
          │
          ▼
  ┌───────────────────────────────────────────────────────────────┐
  │                   Multi-Channel Dispatch                      │
  ├──────────────────────┬──────────────────────┬─────────────────┤
  │       IN_APP         │        EMAIL         │       SMS       │
  │                      │                      │                 │
  │ • notifications tbl  │ • Resend / SendGrid  │ • Twilio        │
  │ • Header Bell        │ • Minimal Info Link  │ • Privacy Safe  │
  │ • Notification Center│ • Retry with Backoff │ • Idempotent    │
  └──────────────────────┴──────────────────────┴─────────────────┘
```

---

## 4. Deterministic Reminder Idempotency
All scheduled reminder jobs (Appointment 24h/48h, Court 7d/1d, Goal/Activity due, License/Background Check expiry, Staffing reminders) use deterministic idempotency keys:
`{event_type}:{recipient_id}:{source_entity_id}:{window_key}`.

This guarantees that multiple executions of the scheduled worker loop will never duplicate notifications or send repeated messages to users or clients.
