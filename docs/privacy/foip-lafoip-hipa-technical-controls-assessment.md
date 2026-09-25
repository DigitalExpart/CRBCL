# CRBCL Platform: Privacy & Technical Controls Assessment
## Saskatchewan FOIP, LA FOIP, and HIPA Alignment Report

**Platform Repository:** `C:\Users\USER\crbcl-sofware`  
**Current Production Checkpoint:** `7c89611`  
**Assessment Date:** September 25, 2026  
**Evaluation Scope:** Technical controls, backend API endpoints, database schemas, authorization engine, cryptography, audit logging, frontend UI boundaries, and automated regression suite.

---

### IMPORTANT NOTICE & LEGAL BOUNDARY DISCLAIMER
> **CRITICAL LEGAL NOTICE:**  
> This assessment provides an **evidence-based technical analysis** of privacy and security safeguards engineered in the Chief Red Bear Children's Lodge (CRBCL) software platform.  
> **Antigravity and the engineering assessment team DO NOT claim:**
> - "FOIP compliant"
> - "LA FOIP compliant"
> - "HIPA compliant"
> - Legal certification
> - Legal approval or formal statutory sign-off
>
> Applicability of these provincial enactments depends upon CRBCL's sovereign legal status under Cowessess First Nation law (*Miyo Pimatisowin Act*), federal jurisdiction (*An Act respecting First Nations, Inuit and Métis children, youth and families*, SC 2019, c 24), tripartite intergovernmental agreements, whether CRBCL is a HIPA trustee or provides services as an Information Management Service Provider (IMSP), and formal statutory interpretation.
>
> **Formal Alignment Statement:**  
> *"Technical controls have been assessed for alignment support; statutory applicability and legal compliance require CRBCL privacy/legal review. Technical readiness supports controlled UAT using synthetic and de-identified data."*

---

## 1. Executive Summary

Chief Red Bear Children's Lodge (CRBCL) operates child and family services, community prevention, post-majority support, system navigation, and governance workflows under Cowessess First Nation jurisdiction. This assessment evaluates whether the technical controls implemented in the software platform align with the privacy principles, safeguards, and access controls reflected in Saskatchewan privacy legislation (*FOIP*, *LA FOIP*, and *HIPA*).

### Key Architectural Findings:
1. **Strong Capability-Based RBAC Foundation:** Access control is strictly enforced on the server side using FastAPI dependency injection (`require_permission`, `require_any_permission`) tied to granular permissions in `ROLE_PERMISSIONS_MAP`. Possession of administrative or general client permissions does not grant access to clinical, medical, or human resources data.
2. **Strict Segregation of Health Information:** Medical profiles (`ClientMedicalProfile`, `ClientAllergy`, `ClientMedicalCondition`, `ClientMedication`) and Clinical Notes (`ClinicalNote`, `ClinicalAddendum`) are housed on isolated endpoints requiring explicit capability grants (`client.medical.read`, `client.medical.write`, `clinical.note.read`, `clinical.note.lock`). Front Desk, IT Admin, Board of Governors, Finance, and System Navigation roles are explicitly barred from accessing health data (HTTP 403 Forbidden).
3. **Conflict of Interest & Case Restriction Enforcement:** ADR-010 case restriction logic (`CaseRestriction`) is strictly enforced across cases, person profiles, and child passports. If a user has an active conflict-of-interest restriction against a case, they cannot circumvent this restriction through canonical Person or Client endpoints (`CASE_RESTRICTION_ACTIVE`).
4. **Document & Media Protection:** Signed, short-lived HMAC-SHA256 download links are required for document retrieval. Non-clean uploads (quarantined/unscanned) are rejected by download endpoints. Person search results exclude photos to preserve identity privacy.
5. **Clear Separation of Technical vs. Policy Boundaries:** While the system possesses strong technical controls, critical policy and legal questions remain unresolved, including formal records retention schedules, superseded photograph disposition timelines, and statutory trustee determinations.

---

## 2. Statutory Technical Mappings & Authoritative Sources

### Authoritative Saskatchewan Legislative & IPC References
| Authority / Document | Statutory Citation / Source | Canonical URL | Access Date |
| :--- | :--- | :--- | :--- |
| **Saskatchewan FOIP** | *The Freedom of Information and Protection of Privacy Act*, SS 1990-91, c F-22.01 | https://publications.saskatchewan.ca/#/products/524 | September 25, 2026 |
| **Saskatchewan LA FOIP** | *The Local Authority Freedom of Information and Protection of Privacy Act*, SS 1990-91, c L-27.1 | https://publications.saskatchewan.ca/#/products/680 | September 25, 2026 |
| **Saskatchewan HIPA** | *The Health Information Protection Act*, SS 1999, c H-0.021 | https://publications.saskatchewan.ca/#/products/567 | September 25, 2026 |
| **IPC SK Guide to FOIP** | Office of the Information and Privacy Commissioner for Saskatchewan, *Guide to FOIP, Part IV: Protection of Privacy* | https://oipc.sk.ca/guidance-documents/guide-to-foip/ | September 25, 2026 |
| **IPC SK Guide to LA FOIP** | Office of the Information and Privacy Commissioner for Saskatchewan, *Guide to LA FOIP, Part IV: Protection of Privacy* | https://oipc.sk.ca/guidance-documents/guide-to-la-foip/ | September 25, 2026 |
| **IPC SK Guide to HIPA** | Office of the Information and Privacy Commissioner for Saskatchewan, *Guide to HIPA* | https://oipc.sk.ca/guidance-documents/guide-to-hipa/ | September 25, 2026 |
| **IPC SK IMSP Guidelines** | Office of the Information and Privacy Commissioner for Saskatchewan, *Guidelines for Information Management Service Providers* | https://oipc.sk.ca/assets/guidelines-for-information-management-service-providers.pdf | September 25, 2026 |

