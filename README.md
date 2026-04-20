# SyncSkill

SyncSkill is a modular-monolith backend and future frontend for intelligent collaborative skill-sharing sessions.

## Current Release Scope

This first backbone release includes:

- auth and JWT login
- user and profile APIs
- team workspace APIs (create team, add members, list members)
- skill catalog and user-skill APIs
- planning APIs for tasks, availability, and routine blocks
- scheduling suggestion APIs with team membership checks
- session booking from suggestions
- initial Alembic schema migration

## Backend Structure

The backend follows a layered traceable flow:

`api -> handler -> service -> repository -> model/schema -> db`

Main backend folders:

- `backend/app/api`
- `backend/app/api/routes`
- `backend/app/api/handlers`
- `backend/app/services`
- `backend/app/repositories`
- `backend/app/models`
- `backend/app/schemas`
- `backend/app/ai`

## Local Setup

1. Create `.env` in repo root
2. Start Postgres
3. Install backend dependencies
4. Run Alembic migration
5. Start FastAPI

Minimal `.env` values:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/syncskill
JWT_SECRET_KEY=change-me-please-use-a-long-secret-key
```

## Suggested Commands

Start Postgres:

```bash
docker compose up -d
```

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements/base.txt
pip install -r backend/requirements/dev.txt
```

Run migration:

```bash
cd backend
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --reload --app-dir backend
```

## CI Test Gate

GitHub Actions workflow:

- `.github/workflows/backend-ci.yml`

This CI gate runs:

- `black --check app tests`
- `pytest -q --ignore=tests/test_mvp_scheduler_http_flow.py`
- `pytest -q tests/test_mvp_scheduler_http_flow.py`

Equivalent local commands:

```bash
cd backend
black --check app tests
pytest -q --ignore=tests/test_mvp_scheduler_http_flow.py
pytest -q tests/test_mvp_scheduler_http_flow.py
```

## Current API Areas

- `/auth`
- `/users`
- `/skills`
- `/teams`
- `/planning`
- `/scheduling`
- `/sessions`

## Notes

- current scheduling logic is rule-based and planning-aware
- local Postgres is mapped to `localhost:5433` to avoid common port conflicts on `5432`
- real matching and stronger slot intersection can be added later without replacing the API shape
- this repo is intentionally the backbone first, then later feature branches can grow around it
