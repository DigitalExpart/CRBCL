# CRBCL Platform Architecture — Phase 1 Platform Foundation

## 1. System Overview

Chief Red Bear Children's Lodge (CRBCL) Family Wellness Case Management Platform establishes a modern native architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                 React 18 / Vite Frontend                    │
│      (TailwindCSS, TanStack Query, Radix UI components)     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / JSON + HttpOnly Cookies
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend Service                   │
│  - Modular Monolith architecture                            │
│  - Native Authentication (Bcrypt + HttpOnly JWT)            │
│  - 5-Stage Capability Authorization & Team Scoping          │
│  - Append-only Compliance Audit & Access Logging            │
│  - Sacred Timeline Business Event Tracking                  │
│  - Transactional Outbox Event Dispatcher                    │
│  - Storage Provider Abstraction                             │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│ PostgreSQL 16 + PostGIS     │ │ Redis 7                     │
│ - pg_trgm for fuzzy search  │ │ - Session caching           │
│ - UUID Primary Keys         │ │ - Background outbox worker  │
│ - Strict Relational Schemas │ │                             │
└─────────────────────────────┘ └─────────────────────────────┘
```

## 2. Core Architectural Principles

1. **Separation of History Concerns**:
   - `audit_events`: Compliance & security audit logs (tamper-evident, non-editable).
   - `timeline_events`: Sacred Timeline business events documenting family milestones.
   - `outbox_events`: Guaranteed asynchronous side effects.

2. **Server-Side Authorization Boundary**:
   - The frontend is a presentation layer; the backend is the authoritative security boundary.
   - IT Administrators administer system configuration but **do not** possess clinical case access.

3. **Transactional Integrity**:
   - Domain operations (e.g. Case Note creation) persist business entities, audit logs, timeline milestones, and outbox triggers in a **single atomic database transaction**.
