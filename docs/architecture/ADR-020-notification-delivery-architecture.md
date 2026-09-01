# ADR-020: Notification Delivery Architecture & Outbox Integration

## Status
Accepted (Phase 9)

## Context
The CRBCL platform requires asynchronous notifications across multiple internal and external channels:
- In-App Notification Center and Header Bell
- Outbound Email (Supervisory alerts, case transfer requests, compliance reminders)
- Outbound SMS (Client appointment reminders, critical compliance deadlines)

Direct synchronous calls to external communication providers (SendGrid, Resend, Twilio) inside business transaction handlers risk distributed failure, long HTTP latencies, connection timeouts, and rollback of legitimate case operations. Additionally, privacy laws and child welfare regulations strictly forbid leaking identifiable case facts, allegations, or placement details over unencrypted external channels.

## Decision

### 1. Transactional Outbox Pattern & Background Dispatch
- All business actions emit an `OutboxEvent` in the same database transaction as the business entity write.
- A decoupled background worker polls pending outbox events, matches recipient routing rules, checks user `notification_preferences`, generates `notifications` (in-app) and `notification_deliveries` (external channels), and invokes provider adapters.
- Failure of external providers (e.g. SMTP drop or Twilio outage) will **never** roll back or impede a core child protection transaction.

### 2. Multi-Channel Provider Abstractions
- Abstract base classes `EmailProvider` and `SmsProvider` define the delivery contracts.
- Development / Test environment uses `ConsoleEmailProvider` and `ConsoleSmsProvider`.
- Production environment configures `ResendEmailProvider` or `SendGridEmailProvider` and `TwilioSmsProvider` via environment variables without hardcoded credentials.

### 3. External Privacy Guard
- External Email and SMS messages must adhere to a strict **Minimal Identifiable Information** policy.
- Payloads contain generic guidance and secure action links (e.g., "Reminder: You have an appointment with Chief Red Bear Children's Lodge on Oct 14, 10:00 AM. Sign in to CRBCL to review details.").
- **Strictly Prohibited in Email/SMS**: Child names, allegations, sexual abuse references, medical diagnoses, case notes, foster home residential street addresses.

### 4. Contact Consent Verification
- External SMS reminders to clients/persons are sent **only if** `PersonContact.sms_consent == True`.
- Without explicit consent, external SMS delivery is cancelled, and only in-app staff alerts are recorded.

### 5. Idempotent Delivery & Deterministic Reminder Keys
- All deliveries track a deterministic `idempotency_key` (e.g. `COURT_REMINDER_7D:{user_id}:{court_event_id}:{date_bucket}`).
- Running reminder cron jobs repeatedly or restarting workers will not generate duplicate deliveries or spam recipients.

### 6. Delivery Lifecycle & Safe Retries
- `notification_deliveries` states: `PENDING`, `PROCESSING`, `SENT`, `FAILED`, `RETRYING`, `CANCELLED`.
- Transient network failures increment `attempt_count` and schedule exponential backoff retries. Exhausted retries mark the delivery as `FAILED` with a safe, non-sensitive error code.

## Consequences
- **Positive**: Zero coupling between domain persistence and third-party delivery uptime.
- **Positive**: Complete compliance with privacy regulations and anti-spam consent standards.
- **Positive**: Total idempotency across background workers and scheduled reminder jobs.
