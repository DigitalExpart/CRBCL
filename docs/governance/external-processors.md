# CRBCL External Processor Governance Matrix

## 1. Overview & Classification Schema

To prevent unvetted third-party services from accessing sensitive Child and Family Services data, all external processors are categorized using the following explicit governance statuses:

- **PRODUCTION_APPROVED**: Formally reviewed, contractually signed off (with Canadian data residency and Zero Data Retention agreements), and approved for live production data.
- **GOVERNANCE_APPROVED**: Reviewed and approved by CRBCL leadership; awaiting final production deployment activation.
- **PILOT**: Configured for controlled pilot testing using synthetic or de-identified test data only.
- **TECHNICALLY_CONFIGURED**: Technical credentials or adapters exist in codebase/environment, but operational use with live data is PROHIBITED.
- **DISABLED**: Provider integration is hard-disabled at feature flag and Integration Gateway levels.

---

## 2. External Processor Inventory Matrix

| Processor / Vendor | Service Purpose | Data Categories Handled | Canadian Residency? | Subprocessor Concerns | Credential Protection | Governance Status | Production Blocker? |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Supabase (AWS ca-central-1)** | PostgreSQL Database, Storage & Auth | Client PII/PHI, Cases, Notes, Finance | Yes (Montreal, Canada) | AWS Infrastructure | Environment Variable JWT / Database Password | **GOVERNANCE_APPROVED** | No |
| **Microsoft Graph (M365)** | Calendar Sync & Teams Notifications | Minimized Event Titles ("CRBCL Appointment"), Teams Alerts | Yes (M365 Canada Tenant) | Microsoft Azure | Azure AD App ID & Secret | **PILOT** | Requires CRBCL Tenant Sign-off |
| **Anthropic Claude (Ask Red Bear)** | AI Summarization & Staff Assistance | Sanitized Case Narratives (PII Redacted) | No (US Primary) | Anthropic API | Server-side API Key (`ANTHROPIC_API_KEY`) | **TECHNICALLY_CONFIGURED** | Requires Commercial ZDR Contract |
| **Cloud OCR Engine** | Form & Passport Data Extraction | Document Extractions, Client Names | Yes (Canada Regional) | Cloud Provider | Server-side API Key | **TECHNICALLY_CONFIGURED** | Requires Human Verification |
| **Twilio / SMTP** | SMS & Email Notifications | Phone Numbers, Email, Minimized Notifications | Yes / Enterprise | Telecom Carriers | API Token | **GOVERNANCE_APPROVED** | No |
| **Samsara Telematics** | Fleet Vehicle GPS & Odometer | Vehicle Identifiers, GPS Lat/Lng | Yes (Canada Regional) | Samsara Cloud | API Key | **PILOT** | Requires Driver Privacy Policy Sign-off |
| **Meta / X Social API** | Public Community Outreach | Public Announcement Text (0 Case FKs) | No (Global CDN) | Meta / X | OAuth Client Token | **DISABLED** | Mandatory Disabled for Case Data |

---

## 3. Governance Enforcement Rules

1. **Gateway Enforcement**: All outbound requests pass through `IntegrationGateway`. Direct HTTP calls to third-party APIs from application code or frontend components are strictly forbidden.
2. **Payload Minimization**: External providers must NEVER receive un-sanitized client health numbers, reporter identities, or detailed case narratives.
3. **No Direct SQL**: AI and external tools communicate solely through explicit allowlisted service calls (`app/services/integrations/ai/tools.py`).
