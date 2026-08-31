# CRBCL Database Schema Reference

## Hosted Database Infrastructure
- **Engine**: Supabase PostgreSQL / PostGIS 15+
- **Current Revision**: `005_assessment_engine`

---

## Entity-Relationship Catalog

### Platform Foundation (001)
- `users`: Staff user accounts with password hashes, verification, and active state.
- `roles`: Role definitions (`caseworker`, `supervisor`, `director`, `it_admin`, etc.).
- `permissions`: Fine-grained permission keys (`case.read`, `case_note.lock`, `case.transfer.approve`, etc.).
- `user_roles`: User-to-Role assignments.
- `role_permissions`: Role-to-Permission assignments.
- `teams`: Organizational departments and units.
- `team_memberships`: User team memberships with primary flags.
- `lookup_lists` & `lookup_values`: Configurable reference lookup values.
- `audit_events`: Tamper-evident audit trail for data modifications.
- `timeline_events`: Sacred timeline storytelling stream.
- `outbox_events`: Transactional outbox event bus for reliable notifications.

### People & Families (002)
- `persons`: Master person directory with Indigenous cultural affiliations and demographics.
- `person_identifications`: Legal IDs (Status Card, Treaty #, Health Card).
- `person_contacts`: Addresses, phone numbers, emergency contacts.
- `person_relationships`: Kinship networks, family relationships.
- `person_cultural_profiles`: Band affiliations, clan, language, elder connections.
- `clients`: Program enrollment wrappers over canonical `persons`.
- `families`: Family wellness files.
- `family_members`: Links linking persons to families with roles and caregiving status.

### Intake & Referrals (003)
- `referral_sequences`: Atomic integer sequence per year (`INT-YYYY-NNNNNN`).
- `intake_referrals`: Front-door referral records.
- `referral_people`: Subjects and collaterals identified during intake.
- `referral_concerns`: Safety concerns and protective factors.
- `referral_incidents`: Specific reported incident details.
- `intake_decisions`: Screening decisions and supervisor approval.
- `child_dispositions`: Multi-child disposition routing records.

### Core Case Management (004)
- `cases`: Master case file entity.
- `case_sequences`: Year-month counters (`CRB-YYYYMM-NNNN`).
- `case_people`: Case roster linking canonical `persons`.
- `case_assignments`: Caseworker and investigator staff assignments.
- `case_external_workers`: External contacts (Band Representatives, Legal Counsel).
- `case_sources`: Collateral & Other sources.
- `case_links`: Sibling and concurrent case linkages.
- `case_restrictions`: Conflict-of-interest access control blocks.
- `case_transfers`: Inter-team transfers with approval queues.
- `case_status_history`: Formal status lifecycle audit log.
- `case_notes`: Clinical case documentation.
- `case_note_people`: Individuals present during note contact.
- `case_note_attachments`: Documents attached to case notes.
- `case_note_addenda`: Append-only addenda for locked notes.

### Configurable Assessment Engine (005)
- `assessment_templates`: Logical template definitions (`HOME_ASSESSMENT`, `THREAT_ASSESSMENT`, `AIEI_ASSESSMENT`).
- `assessment_template_versions`: Version-controlled immutable template snapshots with draft/publish workflows.
- `assessment_sections`: Sections within a template version with order, requirement flags, and visibility rules.
- `assessment_questions`: Questions with data types (`BOOLEAN`, `NUMBER`, `TEXT`, `LONG_TEXT`, `SINGLE_SELECT`, `MULTI_SELECT`, `DATE`, `DATETIME`, `JSON`), validation, and conditional dependencies.
- `assessment_question_options`: Available choices and score values for single and multi-select questions.
- `assessments`: Conducted assessment instances bound to cases, persons, and specific template versions (`ASM-YYYYMM-NNNN`).
- `assessment_answers`: Relational, normalized typed answer columns (`boolean_value`, `number_value`, `text_value`, `date_value`, `datetime_value`, `json_value`, `notes`).
- `assessment_answer_options`: Join table for multi-select option selections.
- `assessment_unlock_events`: Append-only Director unlock audit log with mandatory reasons.
- `assessment_status_history`: Full state lifecycle audit log (`DRAFT`, `IN_PROGRESS`, `COMPLETED`, `LOCKED`, `VOID`).
- `assessment_sequences`: Year-month atomic sequential numbering (`ASM-YYYYMM-NNNN`).

### Safety Plans • Case Plans • Goals • Signatures (006)
- `plan_sequences`: Year-month atomic counter sequence (`PLN-YYYYMM-NNNN`).
- `plans`: Master Safety Plan and Case Plan container entity.
- `plan_versions`: Immutable, versioned plan snapshots (`DRAFT`, `IN_REVIEW`, `FINALIZED`, `LOCKED`).
- `plan_participants`: Circle members, caregivers, workers, and signers with attendance status.
- `plan_concerns`: Relational harm statements and danger concerns with severities (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- `plan_strengths`: Protective capacities and cultural grounding strengths.
- `plan_goals`: SMART goals with target dates, completion timestamps, and status tracking.
- `plan_activities`: Concrete action steps linked to goals with responsible parties and due dates.
- `goal_progress_updates`: Longitudinal progress logs tracking goal milestone advancement.
- `plan_assessments`: Cross-entity relational links connecting clinical assessments to plans.
- `plan_signatures`: Cryptographic e-signatures (`CANVAS_DRAW`, `TYPED_ATTESTATION`, `PHYSICAL_UPLOAD`) bound to canonical SHA-256 document digests.