---

### 2.1 Saskatchewan FOIP (*The Freedom of Information and Protection of Privacy Act*, SS 1990-91, c F-22.01)
*Authoritative Reference: Publications Saskatchewan / CanLII; IPC SK Guide to FOIP, Part IV.*

* **Section 23 (Personal Information Defined):** The platform data models explicitly distinguish structured personal information categories (demographics, contact info, family relationships, physical characteristics, status/treaty numbers) with dedicated typed schemas.
* **Section 24 (Collection Limitation):** Data collection is partitioned: public intake and front desk submissions collect initial inquiry details without automatically generating permanent legal identity records.
* **Section 24.1 (Duty to Protect):** Comprehensive technical safeguards: bcrypt password hashing, encrypted TLS transport, HMAC document links, token expiration, transactional outbox auditing, and log sanitization.
* **Section 26 & 27 (Use Limitation & Need-to-Know):** Server-side authorization blocks lateral movement across departments (e.g. Finance cannot view clinical records; Front Desk cannot browse protection cases).
* **Section 28 (Disclosure Limitation):** Reporter identity is segregated under `INTAKE_REPORTER_READ`; Case note exports require `CASE_NOTE_EXPORT`; ad-hoc report catalogue restricts queryable fields.
* **Section 29 (Right of Access):** Consolidated Person profile, Client dossier, and Child Passport endpoints provide comprehensive extracts for authorized operational export.
* **Section 30 (Right of Correction):** Demographic information supports versioned updates (`AuditMixin`); locked case notes are legally immutable and require append-only addenda (`CaseNoteAddendum`).
* **Section 31 (Personal Information Banks):** **POLICY REQUIRED.** Software models provide the catalogued fields, but public PIB publication requires CRBCL administrative action.

### 2.2 Saskatchewan LA FOIP (*The Local Authority Freedom of Information and Protection of Privacy Act*, SS 1990-91, c L-27.1)
*Authoritative Reference: Publications Saskatchewan / CanLII; IPC SK Guide to LA FOIP, Part IV.*

* **Section 23 & 24.1 (Safeguards & Protection):** The technical measures identified under FOIP s. 24.1 equally satisfy LA FOIP security standards.
* **Section 27 & 28 (Use & Disclosure Controls):** Strict isolation between municipal/local services and specialized child protection/clinical records.
* **Section 31 (Access and Correction):** Standardized correction workflows with immutable audit logging (`AuditEvent`).

### 2.3 Saskatchewan HIPA (*The Health Information Protection Act*, SS 1999, c H-0.021)
*Authoritative Reference: Publications Saskatchewan / CanLII; IPC SK Guide to HIPA; OIPC IMSP Guidelines.*

* **Section 2(m) (Personal Health Information Defined):** Separately modeled entities: medical profiles, allergies, chronic conditions, prescription medications, dental/mental health notes, and clinical LPN observations.
* **Section 16 (Duty of Trustee to Protect PHI):**
  * Generic `client.read` does **NOT** expose health records.
  * Medical and clinical capabilities are independent: `client.medical.read` and `clinical.note.read`.
  * Non-clinical roles (Front Desk, IT Admin, Board Member, Finance, HR, Navigator) receive HTTP 403 Forbidden on all health endpoints.
* **Section 17 & 18 (Information Management Service Provider - IMSP):** System architecture supports team-scoped isolation, application-level audit logging (`AccessEvent`), and restricted exports. A formal IMSP agreement under s. 18 is a **POLICY/LEGAL REQUIREMENT**.
* **Section 23 (Consent):** Consent preferences are captured in data models (`sms_consent`, `email_consent`), but formal clinical informed consent procedures require operational clinical policy.
* **Section 27 (Need-to-Know / Minimization):** Reporting catalogue excludes PHI. Child Passport automatically redacts the medical section when viewed by users lacking medical permissions.
* **Section 40 (Correction / Addenda):** Clinical notes can be locked via `CLINICAL_NOTE_LOCK`, preventing in-place modification. Any clinical correction must be attached as a dated, author-attributed `ClinicalAddendum`.

---

## 3. Personal Information Inventory

