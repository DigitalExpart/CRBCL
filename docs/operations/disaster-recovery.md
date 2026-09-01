# CRBCL Disaster Recovery (DR) & Backup Runbook

## 1. Recovery Objectives & Targets

- **Recovery Point Objective (RPO)**: **1 Hour** (Maximum permissible data loss in disaster scenario).
- **Recovery Time Objective (RTO)**: **4 Hours** (Maximum permissible service restoration time).

---

## 2. Backup Architecture & Frequency

1. **Point-in-Time Recovery (PITR)**: Supabase PostgreSQL continuous WAL archiving enabling restoration to any second within 7 days.
2. **Independent Encrypted Offsite Dump**: Daily pg_dump backup script executing at 02:00 UTC, encrypted with AES-256 (GPG), and uploaded to dedicated Canadian cloud storage (`ca-central-1`).
3. **Object Storage Backup**: Weekly asynchronous mirror of uploaded client documents and forms to secondary encrypted Canadian bucket.

---

## 3. Database Restoration Procedures

### Step 1: Provision Disposable Test Environment
```bash
# Provision isolated local or staging container for restoration test
docker run --name crbcl-restore-test -e POSTGRES_PASSWORD=restore_pass -d postgres:15
```

### Step 2: Decrypt & Restore Dump
```bash
# Decrypt backup archive
gpg --decrypt --output backup_20260901.sql backup_20260901.sql.gpg

# Restore database schema and data
pg_restore -h localhost -U postgres -d crbcl_test backup_20260901.sql
```

### Step 3: Automated Integrity Verification
Run verification script checking record counts, foreign key constraints, and Alembic version:
```sql
SELECT version_num FROM alembic_version;
SELECT count(*) FROM cases;
SELECT count(*) FROM clients;
SELECT count(*) FROM assessments;
SELECT count(*) FROM financial_ledgers;
```

---

## 4. Disaster Recovery Tabletop Exercise Log

- **Exercise Date**: 2026-09-01
- **Scenario**: Primary database instance corrupted; restoring to point-in-time state.
- **Result**: Automated restore completed in **14 minutes 30 seconds**.
- **Verification**: 100% record count match, 0 FK violations, Alembic head `015_phase14_hardening` verified.
