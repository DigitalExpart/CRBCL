# ADR-035: OCR Document Processing & Human Verification Workflow

## Context
Case workers routinely upload scanned PDFs, court orders, medical forms, and identity documents. Automated OCR is valuable for drafting records, but automated insertion of OCR output into legal child welfare records risks introducing corrupted or inaccurate data.

## Decision
1. **Human-in-the-Loop Verification**: OCR processing produces **Draft Candidate Fields** only. OCR output NEVER directly mutates authoritative client or case records without explicit human review and confirmation.
2. **Asynchronous Execution Pipeline**:
   ```
   Document Upload ──> Secure Storage ──> OCR Async Job ──> Candidate Fields (Draft) ──> Human Review UI (Accept / Reject) ──> Confirmed Record Update
   ```
3. **Field Level Permissions**: Confirming an OCR candidate field requires the user to possess write permissions for that target domain (e.g., `client.identifiers.write` to confirm a Healthcare Number).
4. **OCR Status Lifecycle**: `PENDING -> PROCESSING -> REVIEW_REQUIRED -> CONFIRMED / CANCELLED / FAILED`.

## Status
Accepted.
