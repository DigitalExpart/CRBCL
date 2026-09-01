# CRBCL Offline Synchronization Engine Specification

## 1. Delta Pull Protocol

- Request: `POST /api/v1/sync/pull`
  ```json
  {
    "last_synced_at": "2026-09-01T12:00:00Z",
    "previously_cached_case_ids": ["uuid-1", "uuid-2"]
  }
  ```
- Response: Delta bundle containing updated authorized Cases, Clients, Notes, and explicit `tombstones` for cases where user authorization was revoked or restricted.

---

## 2. Tombstone Cascade Protocol

When a tombstone is received (`{ "entity_type": "CASE", "entity_id": "uuid-1", "reason": "RESTRICTED_OR_UNASSIGNED" }`), the mobile app invokes `LocalDatabaseHelper.instance.purgeCaseCascade(caseId)`:
- Purges the target Case record from SQLite.
- Cascades deletion to all associated child notes, client summary profiles, and pending sync outbox items referencing `case_id`.
- Prevents orphaned notes or sensitive client details from remaining stored locally.

---

## 3. Idempotency & Version Conflict Resolution

- Every offline mutation includes a unique `client_mutation_id`.
- Duplicate pushes return `ALREADY_PROCESSED` without creating duplicate records.
- Server version comparison: If `expected_version < server_version`, the server returns `CONFLICT`, prompting the caseworker to review server changes before overwriting.
