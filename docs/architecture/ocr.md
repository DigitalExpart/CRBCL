# OCR Document Processing Architecture

## Pipeline Flow
1. **Document Upload**: User uploads PDF/Image to secure storage.
2. **Virus Scan & Validation**: Document verified.
3. **Asynchronous Job**: Background job enqueues OCR processing task (`ocr_jobs`).
4. **Draft Candidate Extraction**: `OcrProvider` parses text and generates candidate key-value pairs with confidence scores.
5. **Human Review & Confirmation**: Candidate fields are presented in `OCRReview.jsx`. User accepts or rejects each field.
6. **Authoritative Persistence**: Confirmed fields are written to the database using caller field-level permissions.