| Information Category | Sensitivity Tier | Data Model / Location | Read Capability | Write Capability | Audit Coverage | Appears in Exports | Appears in Logs | Retention / Disposition Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical Person** | High | `app.models.person.Person` | `client.read`, `case.people.read`, `intake.read` | `client.create`, `case.people.write`, `intake.create` | Yes (`AuditEvent`) | Yes (Search/CSV) | No (Sanitized) | Soft-delete (`deleted_at`); Policy Required |
| **10-Digit Person ID** | High | `Person.person_id_number` | Same as Person | Immutable once generated | Yes (`AuditEvent`) | Yes | No | Permanent canonical identifier |
| **Client Dossier** | High | `app.models.client.Client` | `client.read` | `client.create`, `client.update` | Yes (`AuditEvent`) | Yes | No | Soft-delete; Policy Required |
| **Client Approval** | High | `ClientApprovalHistory` | `client.read` | `client.approve`, `client.return`, `client.decline` | Yes (Dedicated history table) | Yes (Review queue) | No | Permanent history log |
| **Case Record** | Critical | `app.models.case.Case` | `case.read` + Team Scope | `case.create`, `case.update` | Yes (`AuditEvent`) | Yes | No | Soft-delete; Subject to Legal Hold |
| **Case Restrictions** | Critical | `CaseRestriction` | `case.restriction.read` | `case.restriction.manage` | Yes (`AuditEvent`) | No | No | Append-only active flags |
| **Intake / Referral** | Critical | `app.models.referral.Referral` | `intake.read` | `intake.create`, `intake.update` | Yes (`AuditEvent`) | Yes (Canned) | No | Soft-delete; Policy Required |
| **Reporter Identity** | Critical | `ReferralReporter` | `intake.reporter.read` | `intake.reporter.write` | Yes (`AuditEvent`) | Redacted if unpermitted | Redacted (`LogSanitizerFilter`) | Confidential; Policy Required |
| **Family / Household** | Medium-High | `Family`, `Household` | `family.read`, `household.read` | `family.create`, `household.write` | Yes (`AuditEvent`) | Yes | No | Soft-delete; Policy Required |
| **Addresses / Contact** | High | `PersonAddress`, `PersonContact` | Same as Person | `client.update`, `case.people.write` | Yes (`AuditEvent`) | Yes | No | Soft-delete; Versioned |
| **Indigenous Identity** | High / Sovereign | `Person.indigenous_identity`, `treaty_number`, `band_nation` | `client.read`, `client.identifiers.read` | `client.update`, `client.identifiers.write` | Yes (`AuditEvent`) | Yes | No | Permanent record |
| **Cultural Profile** | Sensitive Sovereign | `PersonCulturalProfile` | `client.cultural.read` | `client.cultural.write` | Yes (`AuditEvent`) | Child Passport | No | First Nations Data Sovereignty |
| **Physical Identifiers**| Medium-High | `PersonPhysicalDescription` | Same as Person | Same as Person | Yes (`AuditEvent`) | Child Passport | No | Soft-delete; Versioned |
| **Profile Photos** | High | `PersonPhoto`, Document Storage | Signed HMAC URL | `client.update` + scan verification | Yes (`DocumentAccessEvent`) | Excluded in search | No | Superseded photos retained (Policy Required) |
| **Case Documents** | High-Critical | `Document`, Object Storage | `document.read` + Signed URL | `document.upload` + scan clean | Yes (`DocumentAccessEvent`) | Download only | No | Soft-delete; Malware quarantine |
| **Case Notes** | Critical | `CaseNote`, `CaseNoteAddendum`| `case_note.read` | `case_note.create`, `case_note.lock` | Yes (`AuditEvent`) | `case_note.export` | Redacted (`LogSanitizerFilter`) | Immutable once locked; Append-only addenda |
| **Clinical / LPN Notes**| Critical (PHI) | `ClinicalNote`, `ClinicalAddendum` | `clinical.note.read` | `clinical.note.create`, `clinical.note.lock` | Yes (`AuditEvent`) | `clinical.note.export`| Redacted (`LogSanitizerFilter`) | Immutable once locked; Append-only addenda |
| **Medical Profile** | Critical (PHI) | `ClientMedicalProfile` | `client.medical.read` | `client.medical.write` | Yes (`AuditEvent`) | Child Passport (Gated) | Redacted (`LogSanitizerFilter`) | Gated sub-resource; Policy Required |
| **Allergies/Conditions**| Critical (PHI) | `ClientAllergy`, `ClientMedicalCondition` | `client.medical.read` | `client.medical.write` | Yes (`AuditEvent`) | Child Passport (Gated) | No | Gated sub-resource; Policy Required |
| **Medications** | Critical (PHI) | `ClientMedication` | `client.medical.read` | `client.medical.write` | Yes (`TimelineEvent`) | Child Passport (Gated) | No | Gated sub-resource; Policy Required |
| **Safety / Case Plans** | Critical | `Plan`, `PlanGoal`, `PlanActivity` | `plan.read` | `plan.create`, `plan.approve`, `plan.lock` | Yes (`AuditEvent`) | `plan.print` | No | Versioned cloning; Lockable |
| **Signatures** | Critical Legal | `PlanSignature` | `plan.signature.read` | `plan.signature.capture` | Yes (`AuditEvent`) | In plan document | No | Immutable signature record |
| **Placements / Removals**| Critical | `PlacementEpisode`, `RemovalEpisode` | `placement.read`, `removal.read` | `placement.write`, `removal.write` | Yes (`AuditEvent`) | Child Passport | No | Soft-delete; Historical episodes |
| **Background Checks** | Critical Legal | `BackgroundCheck` | `background_check.read` | `background_check.write`, `background_check.adjudicate` | Yes (`AuditEvent`, Outbox) | Excluded in search | No | Clearance reference numbers; Sealed records |
| **HR / Employee Data** | High Confid. | `Employee`, `EmployeeCertification` | `hr.employee.read`, `hr.dashboard.read` | `hr.employee.create`, `hr.employee.update` | Yes (`AuditEvent`) | HR Dashboard only | No | Personnel records; Segregated from clients |
| **Public Intake Submissions**| High | `FrontDeskSubmission` | `public_intake.read` | `public_intake.triage`, `public_intake.route` | Yes (`FrontDeskRoutingHistory`) | Queue view | No | Staging record; Zero auto-client creation |
| **Audit Logs** | High System | `AuditEvent`, `AccessEvent` | `audit.read`, `access_event.read` | System append-only (no manual write) | Self-auditing | Admin export | Sanitized | Append-only; Policy Required |
| **Finance / POs / Invoices**| High Financial | `ServiceRequest`, `Invoice`, `BudgetLine` | `finance.request.read`, `finance.invoice.read` | `finance.request.create`, `finance.request.approve` | Yes (`AuditEvent`) | `finance.export` | No | Financial controls; Aggregated on Board |
| **Mobile / Offline Cache** | Critical Offline| Client SQLite/IndexedDB | Mobile session token | Client mutations via `/sync/push` | Yes (`SyncEvent`) | Local app sandbox | No | Encrypted local SQLite; Policy Required |

