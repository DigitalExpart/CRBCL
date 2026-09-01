# CRBCL Production Operations & Maintenance Runbook

## 1. Deployment & Rollback Procedures

### Standard Deployment Sequence
1. **Pre-flight Checks**: Execute complete regression suite (`pytest -v`), `ruff check`, and frontend build (`npm run build`).
2. **Database Backup**: Trigger manual Supabase backup snapshot prior to applying migrations.
3. **Apply Database Migration**: Run `alembic upgrade head`.
4. **Deploy Application Services**: Deploy updated backend containers and static frontend build assets.
5. **Post-Deployment Health Audit**: Verify `GET /health` and check integration registry status.

### Rollback Protocol
- **Application Rollback**: Revert deployment image to previous git release tag (e.g. `v1.0.0-rc.1`).
- **Database Rollback**: Revert migration via `alembic downgrade -1` or restore pre-deployment database snapshot if breaking DDL was executed.

---

## 2. Worker & Service Incident Recovery

1. **Outbox Worker Failure**:
   - Symptom: Outbox notification backlog growing (`integration_sync_runs` or `outbox_events` pending).
   - Remedy: Restart FastAPI background task worker process. Outbox engine automatically retries failed events using exponential backoff.
2. **Account Lockout Reset**:
   - If an executive or caseworker is locked out due to failed password attempts:
     ```python
     user.locked_until = None
     user.failed_login_count = 0
     ```
3. **Integration Gateway Emergency Toggle**:
   - Administrative endpoint `POST /api/v1/integrations/{provider_key}/toggle` allows IT Admin to instantly disable an external integration (`is_enabled=False`) without restarting application nodes.
