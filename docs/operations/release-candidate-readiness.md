# CRBCL Release-Candidate Readiness & Operational Review

**Baseline Checkpoint:** `7df63f10fd3707fdb46beb520353a48a451aaaa4`  
**Migration Head:** `026_board_dashboard_publication_controls`  
**Document Status:** FINAL EVIDENCE-BASED READINESS AUDIT  
**Target Program:** Controlled CRBCL Multi-Department UAT (Synthetic / De-identified Data)  

---

## 1. Final Readiness Determination

### **STATUS: READY FOR CONTROLLED UAT WITH KNOWN LIMITATIONS**

The CRBCL software platform is architecturally sound and functionally ready for **controlled User Acceptance Testing with synthetic and de-identified data** across participating operational departments.

> [!CAUTION]
> **UNRESTRICTED PRODUCTION USE IS NOT APPROVED.**  
> Technical readiness supports controlled UAT using synthetic and de-identified data under supervised conditions. It **does NOT** approve live production deployment or the entry of actual child and family case records. Production deployment remains strictly gated by the 7 pre-production release gates detailed in Section 6.

---

## 2. Automated Test Baseline & Evidence Classification

| Verification Suite | Target | Result | Evidence Classification | Notes |
|---|---|---|:---:|---|
| **Cross-Module UAT Suite** | `tests/test_cross_module_uat.py` | **7 / 7 PASSED** | `AUTOMATED E2E / PARTIAL` | Covers Chains A–F, IDOR denials, immutability, Decimal integrity |
| **Board Dashboard Suite** | `tests/test_board_dashboard.py` | **27 / 27 PASSED** | `DOMAIN REGRESSION VERIFIED` | Governance boundary, publication firewall, aggregate metrics |
| **CEO Dashboard Suite** | `tests/test_ceo_dashboard.py` | **19 / 19 PASSED** | `DOMAIN REGRESSION VERIFIED` | Initiatives, department updates, board actions, metrics |
| **Full Backend Regression** | `pytest -q` | **252 passed, 1 skipped** | `DOMAIN REGRESSION VERIFIED` | Zero failures across all backend modules |
| **Code Linter** | `ruff check app tests` | **PASS (0 errors)** | `STATIC CODE AUDIT` | Zero syntax, import, or lint violations |
| **Frontend Production Build** | `npm run build` (`vite build`) | **PASS (0 errors)** | `STATIC BUILD AUDIT` | 3,049 modules compiled; production bundle generated in `/dist` |
| **Mobile Integration API** | `tests/test_phase15_mobile_sync.py` | **PASSED** | `AUTOMATED VERIFIED` | Backend delta sync, batch upload, and token revocation |
| **Flutter Mobile Client** | `mobile/` | **NOT EXECUTED** | `ENVIRONMENT VERIFICATION REQUIRED` | Flutter CLI is unavailable on this server; native client unverified |

---

## 3. Database & Migration Verification (Phase 11)

- **Current Revision Head:** `026_board_dashboard_publication_controls` (linear single head verified).
- **Alembic History Chain:** Linear from 001 through 026.
- **Verification Qualification:**
  > [!WARNING]
  > **POSTGRESQL MIGRATION VERIFICATION REQUIRED BEFORE PRODUCTION**  
  > Automated tests executed against an in-memory SQLite database using custom compiler hooks (`@compiles(JSONB, "sqlite")`, `@compiles(UUID, "sqlite")`). While schema models and migration scripts adhere to PostgreSQL standards, **a dynamic execution of `alembic upgrade head` against a clean, disposable PostgreSQL instance has NOT yet been run in this environment and must be completed prior to production deployment.**
- **Downgrade Safety:** Downgrade scripts exist across migrations. In production, database rollbacks are strictly handled via point-in-time snapshot recovery rather than running downgrade migrations.

---

## 4. Integration Status Classification

### A. Google Form Public Ingestion (`redbearlodge.ca/intake-form/`)
- **Integration Implementation:** `IMPLEMENTATION VERIFIED WITH SYNTHETIC PAYLOADS`
- **Production Binding:** `EXTERNAL CONFIGURATION / LIVE UAT REQUIRED`
- **Status:** Webhook payload parsing, secret comparison, sequential FD-YYYY-NNNNNN numbering, and referral conversion are verified. Production binding requires mapping live field IDs, installing Apps Script trigger, and configuring `FRONT_DESK_WEBHOOK_SECRET`.

### B. Microsoft 365 Graph Integration
- **Integration Status:** `EXTERNAL CONFIGURATION REQUIRED`
- **Status:** Operates safely on `FakeMicrosoftProvider` for UAT. Live synchronization requires Azure AD App Registration, tenant credential provisioning, and Graph API permission grants.

