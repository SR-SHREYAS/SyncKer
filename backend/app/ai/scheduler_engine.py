"""Rule-based scheduling engine."""

from dataclasses import dataclass
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


@dataclass(frozen=True)
class SlotReasonConfig:
    """Score and explanation metadata for one slot reason."""

    score_multiplier: float
    explanation: str


class SchedulerEngine:
    """Small rule-based engine for first-release suggestions."""

    SLOT_REASON_CONFIG_BY_REASON: dict[SlotReason, SlotReasonConfig] = {
        SLOT_REASON_FOUND: SlotReasonConfig(
            score_multiplier=1.0,
            explanation=(
                "Suggested earliest common slot by intersecting participant availability "
                "and subtracting routine and planned-task conflicts."
            ),
        ),
        SLOT_REASON_NO_OVERLAP: SlotReasonConfig(
            score_multiplier=0.5,
            explanation=(
                "No common slot found in the requested window; returned fallback starting "
                "at window start and clamped to window bounds."
            ),
        ),
        SLOT_REASON_NO_PARTICIPANTS: SlotReasonConfig(
            score_multiplier=0.4,
            explanation=(
                "No participants were provided; returned fallback starting at window start "
                "and clamped to window bounds."
            ),
        ),
    }

    @classmethod
    def get_slot_reason_config(cls, slot_reason: SlotReason) -> SlotReasonConfig:
        """Return slot reason config with exhaustive handling."""
        try:
            return cls.SLOT_REASON_CONFIG_BY_REASON[slot_reason]
        except KeyError as exc:
            raise ValueError(
                f"Unhandled SlotReason in SchedulerEngine: {slot_reason!r}. "
                "Update SLOT_REASON_CONFIG_BY_REASON."
            ) from exc

    @classmethod
    def get_score_multiplier_for_reason(cls, slot_reason: SlotReason) -> float:
        """Return score multiplier for one slot reason."""
        slot_reason_config = cls.get_slot_reason_config(slot_reason)
        return slot_reason_config.score_multiplier

    @classmethod
    def get_explanation_for_reason(cls, slot_reason: SlotReason) -> str:
        """Return explanation text for one slot reason."""
        slot_reason_config = cls.get_slot_reason_config(slot_reason)
        return slot_reason_config.explanation

    def generate(
        self,
        *,
        participant_user_ids: Sequence[int],
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
        # All planned tasks block time in timetable intersection regardless of
        # skill. Skill filtering is used only for scoring relevance.
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

        explanation = self.get_explanation_for_reason(slot_reason)
        score_multiplier = self.get_score_multiplier_for_reason(slot_reason)
        final_score = round(score * score_multiplier, 2)

        return {
            "participant_user_ids": list(participant_user_ids),
            "skill_id": skill_id,
            "suggested_start_at": suggested_start_at,
            "suggested_end_at": suggested_end_at,
            "slot_reason": slot_reason,
            "score": final_score,
            "explanation": explanation,
        }
