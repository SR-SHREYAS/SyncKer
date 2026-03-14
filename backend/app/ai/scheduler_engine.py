"""Rule-based scheduling engine."""

from app.ai.constraints import resolve_window
from app.ai.intersection import pick_first_common_slot
from app.ai.scoring import score_candidate


class SchedulerEngine:
    """Small rule-based engine for first-release suggestions."""

    def generate(
        self,
        *,
        learner_user_id: int,
        mentor_user_id: int,
        skill_id: int,
        minimum_duration_minutes: int,
        window_start_at,
        window_end_at,
        learner_tasks: list[object],
        mentor_tasks: list[object],
        learner_availability_blocks: list[object],
        mentor_availability_blocks: list[object],
        learner_routine_blocks: list[object],
        mentor_routine_blocks: list[object],
    ) -> dict[str, object]:
        """Generate one session suggestion with planning-aware rules."""
        resolved_start, resolved_end = resolve_window(
            window_start_at,
            window_end_at,
            minimum_duration_minutes,
        )
        all_availability = [
            *learner_availability_blocks,
            *mentor_availability_blocks,
        ]
        all_routines = [
            *learner_routine_blocks,
            *mentor_routine_blocks,
        ]
        related_tasks = [
            task
            for task in [*learner_tasks, *mentor_tasks]
            if task.skill_id is None or task.skill_id == skill_id
        ]
        suggested_start_at, suggested_end_at = pick_first_common_slot(
            window_start_at=resolved_start,
            window_end_at=resolved_end,
            minimum_duration_minutes=minimum_duration_minutes,
            availability_blocks=all_availability,
            routine_blocks=all_routines,
        )

        if suggested_end_at > resolved_end:
            suggested_start_at = resolved_start
            suggested_end_at = resolved_start

        score = score_candidate(
            window_start_at=resolved_start,
            suggested_start_at=suggested_start_at,
            minimum_duration_minutes=minimum_duration_minutes,
            related_tasks=related_tasks,
        )

        explanation = (
            "Suggested this slot using availability, routine conflicts, "
            "and tasks related to the selected skill."
        )

        return {
            "learner_user_id": learner_user_id,
            "mentor_user_id": mentor_user_id,
            "skill_id": skill_id,
            "suggested_start_at": suggested_start_at,
            "suggested_end_at": suggested_end_at,
            "score": score,
            "explanation": explanation,
        }
