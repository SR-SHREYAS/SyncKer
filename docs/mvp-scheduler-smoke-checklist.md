# MVP Scheduler Smoke Checklist

This checklist keeps our release smoke flow aligned between Postman and pytest.

## Goal

Validate the core MVP scheduler path works end-to-end:

1. auth
2. team setup
3. participant tasks
4. suggestion generation
5. suggestion apply
6. timetable visibility

## Primary Flow

1. `POST /auth/register` (owner)
2. `POST /auth/register` (participant)
3. `POST /teams` (owner creates team)
4. `POST /teams/{team_id}/members` (owner adds participant)
5. `POST /planning/tasks` (owner creates planned task)
6. `POST /planning/tasks` (participant creates planned task)
7. `POST /scheduling/suggestions/generate` (owner generates suggestion)
8. `POST /scheduling/suggestions/{suggestion_id}/apply` (owner applies suggestion)
9. `GET /planning/tasks` (owner sees collaboration task)
10. `GET /planning/teams/{team_id}/timetable` (owner sees team rows and collaboration task)

## Minimum Negative Checks

1. Invalid JWT token returns `401`.
2. Non-member user reading team timetable returns `403`.
3. Applying non-pending suggestion returns `409`.

## Pytest Coverage

Implemented in:

- `backend/tests/test_mvp_scheduler_flow.py`

## Manual Postman Alignment

Use the same sequence and expected status codes from this file:

- `201` create resources
- `200` read/update/apply success
- `401` invalid auth
- `403` forbidden team access
- `409` invalid apply state
