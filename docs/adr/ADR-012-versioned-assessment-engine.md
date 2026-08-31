# ADR-012: Versioned Assessment Engine & Normalized Answer Model

## Status
Accepted

## Context
The Chief Red Bear Children's Lodge (CRBCL) platform requires a robust, flexible assessment system to support:
1. **Home Assessment** (Home environment, physical conditions, sanitation, caregiver protective capacities, and safety determinations).
2. **Threat Assessment** (Present danger, impending danger indicators, alternative safety interventions, and time-series comparison).
3. **AIEI (Assessment of Indigenous Early Intervention & Prevention)** (Cultural engagement, clan/elder connection, housing, income, chemical dependency, and service recommendations).
4. **Future Assessment Questionnaires** (Kinship assessments, caregiver evaluations, trauma screenings) without altering the relational database schema for each new form.

A child welfare assessment is a legal instrument. Assessments must be immutable upon completion/locking, reportable via relational SQL queries, fully auditable, and resilient to template evolution over time.

---

## Decisions

### 1. Template & Version Separation
- `assessment_templates` defines the logical questionnaire category (e.g., `HOME_ASSESSMENT`, `THREAT_ASSESSMENT`, `AIEI_ASSESSMENT`).
- `assessment_template_versions` captures immutable revisions (`v1`, `v2`) with a discrete lifecycle: `DRAFT -> PUBLISHED -> RETIRED`.
- **Immutability of Published Versions**: Once a version is published, its sections, questions, options, and rules can never be edited or deleted. If questionnaire modifications are required, a new draft version is cloned, edited, and published as the next version.
- Existing historical assessments permanently reference the exact `template_version_id` under which they were completed.

### 2. Normalized Relational Questions & Answers
- Rather than storing user responses in a single unindexed JSON blob, responses are stored in normalized relational rows in `assessment_answers` referencing specific `question_id` records.
- Typed columns (`boolean_value`, `number_value`, `text_value`, `date_value`, `datetime_value`) and relational join table `assessment_answer_options` provide direct SQL querying, aggregations, and high-performance reporting without JSON parsing.
- Bounded JSONB fields (`validation_rules`, `visibility_condition`, `metadata_`) are used solely for configuration metadata.

### 3. Safe Declarative Conditional Visibility
- Questions can declare simple declarative rules (e.g., `{"depends_on_question_key": "substance_concern", "operator": "equals", "value": true}`).
- Dynamic client rendering and backend server-side validation evaluate conditions safely without executing arbitrary JavaScript expressions.

### 4. Assessment Lifecycle & Immutability
- Lifecycle: `DRAFT -> IN_PROGRESS -> COMPLETED -> LOCKED` (optional `CANCELLED`).
- Transitions occur through dedicated domain service commands (`/complete`, `/lock`, `/unlock`, `/reassign`) and are recorded in `assessment_status_history`.
- Once `LOCKED`, all updates to answers or determinations are strictly forbidden.

### 5. Director Unlock & Reassignment Governance
- An authorized Director/Supervisor holding the `assessment.unlock` permission may unlock a locked assessment.
- Unlocking requires a mandatory clinical/administrative justification, and creates an immutable entry in `assessment_unlock_events`, an audit record in `audit_events`, and a business entry in `timeline_events`.
- Reassignment of an assessment filed under the wrong case/family is performed via `POST /assessments/{id}/reassign` by authorized Directors, recording justification and audit trail.

### 6. Transparent Indicator Summaries (No Autonomous AI Decision Making)
- Danger and threat evaluations compute deterministic indicator tallies (e.g., count of active present danger indicators, count of protective capacities).
- Automated AI scoring, removal recommendations, or custody decisions are strictly prohibited. The final determination remains the exclusive responsibility of qualified caseworkers and supervisors.

### 7. Time-Series Comparison Engine
- Assessments of the same template lineage can be compared over time (`GET /api/v1/assessments/compare?ids=A,B`).
- The engine matches questions by stable keys and highlights answer deltas across subsequent home visits or threat assessments.

---

## Consequences
- **Positive**: Complete historical and legal reproducibility of completed assessments.
- **Positive**: Full SQL reportability without unstructured JSON parsing.
- **Positive**: Centralized case restriction and permission security enforced across all assessment endpoints.
- **Positive**: Reusable engine supports future questionnaires seamlessly.
- **Trade-off**: Requires explicit version creation workflows when updating questionnaires.
