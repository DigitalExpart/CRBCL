# CRBCL Server-Side Authorization Model

## The 5-Stage Evaluation Pipeline

```
1. Authentication (JWT / Session Cookie + CSRF Defense)
      ↓
2. Role Permission Check (Capability: e.g. client.read, client.medical.read)
      ↓
3. Team Scope Validation (Is resource in user's assigned/accessible teams?)
      ↓
4. Record Restriction (Confidentiality, sealed records, worker assignment)
      ↓
5. Field Policy (Field-level masking / redaction on sensitive identifiers)
      ↓
ALLOW or DENY (HTTP 403)
```

## Phase 2 Field-Level Permissions
- `client.identifiers.read` / `client.identifiers.write`: Protects Treaty Numbers and Provincial Health Card Numbers.
- `client.medical.read` / `client.medical.write`: Governs clinical medical profiles, allergies, conditions, and medications.
- `client.school.read` / `client.school.write`: Governs school enrollments and Individualized Education Plan (IEP) details.
- `client.cultural.read` / `client.cultural.write`: Governs cultural teachings, ceremonies, and Elder connections.
- `family.relationships.read` / `family.relationships.write`: Governs family kinship relationships and Genogram structures.
- `household.read` / `household.write`: Governs physical residential addresses, households, and mapping.
- `provider.read` / `provider.write`: Governs healthcare and cultural provider directory entries.

## Technical vs Clinical Separation
- **IT Administrator**: Possesses `admin.*` and `audit.read` capabilities. Explicitly **denied** `client.*`, `case.*`, `case_note.*`, and `client.medical.*` permissions to prevent unauthorized access to sensitive family welfare records.
- **Caseworker**: Read/write access strictly scoped to assigned teams and caseload.
- **Clinical Staff / LPN**: Granted `client.medical.*` and `client.read/update` for healthcare management.
