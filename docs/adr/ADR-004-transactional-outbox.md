# ADR-004: Transactional Outbox Pattern

## Status
Approved

## Context
Asynchronous side-effects (e.g. notifications, email, webhooks) must never fail silently or be orphaned if a database transaction aborts.

## Decision
Write outbox events to `outbox_events` in the **exact same PostgreSQL transaction** as the primary business write. An asynchronous background worker polls and processes events with exponential backoff retries.

## Consequences
- Guaranteed at-least-once asynchronous event delivery.
- Zero risk of phantom notifications if a transaction rolls back.
