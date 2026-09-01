# ADR-027: Metadata-Driven Report Builder Architecture

## Status
Accepted

## Context
Ad-hoc reporting tools are prone to SQL injection vulnerabilities and unconstrained query execution that can lock database tables or expose internal database schemas. Allowing frontend users or administrative users to input arbitrary SQL strings or database column names introduces high security risks.

## Decision
We implement a **Metadata-Driven Reporting Catalogue & Query Builder Engine**.

### Architecture:
1. **Server-Controlled Reporting Catalogue**: A static dictionary in backend memory defines all reportable datasets (`cases`, `clients`, `intakes`, `placements`, `finance`, `qa_audits`).
2. **Field Whitelist & Expression Mapping**:
   - Each reportable field defines a stable key (e.g., `case.case_number`), human-readable label, data type, groupable/sortable/aggregatable capabilities, and required permission.
   - Field keys map directly to internal SQLAlchemy column expressions. User inputs NEVER touch SQL string concatenation.
3. **Safe Operator Whitelist**:
   - Allowed filter operators are strictly limited to `eq`, `neq`, `contains`, `gte`, `lte`, `in`, `is_true`, `is_false`.
   - Operators are validated against field data types server-side.
4. **Aggregate Whitelist**:
   - Aggregations (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`) can only be performed on approved numerical or identity fields.
5. **Execution Flow**:
   ```
   User UI Selection (Keys & Values)
           ↓
   FastAPI Schema Validation
           ↓
   Security & Permission Check
           ↓
   SQLAlchemy Statement Generation (ORM)
           ↓
   Row-Level & Case Restriction Injection
           ↓
   Database Execution & Result Formatting
   ```

## Consequences
- 100% immune to SQL injection and un-sanitized database query execution.
- Easy to add new reportable fields by declaring them in the server catalogue.
- Backend can strictly limit query complexity, pagination size, and execution timeouts.
