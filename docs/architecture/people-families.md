# Phase 2 Architecture: People, Families & Households

## 1. Canonical Person vs. Client Model

In Phase 2, CRBCL establishes a canonical human identity model (`persons`) distinct from service-delivery profiles (`clients`):

```
┌─────────────────────────────────────────────────────────────┐
│                           persons                           │
│  - Master demographic record (name, DOB, identifiers)       │
│  - Historical addresses & contact channels                  │
│  - Physical description & distinguishing marks              │
│  - Cultural identity & language goals                       │
│  - Strengths & behavioral challenge tags                    │
└──────────────┬───────────────────────────────┬──────────────┘
               │ 1:0..1                        │ 1:M
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│           clients           │ │      family_members /       │
│  - Case management file     │ │    household_memberships    │
│  - Clinical medical profile │ │ - Kinship roles             │
│  - Prescriptions & allergies│ │ - Multi-household residency │
│  - School enrollments       │ │ - Genogram relationship     │
│  - Assigned care providers  │ │   connections               │
└─────────────────────────────┘ └─────────────────────────────┘
```

## 2. Separation of Biological Family vs. Residential Household

| Entity | Definition | Primary Use Case |
| :--- | :--- | :--- |
| **Family** (`families`) | Relational / biological kinship unit | Case plans, Genograms, family reunification, kinship care |
| **Household** (`households`) | Physical dwelling unit / living arrangement | Home assessments, geographic mapping, safety checks |

A child may belong to a biological family while residing in an auntie's household or a transitional lodge dwelling without distorting kinship lines.

## 3. Duplicate Detection & Controlled Merge

1. **Fuzzy Candidate Matching**: `POST /api/v1/clients/duplicate-check` uses trigram similarity across normalized names, date of birth, treaty numbers, health card numbers, and contact channels.
2. **Controlled Merge**: `POST /api/v1/clients/merge` re-points all client records, family memberships, relationships, and households from the duplicate source to the surviving target person, soft-deletes the source record, and writes an immutable entry to `person_merges` with a compliance audit log.

## 4. Reusable Provider Pool & School Directory

- Providers (physicians, counsellors, dentists, cultural helpers) are registered once in `providers` and linked to multiple clients via `client_providers`.
- Schools and daycares are registered in `schools` and track enrollment history with Individualized Education Plan (IEP) flags in `client_school_enrolments`.
