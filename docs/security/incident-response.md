# CRBCL Incident Response & Security Breach Protocol

## 1. Incident Classification Levels

- **SEV-1 (Critical Breach)**: Unauthorized access or disclosure of L4 Highly Sensitive data (client identity, reporter identity, medical records) or compromise of production database credentials.
- **SEV-2 (High Operational)**: Outage of primary database, MFA failure, or suspected compromised supervisor account.
- **SEV-3 (Medium Impact)**: Third-party integration failure, isolated rate-limit trigger, or failed OCR job queue.
- **SEV-4 (Low / Informational)**: Minor UI bug or non-security exception log.

---

## 2. Response Workflow

1. **Identification & Triage**: Detect anomaly via structured audit logs, error tracking, or user report.
2. **Containment**:
   - Suspend compromised user accounts or active JWT sessions (`user.is_active = False`).
   - Rotate database credentials or API keys via secret manager.
   - If needed, isolate application nodes while keeping database safe.
3. **Eradication & Recovery**: Patch root cause, verify clean database state using backup audit trails, re-enable services.
4. **Post-Incident Analysis**: Generate Root Cause Analysis (RCA) report and update STRIDE threat model.

---

## 3. Escalation Placeholders

- **CRBCL Privacy Officer**: `[CRBCL_PRIVACY_OFFICER_CONTACT_PLACEHOLDER]`
- **CRBCL Executive Director**: `[CRBCL_EXECUTIVE_DIRECTOR_CONTACT_PLACEHOLDER]`
- **IT Operations Lead**: `[CRBCL_IT_LEAD_CONTACT_PLACEHOLDER]`
