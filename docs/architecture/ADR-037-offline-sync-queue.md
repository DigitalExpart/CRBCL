# ADR-037: Offline Sync Queue & Conflict Resolution Architecture

## Status
Approved

## Context
Child welfare caseworkers in Saskatchewan frequently operate in remote First Nations communities, rural areas, and client homes where cellular coverage is absent or unreliable. To maintain continuity of care and safety documentation, caseworkers must be able to view assigned case information, draft case notes, complete risk assessments, and capture photos offline. When connectivity is restored, local offline changes must be securely synchronized with the central CRBCL platform without data loss or overwriting concurrent updates.

## Decision
We adopt an **Offline Outbox Sync Queue Architecture** built on local SQLite storage on the mobile device coupled with server-side transactional synchronization endpoints (`/api/v1/sync/pull` and `/api/v1/sync/push`).

### Key Mechanics:
1. **Delta Pull (`/api/v1/sync/pull`)**:
   - The mobile client sends its `last_synced_at` timestamp.
   - The server queries records (Cases, Clients, Safety Plans, Appointments) within the caseworker's authorized scope updated since `last_synced_at`.
   - Deleted items are returned as tombstone records.
2. **Offline Outbox Push (`/api/v1/sync/push`)**:
   - Local offline mutations (e.g. newly drafted Case Notes, completed Assessments) are written atomically to a local SQLite `sync_queue` table with a client-generated UUID and local creation timestamp.
   - Upon network reconnection, the device sends the queued mutations in batch to `/api/v1/sync/push`.
3. **Conflict Resolution Strategy**:
   - **Immutable Records (Case Notes, Addendums)**: Append-only semantics guarantee zero conflict. Draft notes written offline are inserted as new authoritative records upon push.
   - **Mutable Records (Client Contact Info, Safety Plans)**: Last-Write-Wins based on server timestamp, with a fallback `SyncConflict` flag raised for manual supervisor review if concurrent server modifications occurred.
4. **Idempotency**:
   - Each push item contains a unique `client_mutation_id`. The server records processed IDs in `migration_ledger` / `idempotency_keys` to prevent duplicate processing on network retry.

## Consequences
- Caseworkers can perform critical field duties 100% offline.
- Server database transactions remain completely isolated until explicit push validation occurs.
- Immutability of case notes ensures legal defensibility of field documentation.
