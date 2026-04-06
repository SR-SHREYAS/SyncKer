"""Rule-based scheduling engine."""

from app.ai.constraints import resolve_window
from app.ai.intersection import pick_first_common_slot
from app.ai.scoring import score_candidate


class SchedulerEngine:
    """Small rule-based engine for first-release suggestions."""

    def generate(
        self,
        *,
        participant_user_ids: list[int],
        skill_id: int,
        minimum_duration_minutes: int,
        window_start_at,
        window_end_at,
        tasks: list[object],
        availability_blocks: list[object],
        routine_blocks: list[object],
    ) -> dict[str, object]:
        """Generate one session suggestion with planning-aware rules."""
        resolved_start, resolved_end = resolve_window(
            window_start_at,
            window_end_at,
            minimum_duration_minutes,
        )
        related_tasks = [
            task for task in tasks if task.skill_id is None or task.skill_id == skill_id
        ]
        suggested_start_at, suggested_end_at = pick_first_common_slot(
            window_start_at=resolved_start,
            window_end_at=resolved_end,
            minimum_duration_minutes=minimum_duration_minutes,
            availability_blocks=availability_blocks,
            routine_blocks=routine_blocks,
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
            "participant_user_ids": participant_user_ids,
            "skill_id": skill_id,
            "suggested_start_at": suggested_start_at,
            "suggested_end_at": suggested_end_at,
            "score": score,
            "explanation": explanation,
        }
