# CRBCL Platform: Statutory Privacy & Technical Controls Assessment Matrix
## Saskatchewan FOIP, LA FOIP, and HIPA Alignment Analysis

**Repository:** `C:\Users\USER\crbcl-sofware`  
**Production Checkpoint:** `7c89611`  
**Assessment Date:** September 25, 2026  
**Authoritative References:**
- *The Freedom of Information and Protection of Privacy Act* (FOIP), SS 1990-91, c F-22.01 [Publications Saskatchewan / CanLII, accessed Sept 25, 2026]
- *The Local Authority Freedom of Information and Protection of Privacy Act* (LA FOIP), SS 1990-91, c L-27.1 [Publications Saskatchewan / CanLII, accessed Sept 25, 2026]
- *The Health Information Protection Act* (HIPA), SS 1999, c H-0.021 [Publications Saskatchewan / CanLII, accessed Sept 25, 2026]
- Office of the Information and Privacy Commissioner of Saskatchewan (IPC Saskatchewan / OIPC): Resource Guides to FOIP, LA FOIP, HIPA, and Information Management Service Providers (IMSPs) [IPC SK, accessed Sept 25, 2026]

---

### Important Legal & Policy Notice
> **DISCLAIMER:**  
> This document provides an **evidence-based technical and architecture assessment** of software safeguards implemented within the Chief Red Bear Children's Lodge (CRBCL) case management platform.  
> **Antigravity and the engineering assessment team DO NOT claim:**
> - "FOIP compliant"
> - "LA FOIP compliant"
> - "HIPA compliant"
> - Legal certification or statutory approval
>
> Applicability of these provincial statutes depends on CRBCL's legal status, inherent Cowessess First Nation sovereignty, federal jurisdiction (*An Act respecting First Nations, Inuit and Métis children, youth and families*, SC 2019, c 24 / Bill C-92), tri-partite agreements, and whether CRBCL acts as a HIPA trustee or an Information Management Service Provider (IMSP). All legal interpretations and compliance determinations require formal review by CRBCL Legal Counsel and Privacy Officer.
>
> **Technical readiness statement:** *Technical controls have been assessed for alignment support; statutory applicability and legal compliance require CRBCL privacy/legal review. Technical readiness supports controlled UAT using synthetic and de-identified data.*

---

## 1. Classification Methodology

Each legislative provision is classified under one of five authoritative ratings:
1. **TECHNICAL CONTROL AVAILABLE:** Implemented in code, enforced by server-side business logic / database schemas, and validated by automated tests.
2. **PARTIALLY AVAILABLE:** Baseline technical mechanism exists in software, but configuration, secondary endpoints, or full end-to-end tooling requires extension.
3. **TECHNICAL GAP:** Technical safeguard is not yet engineered in software and requires engineering development.
4. **POLICY/PROCESS REQUIRED:** Control cannot be satisfied by software alone and requires CRBCL governance rules, staff SOPs, operational procedures, or institutional schedules.
5. **LEGAL APPLICABILITY REQUIRES CRBCL COUNSEL/PRIVACY OFFICER:** Unresolved statutory threshold questions regarding whether the enactment applies directly, by agreement, or is superseded by First Nations law.

---

## 2. Legal / Policy Boundary & Unresolved Questions

| Jurisdictional Domain | Unresolved Legal / Policy Question | Governance / Legal Action Required |
| :--- | :--- | :--- |
| **FOIP Status** | Is CRBCL itself a "government institution" under FOIP s. 2(1)(d)? | Formal opinion by CRBCL Counsel regarding Crown agency vs. independent Indigenous authority under Cowessess law. |
| **LA FOIP Status** | Is CRBCL a "local authority" under LA FOIP s. 2(f)? | Determination of whether First Nations child and family service entities fall within local authority definitions. |
| **HIPA Trustee Status** | Is CRBCL a "trustee" under HIPA s. 2(t) for health clinics, LPN nursing, mental health, or addictions services? | Legal analysis of CRBCL clinical services, operating licenses, and direct healthcare provision. |
| **IMSP Relationship** | Does CRBCL act as an Information Management Service Provider (IMSP) under HIPA s. 17/18 to external trustees (e.g. SHA, physicians)? | Audit of inter-agency data sharing agreements and execution of formal HIPA s. 18 IMSP agreements. |
| **Indigenous Law Jurisdiction** | Which records are governed primarily by Cowessess First Nation *Miyo Pimatisowin Act* and Indigenous data sovereignty? | Band Council Resolutions (BCRs) and leadership policy establishing sovereign data governance boundaries. |
| **Provincial Transfer Records** | Which records are received under provincial child welfare agreements with SK Ministry of Social Services? | Information-sharing agreement review to establish handling standards for provincial legacy files. |
| **Retention Schedules** | What statutory retention, archiving, and disposition schedules apply to child protection vs. prevention records? | Executive/Board approval of formal records retention schedule (e.g. permanent child welfare archiving vs. ephemeral operational logs). **Policy Dependency:** Software retention purge workers must NOT be implemented until governing schedules are approved, preventing accidental data loss. |

