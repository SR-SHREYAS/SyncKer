# SyncSkill

SyncSkill is a modular-monolith backend and future frontend for intelligent collaborative skill-sharing sessions.

## Current Release Scope

This first backbone release includes:

- auth and JWT login
- user and profile APIs
- skill catalog and user-skill APIs
- planning APIs for tasks, availability, and routine blocks
- scheduling suggestion APIs
- session booking from suggestions
- initial Alembic schema migration

## Backend Structure

The backend follows a layered traceable flow:

`api -> handler -> service -> repository -> model/schema -> db`

Main backend folders:

- `backend/app/api`
- `backend/app/handlers`
- `backend/app/services`
- `backend/app/repositories`
- `backend/app/models`
- `backend/app/schemas`
- `backend/app/ai`

## Local Setup

1. Copy `.env.example` to `.env`
2. Start Postgres
3. Install backend dependencies
4. Run Alembic migration
5. Start FastAPI

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

## Current API Areas

- `/auth`
- `/users`
- `/skills`
- `/planning`
- `/scheduling`
- `/sessions`

## Notes

- current scheduling logic is rule-based and planning-aware
- local Postgres is mapped to `localhost:5433` to avoid common port conflicts on `5432`
- real matching and stronger slot intersection can be added later without replacing the API shape
- this repo is intentionally the backbone first, then later feature branches can grow around it
