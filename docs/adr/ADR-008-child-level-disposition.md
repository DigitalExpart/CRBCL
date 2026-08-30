# ADR-008: Child-Level Disposition Modeling and Provenance Routing

## Status
Approved

## Context
Referrals frequently involve sibling groups or multi-child households where individual children have vastly differing circumstances, ages, safety thresholds, and support needs. Treating an entire intake as having a single uniform outcome (e.g. "Referral Approved: Protection") results in over-intervention for low-risk children and failure to route adolescents to voluntary prevention or post-majority services.

## Decision
1. **Per-Child Disposition Modeling (`child_dispositions`)**:
   - A single referral must capture individualized disposition decisions for *every* child identified on the referral.
   - Supported disposition categories:
     - `PROTECTION`: Child meets statutory protection threshold; routes to a Child Protection Case.
     - `PREVENTION`: Voluntary community/family wellness support; routes to a Family Prevention Program.
     - `SCREEN_OUT`: Concern unsubstantiated or below service threshold; no active service case opened.
     - `EXTERNAL_REFERRAL`: Transferred to another First Nation Child & Family Services agency or specialized external provider.
     - `POST_MAJORITY`: Youth transitioning to adulthood; routes to Post-Majority support services.

2. **Automated Provenance Routing**:
   - Upon supervisor approval of the referral, `ReferralRoutingService` executes atomically:
     - For each child with disposition `PROTECTION` -> creates a Child Protection Case referencing `origin_referral_id` and `origin_disposition_id`.
     - For each child with disposition `PREVENTION` -> creates/updates a Prevention Program Case referencing the referral and family.
     - For `SCREEN_OUT` / `EXTERNAL_REFERRAL` -> records the destination without opening unneeded internal cases.
   - Case opening is idempotent, preventing duplicate cases if approval requests are retried.

## Consequences
- Protects children from blanket over-intervention.
- Accurately reflects Indigenous community-led family wellness practices.
- Maintains strict provenance from intake allegations to resulting open cases.