---

## 3. Statutory Technical Alignment Matrix

### A. Saskatchewan FOIP (SS 1990-91, c F-22.01)

| FOIP Section | Legislative Requirement | Technical Assessment Classification | Actual Platform Implementation & Evidence |
| :--- | :--- | :--- | :--- |
| **s. 23** | Definition of Personal Information (PI) | **TECHNICAL CONTROL AVAILABLE** | Data dictionary in SQLAlchemy models explicitly defines Person, Client, Family, Contact, Address, Indigenous identity, and demographic fields. |
| **s. 24** | Collection limited to purpose | **PARTIALLY AVAILABLE** | Intake schemas and Client schemas collect structured fields. Front Desk triage separates initial inquiries from canonical case intake. Policy must define approved operational collection scope. |
| **s. 24.1** | Duty to Protect (Reasonable technical, administrative, physical safeguards) | **TECHNICAL CONTROL AVAILABLE** | Comprehensive 5-stage authorization (`PermissionService.check_access`), bcrypt password hashing, encrypted TLS transport, signed HMAC document URLs, outbox auditing, and log sanitization. |
| **s. 26** | Purpose of collection / Use limitation | **TECHNICAL CONTROL AVAILABLE** | Capability-based RBAC (`ROLE_PERMISSIONS_MAP`) segregates roles (Front Desk cannot browse Cases; IT Admin cannot browse Client or HR dossiers; Board has aggregate view only). |
| **s. 27** | Permitted Use of PI | **TECHNICAL CONTROL AVAILABLE** | Team scoping (`UserTeamAccess`, `TeamMembership`) and Case restriction guards (`CaseRestriction`) prevent unauthorized cross-team access or conflicts of interest. |
| **s. 28** | Disclosure limitations | **TECHNICAL CONTROL AVAILABLE** | Reporter identity protected via `INTAKE_REPORTER_READ`; Case notes exports require `CASE_NOTE_EXPORT`; Ad-hoc report catalogue strictly whitelists non-sensitive fields. |
| **s. 29** | Individual's right of access | **TECHNICAL CONTROL AVAILABLE** | Client Dossier, Child Passport (`/api/v1/passports/child/{id}`), and Person profile endpoints consolidate records for authorized operational export. |
| **s. 30** | Right of correction | **TECHNICAL CONTROL AVAILABLE** | Demographic update endpoints (`PATCH /api/v1/persons/{id}`, `PATCH /api/v1/clients/{id}`). Locked case notes preserve history and require append-only addenda (`CaseNoteAddendum`). |
| **s. 31** | Personal information banks | **POLICY/PROCESS REQUIRED** | Requires CRBCL Privacy Officer to publish a public directory of Personal Information Banks (PIBs). Software models provide the foundational inventory. |

---

### B. Saskatchewan LA FOIP (SS 1990-91, c L-27.1)

| LA FOIP Section | Legislative Requirement | Technical Assessment Classification | Actual Platform Implementation & Evidence |
| :--- | :--- | :--- | :--- |
| **s. 23** | Definition of Personal Information | **TECHNICAL CONTROL AVAILABLE** | Structured Person/Client schemas isolate identifiers, phone/email, address, and physical characteristics. |
| **s. 24.1** | Safeguards for personal information | **TECHNICAL CONTROL AVAILABLE** | Server-side permission gates (`require_permission`, `require_any_permission`), JWT session expiration, CSRF double-submit token verification, and security headers middleware. |
| **s. 27** | Use of personal information | **TECHNICAL CONTROL AVAILABLE** | Operational segregation: Finance cannot view clinical records; Navigator cannot view restricted cases; IT Admin cannot access operational files. |
| **s. 28** | Disclosure of personal information | **TECHNICAL CONTROL AVAILABLE** | Field-level redaction on Passports (medical section redacted unless caller holds `client.medical.read`); Public intake submissions isolate caller identity from general workers. |
| **s. 31** | Individual access and correction rights | **TECHNICAL CONTROL AVAILABLE** | Audited updates, immutable audit events (`AuditEvent`, `AccessEvent`), and version tracking across `Client` and `Person`. |

---

### C. Saskatchewan HIPA (SS 1999, c H-0.021)

