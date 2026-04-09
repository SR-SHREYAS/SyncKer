"""Rule-based scheduling engine."""

from datetime import datetime
from typing import Sequence

from app.ai.constraints import resolve_window
from app.ai.contracts import (
    ParticipantPlannedTask,
    ParticipantTimeBlock,
    SLOT_REASON_FOUND,
    SLOT_REASON_NO_OVERLAP,
    SLOT_REASON_NO_PARTICIPANTS,
    SlotReason,
)
from app.ai.intersection import pick_first_common_slot
from app.ai.scoring import score_candidate


class SchedulerEngine:
    """Small rule-based engine for first-release suggestions."""

    SCORE_MULTIPLIER_BY_SLOT_REASON: dict[SlotReason, float] = {
        SLOT_REASON_FOUND: 1.0,
        SLOT_REASON_NO_OVERLAP: 0.5,
        SLOT_REASON_NO_PARTICIPANTS: 0.4,
    }

    def generate(
        self,
        *,
        participant_user_ids: list[int],
        skill_id: int,
        minimum_duration_minutes: int,
        window_start_at: datetime | None,
        window_end_at: datetime | None,
        tasks: Sequence[ParticipantPlannedTask],
        availability_blocks: Sequence[ParticipantTimeBlock],
        routine_blocks: Sequence[ParticipantTimeBlock],
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
        suggested_start_at, suggested_end_at, slot_reason = pick_first_common_slot(
            participant_user_ids=participant_user_ids,
            window_start_at=resolved_start,
            window_end_at=resolved_end,
            minimum_duration_minutes=minimum_duration_minutes,
            availability_blocks=availability_blocks,
            routine_blocks=routine_blocks,
            tasks=tasks,
        )

        score = score_candidate(
            window_start_at=resolved_start,
            suggested_start_at=suggested_start_at,
            minimum_duration_minutes=minimum_duration_minutes,
            related_tasks=related_tasks,
        )

        if slot_reason == SLOT_REASON_FOUND:
            explanation = (
                "Suggested earliest common slot by intersecting participant availability "
                "and subtracting routine and planned-task conflicts."
            )
        elif slot_reason == SLOT_REASON_NO_PARTICIPANTS:
            explanation = (
                "No participants were provided; returned fallback at window start."
            )
        else:
            explanation = "No common slot found in the requested window; returned fallback at window start."

        score_multiplier = self.SCORE_MULTIPLIER_BY_SLOT_REASON.get(slot_reason, 1.0)
        final_score = round(score * score_multiplier, 2)

        return {
            "participant_user_ids": participant_user_ids,
            "skill_id": skill_id,
            "suggested_start_at": suggested_start_at,
            "suggested_end_at": suggested_end_at,
            "slot_reason": slot_reason,
            "score": final_score,
            "explanation": explanation,
        }
