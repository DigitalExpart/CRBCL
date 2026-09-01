# ADR-029: Customizable & Role-Aware User Dashboard Engine

## Status
Accepted

## Context
Different agency roles (Caseworkers, Supervisors, Finance Staff, QA Managers, Executive Leadership) require distinct high-priority metric widgets on their home dashboard. Fixed global layouts force users to navigate away to find daily operational metrics. However, allowing arbitrary user-configured widgets must not bypass permission controls or execute client-supplied frontend aggregation logic over sensitive database tables.

## Decision
We implement a **Role-Aware, Server-Controlled Customizable Dashboard Engine**.

### Architecture:
1. **Server-Side Widget Registry**:
   - Widgets are registered in a backend catalog with strict capability requirements (e.g., `financial_summary` requires `FINANCE_REQUEST_READ`).
   - Standard widget registry includes:
     - `active_cases`, `children_out_of_home`, `new_intakes`, `pending_approvals`, `cases_without_notes`, `cases_over_12_months`, `upcoming_court_dates`, `audits_due`, `placement_capacity`, `financial_summary`, `my_assigned_cases`, `recent_activity`.
2. **Per-User Relational Preferences**:
   - `user_dashboard_widgets` table stores individual user layouts (`user_id`, `widget_key`, `position`, `width`, `height`, `is_visible`, `settings`).
3. **Frontend Drag-and-Drop**:
   - Implemented using `@hello-pangea/dnd`. Layout position changes are persisted via API `POST /api/v1/dashboard/layout`.
4. **Enforced Security Endpoint**:
   - The dashboard aggregation API (`GET /api/v1/dashboard/widgets/data`) evaluates the current user's permissions for every requested widget key.
   - If a user attempts to fetch a widget they lack permission for, the server omits or returns forbidden status for that specific widget payload.

## Consequences
- Every user gets a personalized, drag-and-drop dashboard suited to their role.
- Complete security enforcement: a user cannot display financial metrics, medical alerts, or restricted cases by manipulating frontend state.
