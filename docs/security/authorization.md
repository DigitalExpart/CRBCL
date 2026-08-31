# CRBCL Security & Authorization Architecture

## Access Control Model
CRBCL enforces strict multi-layered authorization:
1. **JWT Bearer Authentication**: FastAPI validates signed JWT tokens issued at login.
2. **Role-Based Access Control (RBAC)**: Fine-grained permissions catalog (`Permissions` enum) mapped to Roles.
3. **Team-Scoped Access**: Caseworkers are bounded to their assigned team(s) unless holding cross-team executive roles.
4. **Conflict-of-Interest Case Restrictions (ADR-010)**:
   - Evaluated centrally at `PermissionService.check_case_access`.
   - When a worker has an active restriction on a case, any API request for that case returns `HTTP 403 Forbidden` immediately, overriding general `case.read` or `case.update` permissions.
5. **Assessment Engine Permissions (Phase 5)**:
   - `assessment.template.read`: View assessment templates and published versions.
   - `assessment.template.manage`: Create, edit, and publish assessment template schemas (System Admin, Director).
   - `assessment.create`: Launch a new assessment instance for a case/family.
   - `assessment.read`: View assessment questionnaires and answer responses.
   - `assessment.update`: Edit draft or in-progress assessment responses.
   - `assessment.complete`: Finalize assessment with clinical determination.
   - `assessment.lock`: Finalize and seal assessment against subsequent modifications.
   - `assessment.unlock`: Strictly restricted Director permission to unlock a finalized assessment with mandatory written justification.
   - `assessment.reassign`: Strictly restricted Director permission to reassign an assessment to a different case/family.
   - `assessment.compare`: Access cross-assessment time-series comparison analytics.
   - `assessment.export` / `assessment.print`: Export or print assessment documents.
   - `assessment.delete`: Soft-delete draft assessments.

6. **Safety & Case Planning Permissions (Phase 6)**:
   - `plan.create`: Create a new Master Plan and initial Version 1.
   - `plan.read`: View plans, versions, goals, and signatures.
   - `plan.update`: Update plan metadata and draft content.
   - `plan.delete`: Soft-delete draft plans.
   - `plan.submit`: Submit draft plan for supervisor clinical review.
   - `plan.approve`: Supervisor approval of plan and finalization sealing.
   - `plan.return`: Supervisor return of plan for revisions.
   - `plan.finalize`: Seal plan and compute canonical SHA-256 document hash.
   - `plan.lock`: Lock finalized plan to enforce complete immutability.
   - `plan.unlock`: Director-only unlock with mandatory written justification.
   - `plan.clone`: Clone plan blueprint into a brand new master plan instance.
   - `plan.print` / `plan.export`: Generate printable legal plan document.
   - `plan.safety.read` / `plan.safety.write`: Safety Plan-specific authorization.
   - `plan.case.read` / `plan.case.write`: Case Plan-specific authorization.
   - `plan.goal.create` / `plan.goal.update` / `plan.goal.delete` / `plan.goal.complete`: SMART goal lifecycle management.
   - `plan.activity.create` / `plan.activity.update` / `plan.activity.delete` / `plan.activity.complete`: Concrete activity management.
   - `plan.signature.capture` / `plan.signature.read`: Electronic signature binding and verification.

7. **Data Protection & Cryptographic Integrity**:
   - Zero database credentials exposed to browser.
   - Frontend communicates exclusively via authenticated REST API endpoints on `/api/v1/*`.
   - Finalized plan versions are cryptographically hashed using SHA-256 deterministic JSON digest.
   - Electronic signatures legally bind to `(plan_version_id, document_hash)`.
   - Published template and plan versions are strictly immutable in PostgreSQL.
