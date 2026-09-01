# Ask Red Bear AI Gateway & Query Architecture

## Overview
Ask Red Bear is CRBCL's assistive AI assistant. It provides case summarization and natural language navigation through a secure, permission-scoped gateway (`AiGateway`).

## Intent Classification & Tool Allowlist
When a user asks a natural language question (e.g., *"What are my active cases in Fort Qu'Appelle?"*), Ask Red Bear classifies intent into approved tools:
- `get_my_cases`
- `get_case_summary`
- `get_upcoming_appointments`
- `run_approved_report`

**Arbitrary SQL execution or raw database access is strictly prohibited.**

## Data Minimization & Redaction
Prior to sending context to the AI Provider (`FakeAiProvider` / `AnthropicProvider`), the gateway enforces:
- Case restriction exclusion
- Medical detail stripping (unless caller possesses `person.medical.read`)
- Reporter identity redaction (unless caller possesses `intake.reporter.read`)
- Financial details redaction (unless caller possesses `finance.request.read`)