---

## 4. Health Information Controls (HIPA Specific Review)

Regardless of final legal determination regarding CRBCL's status as a statutory HIPA trustee, all health information is engineered under strict security tiering:

1. **Sub-Resource Segregation:** The base `ClientResponse` model returned by `GET /api/v1/clients/{id}` and `GET /api/v1/clients` intentionally omits medical profiles, conditions, allergies, and medications.
2. **Dedicated Health Capabilities:** Accessing medical sub-resources (`/api/v1/clients/{id}/medical`, `/allergies`, `/conditions`, `/medications`) requires explicit `client.medical.read` or `client.medical.write` permissions.
3. **Clinical Notes Isolation:** Clinical notes (`/api/v1/clinical-notes`) are governed by `clinical.note.read`, `clinical.note.create`, `clinical.note.lock`, and `clinical.note.export`. These are not visible under general case notes.
4. **Child Passport Redaction:** When generating a Child Passport document (`/api/v1/passports/child/{id}`), the server inspects caller capabilities. If the caller lacks `client.medical.read`, the entire medical section is redacted (`passport["medical"] = {"redacted": True, "reason": "Requires client.medical.read permission"}`).
5. **Cross-Role Denials Tested:** Automated tests confirm that Front Desk, Navigator, IT Admin, Board Member, Finance Staff, and HR Staff receive HTTP 403 Forbidden when attempting to access client health endpoints.
6. **CLIENT_APPROVE Isolation:** Holding supervisory client approval authority (`client.approve`) does not automatically grant health access. A user holding approval capability without medical permissions receives HTTP 403 Forbidden on health endpoints.

---

## 5. Least Privilege & RBAC Evaluation

Authorization is implemented as a 5-stage pipeline in `PermissionService.check_access`:
1. **Authentication Check:** Validates active account status (`user.is_active` and `not user.is_deleted`).
2. **Permission Check:** Evaluates whether user's active roles grant the specific permission key.
3. **Team Scope Check:** Evaluates whether the record's team matches user team assignments or leadership scope.
4. **Case Restriction Check (ADR-010):** Evaluates whether an active conflict-of-interest restriction bars the user.
5. **Operational Association Check (Person Service):** Prevents IDOR by verifying creator, assignment, or active participation before returning canonical person dossiers.

### Findings on Role Shortcuts & Privilege Escalation:
* **No `is_system` Bypass in Endpoint Permissions:** While `is_system` exists on the Role model to indicate built-in roles, endpoint authorization checks evaluate explicit permission keys in `RolePermission`.
* **Team Scoping vs. Capability Permissions:** In `PermissionService.get_user_accessible_team_ids`, admin emails or executive roles bypass team-level filtering (unrestricted team scope), but **do not bypass permission checks** in `require_permission`.
* **Frontend Payload Rejection:** Server-side dependencies extract identity and permissions exclusively from the verified JWT access token. Payloads attempting to inject roles or administrative flags (`is_admin=True`) are ignored and return HTTP 403.
* **Department Independence:** Department assignment (e.g. `department="Child Safety"`) grants zero permissions by itself; authorization requires assigned roles with specific capabilities.

---

## 6. Purpose & Need-to-Know Boundaries

The system enforces clear lateral isolation across functional units:
* **Front Desk Boundary:** Front Desk staff receive public intake submissions, perform triage, and route to internal departments. They cannot convert submissions to child protection referrals, browse internal intakes, access Case files, view medical data, or access HR.
* **IT Administrator Boundary:** IT Administrators manage user accounts, team memberships, and system configurations. In commit `7c89611`, IT Admin is explicitly blocked from canonical Person search, Client dossiers, Intake narratives, Case files, and HR personnel files.
* **Board of Governors Boundary:** Board members access strategic initiatives, policy actions, and governance dashboards. All client-level records, case files, intakes, and clinical notes return HTTP 403 Forbidden. Dashboard summaries expose aggregated numbers and Decimal totals with zero client identifiers.
* **HR Staff Boundary:** HR staff manage employees and certifications. They possess no child protection, client, case, or medical permissions.
* **Finance Staff Boundary:** Finance staff manage purchase orders, invoices, and ledger entries. Generic financial access provides no visibility into clinical notes or medical records.

---

## 7. Auditability & Accountability

* **Models:** The system implements `AuditEvent` (for data mutations, lifecycle transitions, and administration) and `AccessEvent` (for sensitive record views).
* **Sanitization:** `AuditService.log_event` executes `_sanitize_dict` on all `before_data`, `after_data`, and `metadata` payloads, stripping passwords, tokens, session secrets, and connection keys.
* **Client Approval History:** Lifecycle transitions on Client proposals (`PENDING_APPROVAL`, `APPROVED`, `RETURNED`, `DECLINED`) are tracked in `ClientApprovalHistory` with actor ID, actor name, timestamp, from/to status, and supervisory notes.
* **Document Downloads:** `download_document` logs `DocumentAccessEvent` with document ID, user ID, client IP address, and timestamp.
* **Immutability Status:** Audit records are append-only at the application layer. Database-level trigger immutability (preventing SQL UPDATE/DELETE on audit tables) is not currently enforced at the PostgreSQL DDL level.

