# JobPilot

Personal job-search automation tool: discovers postings, scores fit against
a structured resume, tailors application content, and tracks the full
pipeline through a Kanban dashboard.

## Stack
- Backend: Django + Django REST Framework + PostgreSQL
- Frontend: React
- Background jobs: Celery + Redis (introduced in later sprints)

## Status
Early development. See `docs/` (added in later sprints) for architecture
decisions and requirements traceability.

## Setup
Setup instructions will be added as each part of the stack becomes runnable
(backend in Sprint 1, frontend in Sprint 1, full local run in Sprint 19).

## Running with Docker

The full stack (PostgreSQL, Redis, Django, Celery worker, Celery beat, React) runs via Docker Compose.

### Prerequisites
- Docker Desktop installed and running
- A `.env` file at the repo root (see `.env.example`) with `POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD`
- `backend/.env` populated with real secrets (Anthropic API key, Google OAuth credentials, Django secret key) — see `backend/.env.example`

### Start everything
\`\`\`
docker compose up -d
\`\`\`

### First-time setup (fresh database)
\`\`\`
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
\`\`\`

### Access
- Frontend: http://localhost:5173
- Backend admin: http://localhost:8000/admin/
- Backend API: http://localhost:8000/api/

### Logs
\`\`\`
docker compose logs -f [service_name]
\`\`\`

### Stop everything
\`\`\`
docker compose down
\`\`\`
(Add `-v` to also remove the Postgres data volume — this deletes all containerized data permanently.)