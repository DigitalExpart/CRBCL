# Audit, Sacred Timeline, and Transactional Outbox

## Event Distinction

| System | Purpose | Target Audience | Storage Rule |
| :--- | :--- | :--- | :--- |
| **Audit Events** | Regulatory compliance, forensic tracking, security auditing | QA, Auditors, Leadership | Append-only, sanitized, non-editable |
| **Access Events** | Read-access tracking on sensitive case files | QA, Security | Append-only, records IP and user |
| **Sacred Timeline** | Longitudinal family wellness narrative & case history | Caseworkers, Elders, Families | Meaningful business milestones |
| **Transactional Outbox**| Reliable asynchronous messaging & integration delivery | Background Workers | Processed, retried, marked complete |

## Single-Transaction Pattern

```python
async with db.begin():
    # 1. Primary write
    note = await case_note_repo.create(...)
    
    # 2. Compliance log
    await audit_service.log_event(event_type="CASE_NOTE_CREATED", ...)
    
    # 3. Business milestone
    await timeline_service.record_event(event_type=TimelineEventType.CASE_NOTE_ADDED, ...)
    
    # 4. Async trigger
    await outbox_service.enqueue(event_type="CASE_NOTE_NOTIFICATION", ...)

# Transaction commits atomically before background worker picks up outbox event.
```