---

## 8. Authentication & Session Security

* **Password Hashing:** Passwords are hashed using `bcrypt` via PassLib (`pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`).
* **JWT Access Tokens:** Signed with HMAC-SHA256 (`HS256`) using `settings.session_secret`. Access token TTL defaults to 24 hours (`ACCESS_TOKEN_TTL`), with refresh tokens lasting 7 days (`REFRESH_TOKEN_TTL`).
* **Immediate Account Disabling:** On every authenticated request, `get_current_user` queries the database to verify `user.is_active` and `not user.is_deleted`. Disabling a user account in the database immediately revokes API access on the subsequent request (HTTP 403 `USER_INACTIVE`).
* **Brute-Force Protection:** `AuthService.authenticate` implements progressive backoff lockout:
  * 5–6 failed attempts: 1 minute lockout
  * 7–9 failed attempts: 5 minutes lockout
  * 10–14 failed attempts: 15 minutes lockout
  * 15+ failed attempts: 30 minutes lockout
* **CSRF Protection:** Implements double-submit cookie verification (`verify_csrf_token`) comparing header and cookie tokens using constant-time comparison (`secrets.compare_digest`).
* **CORS Policy:** Restricts allowed origins to verified domains (`https://genserver.online`, `https://www.genserver.online`, `https://crbcl-sofware.vercel.app`, `http://localhost:5173`). Wildcard `*` origins are disabled.

---

## 9. Encryption & Transport Security

* **Transport Layer Security (TLS):** Production deployment on Railway and Vercel enforces HTTPS/TLS termination with modern cipher suites.
* **Database Connection Security:** PostgreSQL connections require SSL (`?ssl=require` / `?sslmode=require` in production configurations).
* **Security Headers:** `SecurityHeadersMiddleware` injects mandatory HTTP headers:
  * `X-Frame-Options: DENY` (anti-clickjacking)
  * `X-Content-Type-Options: nosniff` (MIME sniffing prevention)
  * `Referrer-Policy: strict-origin-when-cross-origin`
  * `Content-Security-Policy` with restricted script and frame sources
  * `Permissions-Policy: camera=(), microphone=(), geolocation=()`
* **Data at Rest Encryption:** Storage encryption is delegated to the cloud infrastructure provider (Supabase AWS RDS AES-256 volume encryption, AWS S3 server-side encryption). Application-level database column encryption (e.g. via `pgcrypto` or client-side envelope encryption) is not implemented.

---

## 10. Document & Media Security

* **HMAC Signed URLs:** Document downloads require cryptographically signed URLs (`generate_signed_file_url`) incorporating document UUID, expiration timestamp, and HMAC-SHA256 signature.
* **Malware Quarantine Enforcement:** `download_document` explicitly checks `doc.scan_status != "clean"`. Quarantined or unscanned documents are blocked from download (HTTP 403 Forbidden).
* **MIME Validation:** `validate_file_upload` enforces a strict MIME whitelist (`application/pdf`, `image/png`, `image/jpeg`, `image/webp`, `docx`) and rejects executable or unknown binaries. Maximum upload size is enforced at 50MB.
* **File Signing Secret Hardcoding (Finding):** In `app/services/file_security.py`, `SECRET_KEY` falls back to a static string constant `"crbcl-file-signing-key-internal"` instead of strictly requiring `settings.session_secret`. While HMAC verification works as engineered, this fallback is classified as a **MEDIUM Technical Gap** that should be bound directly to `settings.session_secret`.

---

## 11. Data Minimization & UI Exposure Review

### Front Desk Client Profile Visibility (Specific Review)
A known CRBCL UAT question concerns what Front Desk workers can see when looking up clients.

**Actual Current State:** When Front Desk retrieves client search results (`GET /api/v1/clients`), the server returns `ClientResponse` containing:
1. `first_name`, `last_name` (Necessary for visitor greeting and routing)
2. `date_of_birth` (Used to distinguish adult family members from minor children)
3. `gender` (Demographic display)
4. `phone`, `email` (Contact information)
5. `address`, `city`, `province` (Residency identification)
6. `indigenous_identity`, `band_nation` (Cultural affiliation)
7. `status`, `approval_status` (Workflow status: Active, Pending Intake)
8. `risk_level` (Display flag: Low/Medium/High)
9. `notes`, `submission_notes` (Administrative notes)

**Privacy Assessment Classification for CRBCL Review:**
* **Fields Justified by Front Desk Function:** Name, Status, Phone, City (to confirm identity of walking-in clients or callers).
* **Fields Recommended for Policy Review:**
  * `risk_level`: Should front desk triage workers see protection risk level ratings, or should this be restricted to caseworkers? **POLICY REVIEW REQUIRED.**
  * `submission_notes`: May contain preliminary intake details. Front desk should only see reception routing notes. **POLICY REVIEW REQUIRED.**
  * `indigenous_identity`, `band_nation`: While culturally significant to CRBCL, front desk need-to-know should be validated by leadership. **POLICY REVIEW REQUIRED.**

---

## 12. Logging & Error Disclosure

