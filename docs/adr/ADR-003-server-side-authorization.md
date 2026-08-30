# ADR-003: Server-Side 5-Stage Authorization Framework

## Status
Approved

## Context
Client safety and privacy mandate that UI-only visibility switches are never treated as security boundaries. Technical staff must also be restricted from sensitive family welfare narratives.

## Decision
Enforce authorization server-side through a 5-stage pipeline:
1. Authentication
2. Role Permission Key (Capability)
3. Team Scope Access
4. Record Restriction
5. Field Policy

IT Admins receive only system administration permissions and are blocked from client/case record endpoints.
