# CRBCL Database Schema Documentation

## Foundation Extensions
- `uuid-ossp`: UUID v4 primary keys
- `postgis`: Geospatial capabilities for lodge/territory mapping
- `pg_trgm`: Trigram GIN indexing for high-speed client & person fuzzy matching

## Table Catalog

### 1. People & Canonical Identity (Phase 2)
- `persons`: Master demographic entity for all human beings.
- `person_addresses`: Historical address ledger with latitude/longitude and `on_reserve` flags.
- `person_contacts`: Normalized phone, email, and social contact channels.
- `person_physical_descriptions`: Distinguishing marks, scars, corrective lenses, and attributes.
- `person_cultural_profiles`: Ceremonies, Elders connected, land-based traditions, and language goals.
- `person_strengths`: Relational strength attributes linked to configurable lookups.
- `person_challenges`: Relational behavioral challenges and support flags.
- `person_merges`: Immutable audit history of controlled duplicate identity merges.

### 2. Clinical & Medical Foundation (Phase 2)
- `client_medical_profiles`: Overview medical, dental, and mental health notes.
- `client_allergies`: Allergy records with severity and reaction descriptions.
- `client_medical_conditions`: Diagnosed chronic and acute conditions.
- `client_medications`: Prescription ledger with dosage, frequency, prescriber, and start/end dates.

### 3. Provider Pool & School Directory (Phase 2)
- `providers`: Reusable pool of healthcare, counselling, dental, and cultural providers.
- `provider_locations`: Clinic/office locations for providers.
- `provider_specialties`: Specialty taxonomy tags.
- `client_providers`: Linkage connecting clients to assigned care providers.
- `schools`: School and daycare directory.
- `client_school_enrolments`: Enrollment history with Individualized Education Plan (IEP) tracking.

### 4. Family & Residential Households (Phase 2)
- `families`: Relational/biological family units.
- `family_members`: Person memberships in families with roles.
- `family_relationships`: Directional kinship connections (e.g. `mother_of`, `guardian_of`).
- `households`: Physical residential dwelling units.
- `household_memberships`: Resident living arrangements during specified date ranges.

### 5. Identity & Access Control (Phase 1)
- `users`: User profiles with normalized emails, bcrypt hashes, lockout tracking, and soft-delete.
- `sessions`: Revocable user sessions and refresh token hashes.
- `user_preferences`: Interface and notification preferences.
- `permissions`: Capability keys.
- `roles`: System roles.
- `role_permissions`: Join table mapping permissions to roles.
- `user_roles`: Join table mapping roles to users.
- `teams`: The 22 CRBCL teams.
- `team_memberships`: Primary and secondary team memberships.
- `user_team_access`: Direct team data-scoping grants.

### 6. Compliance & Event Infrastructure (Phase 1)
- `audit_events`: Append-only compliance change log with before/after state.
- `access_events`: Sensitive read-access logging (e.g. `CLIENT_PROFILE_VIEWED`).
- `timeline_events`: Sacred Timeline business history milestones.
- `outbox_events`: Transactional outbox with exponential backoff status tracking.
- `idempotency_keys`: Prevents duplicate executions of critical operations.

### 7. Configuration & Terminology (Phase 1)
- `system_config`: Typed key-value system settings.
- `lookup_lists`: Categorized lookup lists with active/inactive flags.
- `lookup_values`: Configurable items with display labels and sort orders.
- `terminology_keys`: Governance keys for bilingual cultural terms.
- `terminology_translations`: Approved translations in English and Cree.

### 8. Document Storage (Phase 1)
- `documents`: Metadata, private storage paths, validation status.
- `document_versions`: Document history and size records.
- `document_links`: Polymorphic entity linkage.
- `document_access_events`: Download and view audits.

### 9. Core Domain Entities (Phase 1)
- `clients`: Individual case profiles linked to canonical `person_id`.
- `cases`: Service files with human-readable case numbers (`CRB-YYYYMM-XXXX`).
- `case_notes`: Timestamped observations with confidentiality flags.