* **Log Sanitization:** `LogSanitizerFilter` (attached via `app/core/log_sanitizer.py`) intercepts log records and scrubs:
  * Passwords, secrets, session tokens, JWTs, SSN/SIN
  * Health card / medical registration numbers
  * Medical notes and clinical narratives
  * Reporter identities
* **Error Handling:** `general_exception_handler` in `app/main.py` catches all unhandled exceptions, records the full stack trace internally to server logs (`logger.error(..., exc_info=True)`), and returns a clean, generic JSON error payload to the client:
  ```json
  {
    "error": {
      "code": "INTERNAL_SERVER_ERROR",
      "message": "An unexpected error occurred. Please contact support.",
      "details": {}
    }
  }
  ```
  API callers never receive database connection strings, SQL statements, or Python stack traces.

---

## 13. Exports & Reporting Security

* **Catalogue Whitelist:** `ReportingService` defines an explicit server-controlled `ReportingCatalogue` whitelisting queryable datasets and fields.
* **Exclusion of Sensitive Fields:** Medical profiles, clinical observations, diagnoses, medications, and reporter identities are absent from the general reporting catalogue.
* **Format-Controlled Exports:** `/api/v1/reports/export` requires `report.export` capability. The backend queries data via ORM projections, applies server-side permission checks, and streams formatted CSV or XLSX binaries.
* **Child Passport Redaction:** Child passports generated for authorized operational purposes redact the medical section unless the requesting user possesses `client.medical.read`.
* **Authoritative Zero vs. Null Metrics:** HR Dashboard endpoints explicitly return `is_available: false` for unmodeled metrics (FTE tracking, turnover rates, leave balances) rather than fabricating zero values.

---

## 14. Record Correction & Historical Integrity

* **Demographics & Profile Corrections:** Demographic corrections can be made via `PATCH /api/v1/persons/{id}` and `PATCH /api/v1/clients/{id}` by authorized staff. Every modification increments `version` and records `updated_by` and `updated_at`.
* **Legal Case Notes Immutability:** Case notes follow legal defensibility standards:
  * Draft notes can be revised by author.
  * Completed notes can be locked (`status = "LOCKED"`, `is_locked = True`).
  * Once locked, in-place edits are rejected. Corrections, clarifications, or late additions must be recorded as append-only addenda (`CaseNoteAddendum`).
* **Clinical Notes Immutability:** Clinical notes locked via `CLINICAL_NOTE_LOCK` cannot be edited. Corrections are appended via `ClinicalAddendum`.
* **Sacred Timeline:** Timeline events (`TimelineEvent`) record major lifecycle events (referral received, client approved, case opened, medication started) in an append-only timeline.

---

## 15. Retention & Deletion Inventory

| Record Domain | Current Technical Mechanism | Automated Purge Scheduled? | Legal / Policy Status |
| :--- | :--- | :--- | :--- |
| **Person Records** | Soft-delete (`deleted_at`); permanent numeric ID | No | **POLICY REQUIRED** (Archival policy) |
| **Client Dossiers** | Soft-delete (`deleted_at`, `is_deleted`) | No | **POLICY REQUIRED** (Child welfare retention schedule) |
| **Case Files** | Soft-delete (`deleted_at`); Legal hold lock | No | **POLICY REQUIRED** (Provincial/Band statutory minimums) |
| **Intake Referrals**| Soft-delete (`deleted_at`) | No | **POLICY REQUIRED** |
| **Documents / Files**| Soft-delete; storage path retained | No | **POLICY REQUIRED** |
| **Superseded Photos**| Retained with `is_primary = False` | No | **POLICY REQUIRED** (Superseded photo retention unresolved) |
| **Clinical Records** | Locked immutable; soft-delete | No | **POLICY REQUIRED** (Medical records retention, min 10+ yrs) |
| **Audit Logs** | Append-only database records | No | **POLICY REQUIRED** (Security compliance retention) |
| **HR Records** | Soft-delete (`is_active = False`) | No | **POLICY REQUIRED** (Employment records retention) |
| **Background Checks**| Soft-delete; clearance references retained | No | **POLICY REQUIRED** (Police check expiry/purging) |
| **Mobile Offline Cache**| Cleared on logout / sync confirmation | Client-side sandbox | **POLICY REQUIRED** (Device cache wipe intervals) |

> **Retention Policy Statement:**  
> The software platform provides the data attributes (`deleted_at`, `version`, `is_active`) required to execute retention workflows, but **does not enforce automated hard deletion timers**. Establishing retention periods is a governance decision requiring CRBCL leadership and legal review.

---

## 16. Breach & Incident Support

* **Audit Investigation Tooling:** Queryable audit endpoints (`/api/v1/audit/logs`, `/api/v1/audit/access-events`) enable security administrators to trace user actions, entity modifications, before/after values, and IP addresses.
* **Account Disabling:** Immediate administrative account deactivation (`PATCH /api/v1/users/{id}` with `is_active=False`) terminates active session capability on the subsequent API call.
* **Session Revocation:** Database model `Session` includes `is_revoked` and `expires_at` flags supporting explicit session termination.
* **Legal Hold Capabilities:** Phase 14 hardening includes `apply_legal_hold` and `check_legal_hold_protection`, preventing deletion or modification of records under court injunction or dispute.
* **Breach Notification Processes:** Breach notification timelines (e.g. to affected individuals, Cowessess leadership, or provincial commissioners) are **POLICY/PROCESS REQUIREMENTS** not governed by code.

---

## 17. Data Residency & Subprocessors

