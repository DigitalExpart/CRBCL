# CRBCL Platform — Supabase PostgreSQL Operations Guide

## 1. Architectural Overview & Boundaries

The Chief Red Bear Children's Lodge (CRBCL) Family Wellness Case Management Platform utilizes **Supabase as dedicated managed PostgreSQL + PostGIS infrastructure**. 

### Strict Architectural Boundaries
- **No Direct Browser Access**: The React frontend interacts strictly with the native FastAPI backend (`/api/v1/*`).
- **No Supabase Auth / JS SDK Replacement**: Authentication, RBAC, ABAC, and audit logging remain native to the approved FastAPI + SQLAlchemy domain layer.
- **Credential Isolation**: Database connection strings, passwords, and service keys exist only on the backend host / runtime environment. No database credentials or connection secrets are exposed to the client bundle or git repositories.

```
+------------------+         REST API / HTTPS         +-----------------------+
|  React Frontend  |  ---------------------------->   |    FastAPI Backend    |
| (Vite SPA / PWA) |  <----------------------------   | (Native Auth + RBAC)  |
+------------------+         JSON / JWT Bearer        +-----------------------+
                                                                  |
                                                           SQLAlchemy Core
                                                            Async Engine
                                                                  |
                                                                  v
                                                      +-----------------------+
                                                      |  Supabase PostgreSQL  |
                                                      |  + PostGIS Extensions |
                                                      |  (ca-central-1 Pooler)|
                                                      +-----------------------+
```

---

## 2. Connection Modes & Dialects

Supabase provides two primary connectivity pathways depending on network infrastructure:

### A. IPv4 Session Pooler (Standard / Recommended)
Because direct connection domains (`db.[project-ref].supabase.co`) resolve exclusively via IPv6 `AAAA` records on some ISP and cloud networks, applications running on IPv4 networks connect through Supabase's AWS pooler hostname:

- **Host**: `aws-0-[region].pooler.supabase.com` (e.g., `aws-0-ca-central-1.pooler.supabase.com`)
- **Port 5432 (Session Mode)**: Used for both the FastAPI runtime engine and Alembic sync migrations. Supports prepared statements, connection pooling, and DDL schema operations.
- **Port 6543 (Transaction Mode)**: Used only for high-concurrency serverless query workers that do not execute prepared statements or DDL locks. **Do not use Port 6543 for Alembic migrations.**
- **Username Format**: `postgres.[project-ref]` (e.g., `postgres.lxipkalnzvqnkjtzszei`)

### B. Python Database Drivers
1. **Async Runtime (FastAPI / SQLAlchemy Async Engine)**:
   - Driver: `asyncpg` (v0.30.0+)
   - URL Format: `postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?ssl=require`
2. **Synchronous CLI (Alembic Migrations / Admin Scripts)**:
   - Driver: `psycopg` (Psycopg 3 binary v3.2.0+)
   - URL Format: `postgresql+psycopg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require`

---

## 3. Required Database Extensions

Before applying schema migrations, the following extensions must be enabled in the database:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "postgis" SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pg_trgm" SCHEMA extensions;
```

All 4 extensions are active on the CRBCL production Supabase instance.

---

## 4. Alembic Migration Procedure

Schema definitions are declaratively versioned under `backend/migrations/versions/`.

### Applying Migrations to Supabase
```powershell
cd backend
$env:DATABASE_SYNC_URL="postgresql+psycopg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require"
.\.venv\Scripts\alembic.exe upgrade head
```

### Applied Revision History
- `001_platform_foundation`: 34 tables (users, roles, permissions, teams, audit_events, outbox_events, clients, households, cases, notes, timeline_events).
- `002_people_families`: 17 tables (persons, addresses, contacts, physical descriptions, cultural profiles, strengths, challenges, medical profiles, allergies, conditions, medications, providers, schools, family relationships, genogram nodes/edges, person merges).
- `003_intake_referrals`: 9 tables (referrals, referral_sequences, referral_reporters, referral_people, referral_concerns, referral_incidents, referral_links, child_dispositions, intake_decisions).
- **Total Tables**: 60 relational tables.

---

## 5. Database Seed Procedure

The database seed script (`backend/app/core/seed.py`) is **strictly idempotent**. It can be executed repeatedly without generating duplicate teams, roles, permissions, lookup lists, or lookup values.

### Running Seed against Supabase
```powershell
cd backend
.\.venv\Scripts\python.exe -m app.core.seed
```

### Seeded Baseline Objects
- **Permissions**: 61 granular capability permissions across 12 categories.
- **Roles**: 11 system roles with Indigenous child welfare mappings.
- **Teams**: 22 operational and program teams.
- **Lookup Lists**: 12 system lookup categories (referral sources, concern types, response priorities, etc.).
- **Lookup Values**: 73 standard lookup options.
- **Initial Dev Admin**: `admin@crbcl.ca` (Development environment only).

---

## 6. Testing & Validation Workflows

### Fast Path (In-Memory Unit & Regression Suite)
By default, the pytest test suite executes against SQLite in-memory for sub-second developer feedback loops:
```powershell
cd backend
.\.venv\Scripts\pytest.exe -v
# Output: 29 passed, 1 skipped in ~30s
```

### Integration Path (Live Supabase PostgreSQL End-to-End Suite)
To validate the full HTTP, authorization, sequence generation, timeline logging, multi-child disposition matrix, and automated case routing against live Supabase PostgreSQL:
```powershell
cd backend
$env:TEST_POSTGRES_DB="1"
.\.venv\Scripts\pytest.exe -v tests/test_supabase_e2e.py -s
# Output: 1 passed in live PostgreSQL mode
```

---

## 7. Security & Secrets Management Rules

1. **Zero Git Secrets**: `.env` files are explicitly excluded via `.gitignore`.
2. **Template Synchronization**: Only `.env.example` containing non-secret placeholder variables is committed.
3. **No Frontend Exposure**: `VITE_*` variables must never contain database passwords, connection strings, or service keys.
4. **Dual Repository Sync**: All codebase commits and documentation must be pushed concurrently to both upstream repositories:
   - `https://github.com/DigitalExpart/CRBCL.git`
   - `https://github.com/innovatorledger-web/crbcl.git`

---

## 8. Troubleshooting

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `psycopg.OperationalError: could not translate host name` | Direct Supabase domain (`db.[ref].supabase.co`) resolves to IPv6 only on IPv4 networks. | Use the AWS pooler host `aws-0-[region].pooler.supabase.com` with username `postgres.[ref]`. |
| `prepared statement already exists` / `prepared statement does not exist` | Using Transaction Pooler (Port 6543) with drivers expecting prepared statements or DDL locks. | Connect to Port 5432 (Session Pooler mode) for migrations and FastAPI engine. |
| `SSL connection has been closed unexpectedly` | SSL negotiation mode mismatch. | Ensure `?ssl=require` for asyncpg and `?sslmode=require` for psycopg. |
| `alembic_version lock timeout` | Simultaneous DDL migrations or uncommitted session locks. | Verify `poolclass=pool.NullPool` in `migrations/env.py` and run migrations sequentially. |
