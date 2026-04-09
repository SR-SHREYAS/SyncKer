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
        routine_blocks: list[object]
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
        suggested_start_at, suggested_end_at, found_common_slot = (
            pick_first_common_slot(
                participant_user_ids=participant_user_ids,
                window_start_at=resolved_start,
                window_end_at=resolved_end,
                minimum_duration_minutes=minimum_duration_minutes,
                availability_blocks=availability_blocks,
                routine_blocks=routine_blocks,
                tasks=tasks,
            )
        )

        if suggested_end_at > resolved_end:
            suggested_start_at = resolved_start
            suggested_end_at = resolved_start
            found_common_slot = False

        score = score_candidate(
            window_start_at=resolved_start,
            suggested_start_at=suggested_start_at,
            minimum_duration_minutes=minimum_duration_minutes,
            related_tasks=related_tasks,
        )

        if found_common_slot:
            explanation = (
                "Suggested earliest common slot by intersecting participant availability "
                "and subtracting routine and planned-task conflicts."
            )
        else:
            explanation = "No common slot found in the requested window; returned fallback at window start."

        return {
            "participant_user_ids": participant_user_ids,
            "skill_id": skill_id,
            "suggested_start_at": suggested_start_at,
            "suggested_end_at": suggested_end_at,
            "score": score,
            "explanation": explanation,
        }
