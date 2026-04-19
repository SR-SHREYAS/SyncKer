"""Scheduling score logic."""

from datetime import datetime
from typing import Sequence

from app.ai.contracts import SkillTaggedTask


def score_candidate(
    *,
    window_start_at: datetime,
    suggested_start_at: datetime,
    minimum_duration_minutes: int,
    related_tasks: Sequence[SkillTaggedTask],
) -> float:
    """Return a simple score for one generated slot.

    Earlier valid slots score higher, and relevant urgent tasks push the score up.
    """
    minutes_from_start = max(
        (suggested_start_at - window_start_at).total_seconds() / 60, 0
    )
    raw_score = 100 - (minutes_from_start / max(minimum_duration_minutes, 15))
    if related_tasks:
        raw_score += min(len(related_tasks) * 5, 15)
    return round(max(raw_score, 10), 2)