| HIPA Section | Legislative Requirement | Technical Assessment Classification | Actual Platform Implementation & Evidence |
| :--- | :--- | :--- | :--- |
| **s. 2(m)** | Definition of Personal Health Information (PHI) | **TECHNICAL CONTROL AVAILABLE** | Separate domain models: `ClientMedicalProfile`, `ClientAllergy`, `ClientMedicalCondition`, `ClientMedication`, `ClinicalNote`, `ClinicalAddendum`. |
| **s. 16** | Duty of trustee to protect PHI (Administrative, technical, physical safeguards) | **TECHNICAL CONTROL AVAILABLE** | Strict sub-resource isolation: Generic `client.read` does NOT disclose health information. Requires independent `client.medical.read` and `clinical.note.read`. |
| **s. 17** | Information Management Service Providers (IMSP) | **TECHNICAL CONTROL AVAILABLE** | System architecture supports tenant/team segregation, detailed access event logging (`AccessEvent`), and export controls suitable for IMSP operational hosting. |
| **s. 18** | Agreement requirements for IMSPs | **POLICY/PROCESS REQUIRED** | Contractual agreements between CRBCL and external healthcare entities/trustees must be drafted by Counsel. |
| **s. 23** | Consent for collection, use, and disclosure | **POLICY/PROCESS REQUIRED** | Technical model includes consent flags (`sms_consent`, `email_consent`, `PlanSignature`), but formal statutory health consent workflows require operational clinical policy. |
| **s. 27** | Need-to-know / Data minimization | **TECHNICAL CONTROL AVAILABLE** | Front Desk, IT Admin, Board Member, Finance, HR, and Navigator are denied health access (403 Forbidden). Person search results exclude health data and photos. |
| **s. 32** | Individual right of access to PHI | **TECHNICAL CONTROL AVAILABLE** | Authorized clinical workers can export consolidated medical summaries and clinical notes via `CLINICAL_NOTE_EXPORT` and Child Passport. |
| **s. 40** | Right to request correction / Addenda | **TECHNICAL CONTROL AVAILABLE** | Clinical notes support cryptographic immutability: once locked via `CLINICAL_NOTE_LOCK`, edits are forbidden; corrections must be appended as signed `ClinicalAddendum`. |

---

## 4. Operational RBAC Access Boundary Matrix

| Role | Person Record Search | Client Dossier | Medical Profile | Clinical Notes | Case Management | Restricted Case | Intake Narratives | HR Dossier | Finance Requests | Board Reports |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Caseworker** | ✅ (Scoped) | ✅ | ✅ | ❌ | ✅ (Assigned) | ⛔ (Restricted) | ✅ | ❌ | ❌ | ❌ |
| **Supervisor** | ✅ | ✅ | ✅ | ❌ | ✅ (Team) | ⛔ (Restricted) | ✅ (Approve) | ❌ | ❌ | ❌ |
| **Director / Manager** | ✅ | ✅ | ✅ | ❌ | ✅ (All Teams)| ⛔ (Restricted) | ✅ (Approve) | ✅ (Read) | ❌ | ❌ |
| **Clinical Staff (LPN)** | ✅ (Scoped) | ✅ | ✅ | ✅ (Full) | ✅ (Scoped) | ⛔ (Restricted) | ❌ | ❌ | ❌ | ❌ |
| **Cultural Worker** | ✅ (Scoped) | ✅ | ❌ | ❌ | ✅ (Scoped) | ⛔ (Restricted) | ❌ | ❌ | ❌ | ❌ |
| **Navigator** | ❌ (Person) | ✅ (Basic) | ❌ | ❌ | ❌ | ❌ | ✅ (Intake) | ❌ | ❌ | ❌ |
| **Front Desk** | ❌ (Blocked) | ✅ (Basic) | ❌ | ❌ | ❌ | ❌ | ✅ (Public) | ❌ | ❌ | ❌ |
| **Resource Worker** | ✅ (Scoped) | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Resource Supervisor** | ✅ (Scoped) | ✅ (Approve)| ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Resource Director** | ✅ (Scoped) | ✅ (Approve)| ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **HR Staff** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Full) | ❌ | ❌ |
| **Finance Staff** | ❌ | ✅ (Basic) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Full) | ❌ |
| **IT Administrator** | ❌ (Blocked) | ❌ (Blocked)| ❌ | ❌ | ❌ | ❌ | ❌ (Blocked) | ❌ | ❌ | ❌ |
| **Board Member** | ❌ (Blocked) | ❌ (Blocked)| ❌ | ❌ | ❌ | ❌ | ❌ (Blocked) | ❌ | ❌ | ✅ (Aggregates)|
| **Executive Director** | ✅ (Oversight)| ✅ | ✅ | ✅ | ✅ (Oversight)| ⛔ (Conflict) | ✅ (Oversight) | ✅ | ✅ | ✅ |
| **CEO** | ✅ (Oversight)| ✅ | ✅ | ✅ | ✅ (Oversight)| ⛔ (Conflict) | ✅ (Oversight) | ✅ | ✅ | ✅ |

*Legend: ✅ Authorized via active capability permission; ❌ Prohibited / lacks permission (returns HTTP 403); ⛔ Conflict of Interest blocks access even if role is otherwise authorized.*
