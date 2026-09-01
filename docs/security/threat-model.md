# CRBCL Security Threat Model (STRIDE Methodology)

## 1. STRIDE Analysis Matrix

| Threat Category | Potential Attack Vector | System Impact | Implemented Mitigation / Guard |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Credential theft, session hijacking, OTP brute-force | Unauthorized user identity assumption | Argon2id password hashing, MFA (TOTP), HttpOnly secure cookies, rate limiting (10 req/min). |
| **Tampering** | Parameter tampering, SQL injection, stored XSS, audit record alteration | Data corruption, legal record tampering | SQLAlchemy parameterized queries, audit immutability triggers, React auto-escaping, HTML sanitization. |
| **Repudiation** | User denies performing action (e.g. approving financial payout) | Lack of legal accountability | Cryptographic attestation, immutable `AuditEvent` & `AccessEvent` logging, outbox pattern. |
| **Information Disclosure** | IDOR, Case Restriction bypass, IT Admin privacy breach, AI prompt injection, un-redacted export | Disclosure of sensitive child welfare / medical data | Backend UUID scope checks, `CaseRestriction` authorization filters, IT Admin content redactions, `AiGateway` context filters. |
| **Denial of Service** | Endpoint flooding, heavy report queries, AI token exhaustion | Application unavailability, elevated cloud costs | `EndpointRateLimiter` middleware, query timeout limits, AI daily token caps per user. |
| **Elevation of Privilege** | JWT payload alteration, role manipulation, reporting bypass | Normal user gaining Director/Admin rights | Server-side database permission checks (`user.roles.permissions`), no trust in client-side JWT claims. |

---

## 2. Special Integration & AI Threat Vectors

1. **Prompt Injection & Indirect Injection**: Malicious text embedded in client documents attempting to force AI tools to execute unauthorized queries or bypass redactions.
   - *Mitigation*: Backend tool authorization (`AiGateway.get_authorized_case_ids`) executes *before* AI query execution. Even if prompt guard is bypassed, backend tool boundaries reject unauthorized case access.
2. **Prohibited Decisions**: AI recommending child removal or custody alterations.
   - *Mitigation*: Hardcoded safety checks in `inspect_prompt_safety()` block autonomous legal/custody decisions.
3. **Third-Party Subprocessor Leakage**: Unsanitized PII reaching external APIs.
   - *Mitigation*: `IntegrationGateway` strips names, health numbers, and narratives before payload transmission.
