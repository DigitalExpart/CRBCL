# CRBCL Database Schema Reference

## Hosted Database Infrastructure
- **Engine**: Supabase PostgreSQL / PostGIS 15+
- **Current Revision**: `004_case_management`

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
