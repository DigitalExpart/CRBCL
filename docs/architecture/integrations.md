# CRBCL Enterprise Integrations Architecture Overview

## Architecture Overview
The Enterprise Integrations Layer isolates third-party integrations (Microsoft 365, Telematics, AI, OCR, Communications) behind a central Gateway architecture.

```
[ Frontend Client ] ──> [ FastAPI Gateway ] ──> [ Auth & Policy Check ] ──> [ Data Minimization Filter ] ──> [ Outbox Sync Queue ] ──> [ Abstract Provider Adapter ] ──> [ External API ]
```

### Components
1. **Integration Registry & Admin Service**: Manages provider configuration metadata, enabled flags, health checks, and last sync logs.
2. **Microsoft 365 Integration**: Outbound Outlook Calendar synchronization and privacy-safe Teams notification delivery.
3. **OCR Processing Engine**: Asynchronous document extraction with human-in-the-loop candidate confirmation.
4. **Ask Red Bear AI Gateway**: Assistive AI summaries and natural-language query routing with pre-execution authorization.
5. **Social & Communications Foundation**: Public outreach post management, decoupled from clinical case records.
