# CRBCL Reporting, Quality Assurance & Passports Domain Architecture

## Overview
Phase 11 introduces the organization-wide reporting, quality assurance, audit tickler, child/parent passport generation, and customizable dashboard architecture for Chief Red Bear Children's Lodge (CRBCL).

---

## Domain Capabilities

### 1. Canned & Ad-Hoc Reporting System
- **Canned Reports**:
  1. **Intake Monthly Report**: Monthly intake volume, dispositions, concerns, and team routing (reporter identity redacted unless authorized).
  2. **Active Cases by Worker**: Worker caseload breakdown by status, case type, and risk.
  3. **Cases by Type & Status**: Cross-tabulation of cases across protection, voluntary, kinship, and prevention types.
  4. **Children Currently in Placement**: Active non-discharged placement episodes by home type and age.
  5. **Program Utilisation Report**: Active enrollment metrics across wellness programs.
  6. **Financial Summary Report**: Spending rollups by budget line, funding source, and placement billing (uses Phase 10 engine).
- **Ad-Hoc Builder**: Metadata-driven report generator allowing field selection, safe filtering (`eq`, `contains`, `date_range`), grouping, and aggregations (`COUNT`, `SUM`, `AVG`).
- **Saved Reports & Runs**: User saved report definitions with granular visibility (`PRIVATE`, `TEAM`, `AUTHORIZED_SHARED`) and run history tracking (`report_runs`).

### 2. Child & Parent Passports
- **Child Passport**: Comprehensive, permission-aware single document compiling demographics, family relationships, emergency contacts, medical profiles (requires `CLIENT_MEDICAL_READ`), medications, providers, school, cultural information, and placement history.
- **Parent Passport**: Authorized summary of identity, family relationships, active case status, and services.
- **Security & Printing**: Generates printable views and PDF downloads with confidentiality footers and audit event logging (`CHILD_PASSPORT_GENERATED`, `PARENT_PASSPORT_GENERATED`).

### 3. Quality Assurance & Audit Tickler Engine
- **Versioned QA Templates**: Administrative checklists versioned to preserve historical audit integrity (`qa_audit_templates`, `qa_audit_template_versions`).
- **Case Audits**: Checklist reviews with `YES` / `NO` / `N/A` items, severity findings, and follow-up tracking (`qa_audits`).
- **Audit Tickler Engine**: Automatically calculates compliance due windows (`MONTHLY`, `QUARTERLY`, `SEMI_ANNUAL`, `ANNUAL`) and categorizes cases into `OK`, `DUE_SOON`, and `OVERDUE`.
- **QA Dashboard**: Aggregates overdue audits, cases without recent notes (30+ days), cases open >12 months, children in placement, and pending approvals.

### 4. Role-Aware & Customizable Dashboard Engine
- **Widget Registry**: Server-backed catalog of 12 standard operational metrics.
- **User Personalization**: Drag-and-drop widget layout ordering (`user_dashboard_widgets`) with `@hello-pangea/dnd`.
- **Executive Command Center**: High-level organizational KPIs for Executive Directors and Supervisors.

---

## Technical Security Boundaries
- **Case Restrictions**: Restricted cases (`case_restrictions`) are automatically filtered out from all report queries and QA tickler lists for restricted users.
- **Field Sensitivity**: Medical, reporter, and financial fields are conditionally included only when the caller possesses required capability tokens.
- **Export Controls**: All CSV/XLSX/PDF exports log audit events and enforce identical query filters as interactive UI tables.
