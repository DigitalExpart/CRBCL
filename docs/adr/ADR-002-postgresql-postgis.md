# ADR-002: PostgreSQL with PostGIS & Trigram Search

## Status
Approved

## Context
Case management necessitates strict foreign key constraints, ACID transactional guarantees, fuzzy name search for family reunification, and geographic boundaries.

## Decision
Use PostgreSQL 16 with `postgis` and `pg_trgm` extensions enabled.

## Consequences
- ACID compliance across all transactional operations.
- GIN trigram indexes for high-speed client name search.
- Relational integrity preventing orphaned child/case records.
