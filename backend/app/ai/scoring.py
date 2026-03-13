"""Scheduling score logic."""

from datetime import datetime


def score_candidate(
    *,
    window_start_at: datetime,
    suggested_start_at: datetime,
    minimum_duration_minutes: int,
) -> float:
    """Return a simple score for one generated slot.

    Earlier valid slots score slightly higher in the MVP rule engine.
    """
    minutes_from_start = max((suggested_start_at - window_start_at).total_seconds() / 60, 0)
    raw_score = 100 - (minutes_from_start / max(minimum_duration_minutes, 15))
    return round(max(raw_score, 10), 2)
