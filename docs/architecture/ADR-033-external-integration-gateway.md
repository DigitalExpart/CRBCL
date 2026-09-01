# ADR-033: External Integration Gateway & Isolated Provider Architecture

## Context
The CRBCL platform requires integrations with external enterprise providers (Microsoft 365, Telematics, AI models, OCR engines, and Social Communications platforms). Directly invoking third-party APIs from frontend components or raw database triggers exposes client data to catastrophic privacy leaks, secret leakage, and cascading failure propagation.

## Decision
We implement a **FastAPI External Integration Gateway** pattern. All outgoing enterprise requests flow through a multi-layer isolation pipeline:

```
[ Domain Request ] ──> [ Integration Gateway ] ──> [ Policy / Auth Check ] ──> [ Data Minimization ] ──> [ Outbox / Async Job ] ──> [ Provider Adapter ] ──> [ External API ]
```

### Gateway Guarantees
1. **Zero Direct DB Access**: External providers NEVER receive database credentials, connection strings, or direct SQL execution capabilities.
2. **Authorization First**: Backend permissions (`Permissions.INTEGRATION_MANAGE`, domain capability check) are verified before any payload construction begins.
3. **Data Minimization Engine**: All outgoing payloads pass through domain-specific redaction filters. PII/PHI is stripped or tokenized.
4. **Outbox & Failure Isolation**: External calls execute asynchronously via the Outbox pattern. Failure of an external provider (e.g., Microsoft Graph timeout) never rolls back or blocks internal CRBCL transactions.
5. **Abstract Provider Pattern**: Domain code depends strictly on abstract base classes (`MicrosoftProvider`, `OcrProvider`, `AiProvider`). Production adapters (`SamsaraProvider`, `AnthropicProvider`) are swapped seamlessly with zero code changes.

## Status
Accepted.
