"""Shared interval utilities for scheduling operations."""

from datetime import datetime, timedelta


def intervals_overlap(
    *,
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    """Return True when two intervals overlap."""
    return first_start < second_end and second_start < first_end


def merge_intervals(
    intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Merge overlapping intervals to simplify availability checks."""
    if not intervals:
        return []
    sorted_intervals = sorted(intervals, key=lambda item: item[0])
    merged_intervals: list[tuple[datetime, datetime]] = [sorted_intervals[0]]
    for next_start_at, next_end_at in sorted_intervals[1:]:
        current_start_at, current_end_at = merged_intervals[-1]
        if next_start_at <= current_end_at:
            merged_intervals[-1] = (
                current_start_at,
                max(current_end_at, next_end_at),
            )
        else:
            merged_intervals.append((next_start_at, next_end_at))
    return merged_intervals


def insert_merged_interval(
    *,
    merged_intervals: list[tuple[datetime, datetime]],
    interval: tuple[datetime, datetime],
) -> None:
    """Insert one interval into sorted merged intervals with local merge."""
    interval_start_at, interval_end_at = interval
    insert_index = 0
    while (
        insert_index < len(merged_intervals)
        and merged_intervals[insert_index][1] < interval_start_at
    ):
        insert_index += 1

    while (
        insert_index < len(merged_intervals)
        and merged_intervals[insert_index][0] <= interval_end_at
    ):
        existing_start_at, existing_end_at = merged_intervals.pop(insert_index)
        interval_start_at = min(interval_start_at, existing_start_at)
        interval_end_at = max(interval_end_at, existing_end_at)

    merged_intervals.insert(insert_index, (interval_start_at, interval_end_at))


def find_next_available_start(
    *,
    candidate_start: datetime,
    duration: timedelta,
    occupied_intervals: list[tuple[datetime, datetime]],
    horizon_end: datetime,
) -> datetime | None:
    """Return earliest non-overlapping start >= candidate_start within horizon."""
    resolved_start = candidate_start
    for occupied_start, occupied_end in occupied_intervals:
        resolved_end = resolved_start + duration
        if resolved_end <= occupied_start:
            break
        if resolved_start >= occupied_end:
            continue
        resolved_start = occupied_end

    if resolved_start + duration > horizon_end:
        return None
    return resolved_start