### C. Mobile Application
- **Backend Sync API:** `AUTOMATED VERIFIED` (delta sync and conflict handling).
- **Flutter Client:** `ENVIRONMENT VERIFICATION REQUIRED` (Flutter CLI unavailable; native build unverified).

---

## 5. Unresolved Policy Decisions (CRBCL Governance Items)

Major feature development is frozen; however, the following operational and governance policy decisions must be resolved by CRBCL leadership before or during UAT:

### A. Resource Unit Policy Items (Restored from Requirements)
1. **Monitoring Visit Cadence:** Policy determination on mandatory frequency of routine placement home inspections (e.g. 30-day vs. 60-day cycles).
2. **Caregiver Training Requirements & Renewals:** Clarification of required annual pre-service and in-service training hours (cultural competence, trauma-informed care, CPR).
3. **Background Check Clearances & Renewals:** Renewal intervals for Criminal Record and Child Abuse Registry clearances (e.g. annual vs. triennial).
4. **Licensing & Inspection Cadence:** Standard Foster Home license terms (1-year provisional vs. 2-year standard renewal).
5. **Caregiver Support Expenditure Thresholds:** Spending limit requiring Director authorization vs. caseworker discretion.
6. **Placement Matching Weighting:** Relative scoring weights for cultural community match vs. geographic proximity vs. sibling co-placement.
7. **Caregiver Complaint SLAs:** Target resolution timelines for Level 1 (informal) vs. Level 2 (formal investigation) complaints.
8. **Long-Term Retention & Outcome Definitions:** Formalization of caregiver retention metrics and permanency success indicators.

### B. Executive & Board Governance Policy Items
1. **HR Workforce Metrics:** Definition of Full-Time Equivalent (FTE) formulas, permanent vs. term contract rules, and resignation vs. termination turnover classification.
2. **Board Decision Recording Authority:** Delegation of who possesses authority to record formal Board resolutions (Board Secretary vs. CEO).
3. **Publication Authority Delegation:** Policy on whether the Executive Director may publish department reports to the Board in the CEO's absence.
4. **Chief & Council Visibility Model:** Determination of whether Chief & Council receive an executive-level view, a board-level view, or a specialized governance dashboard.
5. **Available Resource Bed Semantic Validation:** Validation of net available bed calculation (`total_capacity - active_children`) in cases where children are placed in external/kinship homes outside CRBCL licensed homes.

---

## 6. Pre-Production Release Gates

The platform cannot proceed from Controlled UAT to live production without satisfying these **seven mandatory release gates**:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Manual CRBCL Multi-Department UAT Sign-Off               │
│ • Front Desk, CFS Caseworkers, Supervisors, Resource Unit   │
│ • Finance, Human Resources, CEO, and Board Representatives   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. CRBCL Governance Policy Decisions Formalized             │
│ • Resource Unit cadences, HR workforce definitions          │
│ • Chief & Council visibility model                          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Live External Integration Configuration                  │
│ • Google Form entry IDs and Apps Script trigger verified    │
│ • Microsoft 365 Azure AD tenant credentials configured      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Disposable PostgreSQL Migration Verification             │
│ • Execute `alembic upgrade head` against fresh PostgreSQL   │
│ • Verify schema integrity, constraints, and index creation  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Independent Penetration & Security Testing               │
│ • OWASP Top 10, IDOR deep probe on sensitive endpoints      │
│ • Session management, token revocation, CSRF audit          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Legal & Privacy Review                                   │
│ • First Nations OCAP compliance                             │
│ • Bill C-92 & provincial child welfare privacy standards    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Operational Rollout & Staff Training Program             │
│ • Role-based user training, incident runbooks, support desk │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Recommended Controlled UAT Pilot Progression

Controlled UAT should proceed in five disciplined stages using synthetic data:

- **Stage 1 (Week 1): Front Desk & Public Triage Intake**  
  *Focus:* Ingest synthetic submissions, review queue, route to CFS, duplicate checks, convert to referral.
- **Stage 2 (Week 2): Protection Casework & Family Wellness**  
  *Focus:* Open case files, create progress notes, lock notes, submit addenda, log Active Efforts.
- **Stage 3 (Week 3): Resource Unit & Caregiver Licensing**  
  *Focus:* Manage recruitment inquiries, state transitions, placement matching queries, license issuance.
- **Stage 4 (Week 4): Finance Operations & Placement Billing**  
  *Focus:* Service requests, sub-cent pricing, anti-self-approval enforcement, second-officer approvals.
- **Stage 5 (Week 5): CEO Command Centre & Board Governance**  
  *Focus:* Review department executive updates, strategic initiatives, explicit Board publication, `/board` view.
