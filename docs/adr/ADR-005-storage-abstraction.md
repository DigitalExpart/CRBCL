# ADR-005: Document Storage Provider Abstraction

## Status
Approved

## Context
Documents uploaded to CRBCL must be stored securely, kept private by default, subjected to anti-malware validation, and decoupled from any single cloud vendor.

## Decision
Create an abstract `StorageProvider` with concrete implementations:
- `LocalStorageProvider` for local offline development.
- `S3StorageProvider` for future S3/MinIO cloud deployments.

Document URLs are never permanent or public; access is granted exclusively through short-lived signed URLs or authenticated proxy download endpoints.
