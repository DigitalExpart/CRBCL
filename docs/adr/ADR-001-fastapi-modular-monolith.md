# ADR-001: FastAPI Modular Monolith Architecture

## Status
Approved

## Context
CRBCL requires high developmental velocity, strict data privacy, strong type-safety, and unified relational integrity across case management, child welfare, finance, and human resources.

## Decision
Adopt a Python FastAPI Modular Monolith structured by domain capabilities (`app/auth`, `app/permissions`, `app/audit`, `app/workflows`, `app/storage`, `app/api/v1`).

## Consequences
- Single deployable backend minimizing operational overhead.
- Clear internal module boundaries allowing future extraction if required.
- High-performance asynchronous I/O via `uvicorn` and `asyncpg`.
