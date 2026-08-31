# ADR-011: Case Note Immutability, Locking, Addenda, and Correction Architecture

## Status
Accepted

## Context
Case notes in child welfare services document critical interactions, observations, well-child visits, disclosures, and risk assessments that may serve as evidence in court proceedings, coroner inquiries, or legislative oversight. 

Modifying historical case notes silently or overwriting locked records compromises legal integrity and breaches child protection standards.

## Decision
1. Implement a structured lifecycle for case notes:
   - `DRAFT`: Worker is actively preparing the narrative; editable only by the author.
   - `COMPLETED`: Note has been finalized by the worker; ready for locking.
   - `LOCKED`: Note is legally frozen (`is_locked = TRUE`, with `locked_at` and `locked_by`).
2. Once a note is in `LOCKED` status:
   - Any `PATCH` or `PUT` request attempting to alter `content`, `subject`, `contact_type`, `location`, or `duration_minutes` is **strictly rejected** by the backend with `HTTP 409 Conflict` or `HTTP 403 Forbidden`.
3. To accommodate necessary corrections, late-discovered facts, or supervisor amendments:
   - Introduce `case_note_addenda`: A relational table linking to the original `case_note_id`, preserving the exact original narrative while appending dated, author-attributed clarification notes.
   - If a formal supervisor unlock is executed, the previous state, rationale, supervisor identity, and timestamp are immutably logged to `audit_events` and `timeline_events`.
4. Provide a note cloning feature (`POST /api/v1/case-notes/{id}/clone`) that copies structured metadata (contact type, location, note type) into a fresh `DRAFT` note without copying timestamps, completion states, or locked flags.
5. Case notes that include `next_appointment_at` trigger calendar/appointment scheduling in the domain service layer.
6. When `notify_team = TRUE`, notifications are enqueued via the transactional Outbox pattern (`outbox_events`), guaranteeing zero dropped notifications without blocking the database transaction.

## Consequences
- Guarantees non-repudiation and evidential integrity for all clinical and investigative notes.
- Eliminates accidental narrative loss while providing transparent correction mechanisms.
