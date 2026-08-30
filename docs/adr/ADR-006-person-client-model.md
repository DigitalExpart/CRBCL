# ADR-006: Canonical Person vs. Client Data Architecture

## Status
Approved

## Context
In child and family wellness case management, real-world human beings interact with the system across multiple distinct contexts:
- Children receiving protective or prevention services
- Parents, guardians, grandparents, and extended kinship caregivers
- Collateral contacts, reporters, and witnesses
- School educators and healthcare providers
- Members of residential households and placement facilities
- Community leaders and emergency contacts

If the platform models individuals solely through an isolated `clients` table:
1. Non-client family members (e.g. a grandmother or cousin residing in the home) cannot be modeled without creating artificial "clients".
2. When a collateral source or parent later becomes an active service recipient, their identity would be duplicated, fragmenting medical histories, addresses, and relationships.
3. Complex kinship structures and households cannot be faithfully captured without redundant person records.

## Decision
Adopt a **Canonical Person Model** with specialized contextual profiles:

```
┌─────────────────────────────────────────────────────────────┐
│                           persons                           │
│  - Canonical human identity & master demographic record     │
│  - Normalized names, aliases, DOB, Indigenous identity      │
│  - Unified duplicate detection & historical address ledger  │
└──────────────┬───────────────────────────────┬──────────────┘
               │ 1:0..1                        │ 1:M
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│           clients           │ │      family_members /       │
│  - Formal case management   │ │    household_memberships    │
│  - Intake date & risk level │ │ - Roles & kinship links     │
│  - Clinical medical profile │ │ - Multi-household residence │
│  - School enrollments       │ │ - Genogram relationship     │
│  - Strengths & challenges   │ │   connections               │
└─────────────────────────────┘ └─────────────────────────────┘
```

### Key Principles
1. **Single Real-World Identity**: Every human being is recorded once in `persons`.
2. **Client as Service Role**: The `clients` table holds specialized service delivery data and references `person_id`.
3. **Frontend API Compatibility**: The `/api/v1/clients` and `/api/v1/clients/{id}` endpoints transparently join and return person demographics alongside client case attributes, ensuring full backward compatibility with the existing React UI while enabling relational depth.
4. **Relational Kinship**: Family relationships (`family_relationships`) and residential living arrangements (`household_memberships`) link directly to `persons`, allowing accurate Genograms and Household Maps.

## Consequences
- **Positive**: Eliminates identity duplication across families and cases. Supports multi-generational kinship care and non-client caregivers naturally.
- **Positive**: Enables pg_trgm fuzzy matching across all known individuals before opening new files.
- **Manageable**: Repositories join `persons` and `clients` seamlessly for client CRUD operations.
