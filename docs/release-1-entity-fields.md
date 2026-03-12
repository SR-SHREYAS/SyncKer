# Release 1 Entity Fields

This document locks the first-release backend entity scope before implementation.

## Design rules

- Only fields required for MVP are included.
- Audit fields are standardized where useful: `id`, `created_at`, `updated_at`.
- Business rules stay in services and the scheduling engine, not in ORM models.

## User

- `id`
- `email`
- `username`
- `password_hash`
- `is_active`
- `created_at`
- `updated_at`

## Profile

- `id`
- `user_id`
- `full_name`
- `bio`
- `role`
- `timezone`
- `created_at`
- `updated_at`

Notes:
- `role` is `learner`, `mentor`, or `both`.
- `timezone` is required because scheduling depends on it.

## Skill

- `id`
- `name`
- `slug`
- `description`
- `created_at`

## UserSkill

- `id`
- `user_id`
- `skill_id`
- `proficiency_level`
- `is_teaching`
- `is_learning`
- `created_at`

Notes:
- `proficiency_level` should be a simple bounded scale in release 1.
- `is_teaching` and `is_learning` allow one skill to support both directions.

## Task

- `id`
- `user_id`
- `title`
- `description`
- `priority`
- `status`
- `estimated_minutes`
- `deadline_at`
- `skill_id`
- `created_at`
- `updated_at`

Notes:
- `priority` should stay simple: low, medium, high.
- `status` should stay simple: pending, in_progress, completed.
- `skill_id` is optional but useful for scheduling skill-based sessions.

## AvailabilityBlock

- `id`
- `user_id`
- `day_of_week`
- `start_time`
- `end_time`
- `is_recurring`
- `specific_date`
- `created_at`
- `updated_at`

Notes:
- Use recurring weekly blocks for normal availability.
- `specific_date` supports one-off availability without a second model.

## RoutineBlock

- `id`
- `user_id`
- `title`
- `day_of_week`
- `start_time`
- `end_time`
- `is_recurring`
- `specific_date`
- `created_at`
- `updated_at`

Notes:
- This represents regular occupied time or routine commitments.
- It is intentionally separate from availability to simplify reasoning.

## SessionSuggestion

- `id`
- `generated_for_user_id`
- `mentor_user_id`
- `learner_user_id`
- `skill_id`
- `suggested_start_at`
- `suggested_end_at`
- `score`
- `status`
- `explanation`
- `created_at`

Notes:
- `status` should start as `pending`, `accepted`, `rejected`, `expired`.
- `explanation` is important for transparency and demo value.

## Session

- `id`
- `session_suggestion_id`
- `skill_id`
- `title`
- `scheduled_start_at`
- `scheduled_end_at`
- `status`
- `created_by_user_id`
- `created_at`
- `updated_at`

Notes:
- `status` should start as `scheduled`, `completed`, `cancelled`.

## SessionParticipant

- `id`
- `session_id`
- `user_id`
- `participant_role`
- `response_status`
- `joined_at`
- `created_at`

Notes:
- `participant_role` should start as `mentor` or `learner`.
- `response_status` should start as `invited`, `accepted`, `declined`.

## Deferred for later releases

These are intentionally excluded from release 1:

- `CommitmentBlock`
- `Notification`
- `ChatMessage`
- `WhiteboardState`
- `FileAsset`
- `MLFeedback`
- `AvailabilityReliabilityScore`
