# Local Development Operations Guide

## Prerequisites
- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.11+ (optional if using Docker)

## Quick Start (Dockerized Backend)

1. **Start Backend Infrastructure**:
   ```bash
   cd infrastructure
   docker compose up -d
   ```

2. **Apply Database Migrations & Seed Data**:
   ```bash
   # Run within the API container or locally:
   docker compose exec api alembic upgrade head
   docker compose exec api python -m app.core.seed
   ```

3. **Start Frontend**:
   ```bash
   # In root repository directory:
   npm install
   npm run dev
   ```

4. **Access the Applications**:
   - Frontend: `http://localhost:5173`
   - Backend API Docs: `http://localhost:8000/docs`
   - Default Dev Admin: `admin@crbcl.ca` / `crbcl_admin_2026`
