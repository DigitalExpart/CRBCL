# ADR-022: Financial Money Model, Currency, and Deterministic Rounding

## Status
Accepted (Phase 10)

## Context
CRBCL (Chief Red Bear Children's Lodge) operates child and family wellness services requiring financial tracking, purchase orders, client disbursements, staff expense reimbursements, and placement facility per-diem billing.
Binary floating-point arithmetic (`float` in Python and `DOUBLE PRECISION`/`FLOAT` in SQL) introduces well-known precision artifacts (e.g., `0.10 + 0.20 = 0.30000000000000004`), which violates accounting principles and legal audit standards.

## Decision
1. **Authoritative Calculation in Decimal**:
   - All backend calculations must strictly use Python `decimal.Decimal`.
   - Floating-point arithmetic (`float`) is strictly prohibited in financial domain models, services, repositories, and schemas.
2. **Database Numeric Precision**:
   - Monetary values (amounts, totals, subtotals, budgets, funding totals) must use PostgreSQL `NUMERIC(14,2)`:
     - Supports up to \$999,999,999,999.99 (999 billion CAD), with exactly 2 fractional digits for cents.
   - Per-diem daily rates and quantities use `NUMERIC(10,2)`.
3. **Operational Currency**:
   - The authoritative operational currency is Canadian Dollars (`CAD`).
   - Currency codes are explicitly stored as 3-letter ISO-4217 strings (defaulting to `"CAD"`).
4. **Deterministic Rounding Policy**:
   - All line-item, subtotal, and tax calculations use `ROUND_HALF_UP` (standard banking/accounting rounding).
   - Python's `decimal.ROUND_HALF_UP` is enforced via helper functions (`quantize_money(val: Decimal) -> Decimal`).
5. **Server-Side Authority**:
   - The server is the sole calculation authority for line items, subtotals, taxes, and grand totals.
   - Any client-submitted total amounts that deviate from the server's calculated total are rejected.

## Consequences
- **Positive**: Guaranteed zero floating-point drift, deterministic database round-trips, and full compliance with Canadian financial audit standards.
- **Trade-off**: Requires explicit casting from strings/ints to `Decimal` in Pydantic schemas and serialization to string/formatted decimals for JSON APIs.
