# ADR-036: Ask Red Bear Assistive AI Security & Privacy Governance

## Context
Ask Red Bear provides natural-language search, navigation, and case summarization. AI model interactions pose risks if prompts receive unauthorized case data or if AI models are given direct SQL/database access.

## Decision
1. **Authorization-Before-Context (Mandatory)**: FastAPI authorization and case restriction checks run BEFORE any prompt or data context is assembled. If a user is restricted from Case X or lacks `person.medical.read`, Case X and medical data are 100% excluded from AI context.
2. **Zero Direct DB Access**: Ask Red Bear NEVER receives database credentials, connection strings, or arbitrary SQL execution capabilities. It interacts exclusively through a strict allowlist of backend service functions (`get_my_cases`, `get_case_summary`, `run_approved_report`).
3. **Assistive Only (Prohibited Decisions)**: Ask Red Bear is strictly assistive. It is explicitly prohibited from making autonomous decisions regarding child removal, abuse findings, custody, placement suitability, risk ratings, or financial approvals.
4. **Prompt Injection Defense**: Security boundaries are enforced deterministically by FastAPI middleware and service permissions, not by prompt instructions alone.

## Status
Accepted.