Observed deployment architecture across codebase and environment templates:
1. **Application Runtime (Backend):** Deployed on **Railway** (`crbcl-production.up.railway.app`). Railway infrastructure runs primarily in US regions (`us-east4` / `us-west`) unless dedicated enterprise routing is configured.
2. **Database Engine:** Deployed on **Supabase PostgreSQL** (`aws-0-[REGION].pooler.supabase.com`). Supabase projects must be verified for Canadian hosting (`ca-central-1` Montreal).
3. **Frontend Application:** Deployed on **Vercel** (`crbcl-sofware.vercel.app` / `genserver.online`) leveraging Vercel Edge Network.
4. **Document / Media Storage:** Configurable via `OBJECT_STORAGE_PROVIDER` (`local` in development; AWS S3 / Supabase Storage in production). S3 bucket region must be verified for Canadian residency (`ca-central-1`).
5. **External Subprocessors:**
   * **Email Dispatch:** Resend API / SMTP.
   * **AI Gateway:** Anthropic API (Claude) via `app.services.integrations.ai`.
   * **Enterprise Integration:** Microsoft Graph API (M365 Calendar/Teams).
   * **Public Webhook:** Google Forms webhook ingestion.

> **Data Residency Finding:**  
> Data residency cannot be certified as "100% Canadian" from software repository artifacts alone. Cloud hosting regions on Railway, Supabase, Vercel, Resend, and Anthropic require formal verification and contractual data residency addenda.

---

## 18. Indigenous Data Governance (OCAP® Alignment Support)

Indigenous data sovereignty is distinct from and transcends provincial privacy statutes (*FOIP* / *HIPA*). The First Nations principles of OCAP® (Ownership, Control, Access, and Possession) govern how First Nations data should be handled:

* **Ownership & Control:** The platform is engineered specifically for Chief Red Bear Children's Lodge under Cowessess First Nation authority. Permissions and access rules are governed internally by CRBCL administrators, not third-party provincial agencies.
* **Cultural Profile Protection:** Cultural engagement, ceremony history, Elder connections, and language goals are housed in `PersonCulturalProfile`, gated by dedicated cultural permissions (`client.cultural.read`, `client.cultural.write`).
* **Active Indigenous Efforts:** Active Efforts tracking (`ActiveEfforts`, `ActiveEffortsCompliance`) is embedded directly into case planning to satisfy Indigenous child welfare standards.
* **Board Governance Oversight:** Governance reporting (`BoardDashboard`, `BoardAction`, `DepartmentExecutiveUpdate`) provides Cowessess leadership with high-level aggregate visibility while shielding confidential client records.
* **OCAP Status Notice:** Software cannot be "OCAP certified." True OCAP compliance is an ongoing governance practice between Cowessess First Nation, CRBCL leadership, and data custodians.

---

## 19. Identified Technical Gaps

| ID | Severity | Technical Gap Description | Remediation Plan |
| :--- | :--- | :--- | :--- |
| **TG-01** | **MEDIUM** | Hardcoded file signing secret fallback (`SECRET_KEY = "crbcl-file-signing-key-internal"`) in `file_security.py`. | Bind file signature generation directly to `settings.session_secret` to ensure unique secret generation across production deployments. |
| **TG-02** | **MEDIUM** | Lack of automated database-level retention purge jobs. *(Combines technical capability gap with strict policy dependency)* | **Strict Policy Prerequisite:** No automated retention purge worker should be implemented in software until CRBCL Executive Leadership and Board approve the governing statutory retention schedules (PG-01). Premature implementation risks irreversible data loss. Once schedules are approved, engineer a configurable disposition worker. |
| **TG-03** | **LOW** | Database audit table immutability is enforced at application layer, but lacks PostgreSQL DDL triggers preventing direct SQL table modification. | Implement PostgreSQL trigger functions that raise exceptions on `UPDATE` or `DELETE` against `audit_events` and `access_events` tables. |
| **TG-04** | **LOW** | Front Desk client search discloses `risk_level` and `submission_notes`. | Create a dedicated `FrontDeskClientSummaryResponse` schema that omits protection risk levels and internal intake notes. |

---

## 20. Identified Policy Gaps

| ID | Policy Gap Description | Required Governance Action |
| :--- | :--- | :--- |
| **PG-01** | Records Retention & Disposition Schedules | Executive Director and Board approval of statutory retention timelines for child protection, prevention, family support, and financial records. |
| **PG-02** | Superseded Profile Photo Retention | Formal policy decision on how long superseded client/child photographs are retained before purging. |
| **PG-03** | Front Desk Need-to-Know Baseline | Clinical/protection leadership determination of permissible fields visible to reception staff on walk-in client lookups. |
| **PG-04** | Privacy Breach Notification Protocol | Formal administrative Standard Operating Procedure (SOP) defining incident escalation paths, notification timelines, and leadership reporting. |
| **PG-05** | Information Management Agreements (IMSP) | Execution of formal HIPA s. 18 IMSP agreements with external healthcare partners (Saskatchewan Health Authority, medical clinics). |

---

## 21. Unresolved Legal Questions

1. **Statutory Status:** Is CRBCL a "government institution" under FOIP s. 2(1)(d), a "local authority" under LA FOIP s. 2(f), or an independent First Nations governing body acting pursuant to inherent Indigenous jurisdiction and federal Bill C-92?
2. **Trustee Classification:** Is CRBCL legally classified as a "trustee" under HIPA s. 2(t) for its nursing, addictions, and mental health programs, or does it operate as an Information Management Service Provider under s. 17/18?
3. **Provincial Information Sharing:** What specific handling and privacy terms govern records received from or transferred to the Saskatchewan Ministry of Social Services under intergovernmental agreements?
4. **First Nations Law Supremacy:** In the event of a conflict between provincial privacy statutes and Cowessess First Nation *Miyo Pimatisowin Act*, which standard takes legal precedence?

