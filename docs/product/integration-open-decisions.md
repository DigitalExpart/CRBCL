# CRBCL Enterprise Integrations — Open Decisions & Policy Requirements

## Decisions Required from CRBCL Executive & Legal Leadership

1. **Microsoft 365 Tenant & Graph Scope Approval**:
   - *Question*: Shall CRBCL register an Azure AD Multi-Tenant Application or Single-Tenant App Registration for Outlook Calendar sync?
   - *Recommendation*: Use Single-Tenant delegated permissions (`Calendars.ReadWrite`) scoped strictly to agency staff accounts.

2. **AI Provider & Prompt Retention Policy**:
   - *Question*: Is Anthropic (Claude 3.5 Sonnet) or OpenAI approved for processing anonymized case summaries under Saskatchewan privacy law?
   - *Status*: Unverified. AI features remain `DISABLED` by default using `FakeAiProvider` until contractual Zero Data Retention (ZDR) agreements are finalized.

3. **OCR Document Classification Boundaries**:
   - *Question*: Which scanned document types (e.g., birth certificates vs medical reports vs court orders) are permitted for OCR extraction?
   - *Status*: Restrict initial OCR processing to general administrative documents and intake referral forms.

4. **Social Media & Public Outreach Approval Workflow**:
   - *Question*: Who holds authority to approve social media posts drafted in the Communications Hub before publication?
   - *Recommendation*: Mandatory two-person approval workflow (Communications Coordinator draft -> Executive Director approve).
