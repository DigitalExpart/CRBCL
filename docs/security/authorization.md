# CRBCL Security & Authorization Architecture

## Access Control Model
CRBCL enforces strict multi-layered authorization:
1. **JWT Bearer Authentication**: FastAPI validates signed JWT tokens issued at login.
2. **Role-Based Access Control (RBAC)**: Fine-grained permissions catalog (`Permissions` enum) mapped to Roles.
3. **Team-Scoped Access**: Caseworkers are bounded to their assigned team(s) unless holding cross-team executive roles.
4. **Conflict-of-Interest Case Restrictions (ADR-010)**:
   - Evaluated centrally at `PermissionService.check_case_access`.
   - When a worker has an active restriction on a case, any API request for that case returns `HTTP 403 Forbidden` immediately, overriding general `case.read` or `case.update` permissions.
5. **Data Protection**:
   - Zero database credentials exposed to browser.
   - Frontend communicates exclusively via authenticated REST API endpoints on `/api/v1/*`.