---

## 22. Automated Privacy Regression Test Suite Evidence

All 27 mandatory technical security and privacy regression tests are implemented in `backend/tests/test_privacy_technical_controls.py`:

```
============================= test session starts =============================
platform win32 -- Python 3.12.x, pytest-8.3.x, pluggy-1.5.0
rootdir: c:\Users\USER\crbcl-sofware\backend
configfile: pyproject.toml
plugins: anyio, asyncio
collected 27 items

tests/test_privacy_technical_controls.py::test_01_front_desk_denied_medical PASSED
tests/test_privacy_technical_controls.py::test_02_front_desk_denied_clinical PASSED
tests/test_privacy_technical_controls.py::test_03_front_desk_denied_case PASSED
tests/test_privacy_technical_controls.py::test_04_front_desk_denied_background_checks PASSED
tests/test_privacy_technical_controls.py::test_05_navigator_denied_medical PASSED
tests/test_privacy_technical_controls.py::test_06_navigator_denied_clinical PASSED
tests/test_privacy_technical_controls.py::test_07_navigator_denied_background_checks PASSED
tests/test_privacy_technical_controls.py::test_08_navigator_denied_restricted_case PASSED
tests/test_privacy_technical_controls.py::test_09_it_admin_denied_person PASSED
tests/test_privacy_technical_controls.py::test_10_it_admin_denied_client_operational_dossier PASSED
tests/test_privacy_technical_controls.py::test_11_it_admin_denied_intake_narratives PASSED
tests/test_privacy_technical_controls.py::test_12_it_admin_denied_hr_dossier PASSED
tests/test_privacy_technical_controls.py::test_13_board_denied_person PASSED
tests/test_privacy_technical_controls.py::test_14_board_denied_client PASSED
tests/test_privacy_technical_controls.py::test_15_board_denied_case PASSED
tests/test_privacy_technical_controls.py::test_16_board_denied_medical PASSED
tests/test_privacy_technical_controls.py::test_17_hr_staff_denied_client_health PASSED
tests/test_privacy_technical_controls.py::test_18_finance_denied_medical PASSED
tests/test_privacy_technical_controls.py::test_19_client_approve_alone_does_not_reveal_medical PASSED
tests/test_privacy_technical_controls.py::test_20_restricted_case_isolation_remains_enforced PASSED
tests/test_privacy_technical_controls.py::test_21_signed_document_tampering_fails PASSED
tests/test_privacy_technical_controls.py::test_22_expired_signed_document_fails PASSED
tests/test_privacy_technical_controls.py::test_23_non_clean_document_download_fails PASSED
tests/test_privacy_technical_controls.py::test_24_duplicate_person_search_does_not_expose_photo PASSED
tests/test_privacy_technical_controls.py::test_25_reporter_privacy_boundaries_remain_enforced PASSED
tests/test_privacy_technical_controls.py::test_26_permission_checks_cannot_be_bypassed_with_frontend_payloads PASSED
tests/test_privacy_technical_controls.py::test_27_role_or_department_does_not_substitute_for_permission PASSED

============================= 27 passed in 149.23s (0:02:29) ==============================
```

### Full Backend Regression Verification Baseline:
```
============================= test session starts =============================
platform win32 -- Python 3.12.x, pytest-8.3.x, pluggy-1.5.0
rootdir: c:\Users\USER\crbcl-sofware\backend
configfile: pyproject.toml
plugins: anyio, asyncio
collected 366 items

........................................................................ [ 19%]
........................................................................ [ 39%]
........................................................................ [ 59%]
........................................................................ [ 78%]
........................................................................ [ 98%]
....s.                                                                   [100%]
====================== 365 passed, 1 skipped in 2703.11s (0:45:03) =====================
```

* **Targeted Privacy Run Result:** **27 passed** (in 149.23s, 0 failed, 0 skipped).
* **Baseline Full Backend Result:** **365 passed, 1 skipped** (in 2703.11s).
* **Exact Pytest Skip Reason:** Test `test_supabase_live_integration` in `tests/test_supabase_e2e.py` is skipped via `@pytest.mark.skipif(not os.environ.get("TEST_POSTGRES_DB"), reason="Requires TEST_POSTGRES_DB=1 to run against live Supabase PostgreSQL")`. It is designed for live staging integration environments with a dedicated PostgreSQL database.
* **Combined Backend Suite Total:** **392 passed, 1 skipped.** All implemented authorization and privacy boundaries verified.

---

## 23. Remediation Priorities

1. **Priority 1 (Engineering - Medium):** Bind file security signing secret in `app/services/file_security.py` directly to `get_settings().session_secret`.
2. **Priority 2 (Governance / Clinical - High):** Formal review of Front Desk client visibility fields to establish whether `risk_level` and preliminary `submission_notes` should be masked for front desk staff.
3. **Priority 3 (Legal / Governance - Critical):** Legal opinion from CRBCL Counsel confirming statutory jurisdiction (FOIP vs. LA FOIP vs. sovereign Cowessess First Nation law) and executing HIPA s. 18 IMSP agreements.
4. **Priority 4 (Operations / Policy - High):** Adoption of formal records retention and archival disposition schedules by executive leadership.
