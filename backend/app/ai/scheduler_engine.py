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
    ) -> dict[str, object]:
        """Generate one session suggestion with a simple explanation."""
        resolved_start, resolved_end = resolve_window(
            window_start_at,
            window_end_at,
            minimum_duration_minutes,
        )
        suggested_start_at, suggested_end_at = pick_first_common_slot(
            window_start_at=resolved_start,
            minimum_duration_minutes=minimum_duration_minutes,
        )

        if suggested_end_at > resolved_end:
            suggested_start_at = resolved_start
            suggested_end_at = resolved_start

        score = score_candidate(
            window_start_at=resolved_start,
            suggested_start_at=suggested_start_at,
            minimum_duration_minutes=minimum_duration_minutes,
        )

        explanation = (
            "Suggested this slot using the first valid rule-based window "
            "for the selected users and skill."
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
