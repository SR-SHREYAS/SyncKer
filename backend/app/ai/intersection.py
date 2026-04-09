"""Availability intersection logic."""

from datetime import datetime, timedelta
from typing import Literal, Sequence

from app.ai.contracts import ParticipantPlannedTask, ParticipantTimeBlock
from app.ai.datetime_utils import normalize_datetime_to_utc
from app.ai.time_windows import merge_intervals


def _belongs_to_participant(record: object, participant_user_id: int) -> bool:
    """Return True when a record belongs to one participant.

    If no user_id exists, treat the record as globally applicable.
    """
    record_user_id = getattr(record, "user_id", None)
    if record_user_id is None:
        return True
    return record_user_id == participant_user_id


def _clip_interval_to_window(
    *,
    interval_start_at: datetime,
    interval_end_at: datetime,
    window_start_at: datetime,
    window_end_at: datetime,
) -> tuple[datetime, datetime] | None:
    """Clip one interval to the scheduling window."""
    interval_start_at = normalize_datetime_to_utc(interval_start_at)
    interval_end_at = normalize_datetime_to_utc(interval_end_at)
    window_start_at = normalize_datetime_to_utc(window_start_at)
    window_end_at = normalize_datetime_to_utc(window_end_at)
    clipped_start_at = max(interval_start_at, window_start_at)
    clipped_end_at = min(interval_end_at, window_end_at)
    if clipped_end_at <= clipped_start_at:
        return None
    return clipped_start_at, clipped_end_at


def _build_time_block_intervals(
    *,
    blocks: Sequence[ParticipantTimeBlock],
    window_start_at: datetime,
    window_end_at: datetime,
) -> list[tuple[datetime, datetime]]:
    """Expand recurring and one-off blocks to concrete datetime intervals."""
    concrete_intervals: list[tuple[datetime, datetime]] = []
    current_date = window_start_at.date()

    while current_date <= window_end_at.date():
        for block in blocks:
            if block.is_recurring:
                if block.day_of_week != current_date.weekday():
                    continue
            elif block.specific_date != current_date:
                continue

            block_start_at = datetime.combine(
                current_date,
                block.start_time,
                tzinfo=window_start_at.tzinfo,
            )
            block_end_at = datetime.combine(
                current_date,
                block.end_time,
                tzinfo=window_start_at.tzinfo,
            )
            if block_end_at <= block_start_at:
                continue

            clipped_interval = _clip_interval_to_window(
                interval_start_at=block_start_at,
                interval_end_at=block_end_at,
                window_start_at=window_start_at,
                window_end_at=window_end_at,
            )
            if clipped_interval is not None:
                concrete_intervals.append(clipped_interval)
        current_date += timedelta(days=1)

    return merge_intervals(concrete_intervals)


def _build_task_busy_intervals(
    *,
    tasks: Sequence[ParticipantPlannedTask],
    window_start_at: datetime,
    window_end_at: datetime,
) -> list[tuple[datetime, datetime]]:
    """Build concrete busy ranges from planned tasks."""
    busy_intervals: list[tuple[datetime, datetime]] = []
    for task in tasks:
        task_start_at = getattr(task, "planned_start_at", None)
        task_end_at = getattr(task, "planned_end_at", None)
        if task_start_at is None or task_end_at is None:
            continue
        if task_end_at <= task_start_at:
            continue

        clipped_interval = _clip_interval_to_window(
            interval_start_at=task_start_at,
            interval_end_at=task_end_at,
            window_start_at=window_start_at,
            window_end_at=window_end_at,
        )
        if clipped_interval is not None:
            busy_intervals.append(clipped_interval)

    return merge_intervals(busy_intervals)


def _subtract_intervals(
    *,
    available_intervals: list[tuple[datetime, datetime]],
    blocked_intervals: list[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Subtract blocked intervals from available intervals."""
    free_intervals: list[tuple[datetime, datetime]] = []
    for available_start_at, available_end_at in available_intervals:
        cursor = available_start_at
        for blocked_start_at, blocked_end_at in blocked_intervals:
            if blocked_end_at <= cursor:
                continue
            if blocked_start_at >= available_end_at:
                break
            if blocked_start_at > cursor:
                free_intervals.append((cursor, min(blocked_start_at, available_end_at)))
            cursor = max(cursor, blocked_end_at)
            if cursor >= available_end_at:
                break

        if cursor < available_end_at:
            free_intervals.append((cursor, available_end_at))

    return merge_intervals(free_intervals)


def _intersect_intervals(
    left_intervals: Sequence[tuple[datetime, datetime]],
    right_intervals: Sequence[tuple[datetime, datetime]],
) -> list[tuple[datetime, datetime]]:
    """Return overlap of two interval lists after canonical normalization."""
    normalized_left_intervals = merge_intervals(list(left_intervals))
    normalized_right_intervals = merge_intervals(list(right_intervals))

    overlaps: list[tuple[datetime, datetime]] = []
    left_index = 0
    right_index = 0

    while left_index < len(normalized_left_intervals) and right_index < len(
        normalized_right_intervals
    ):
        left_start_at, left_end_at = normalized_left_intervals[left_index]
        right_start_at, right_end_at = normalized_right_intervals[right_index]

        overlap_start_at = max(left_start_at, right_start_at)
        overlap_end_at = min(left_end_at, right_end_at)
        if overlap_end_at > overlap_start_at:
            overlaps.append((overlap_start_at, overlap_end_at))

        if left_end_at <= right_end_at:
            left_index += 1
        else:
            right_index += 1

    return overlaps


def _build_participant_free_intervals(
    *,
    participant_user_id: int,
    window_start_at: datetime,
    window_end_at: datetime,
    availability_blocks: Sequence[ParticipantTimeBlock],
    routine_blocks: Sequence[ParticipantTimeBlock],
    tasks: Sequence[ParticipantPlannedTask],
) -> list[tuple[datetime, datetime]]:
    """Build one participant's free intervals in the window."""
    participant_availability_blocks = [
        block
        for block in availability_blocks
        if _belongs_to_participant(block, participant_user_id)
    ]
    if participant_availability_blocks:
        available_intervals = _build_time_block_intervals(
            blocks=participant_availability_blocks,
            window_start_at=window_start_at,
            window_end_at=window_end_at,
        )
    else:
        available_intervals = [(window_start_at, window_end_at)]

    participant_routine_blocks = [
        block
        for block in routine_blocks
        if _belongs_to_participant(block, participant_user_id)
    ]
    routine_busy_intervals = _build_time_block_intervals(
        blocks=participant_routine_blocks,
        window_start_at=window_start_at,
        window_end_at=window_end_at,
    )
    participant_tasks = [
        task for task in tasks if _belongs_to_participant(task, participant_user_id)
    ]
    task_busy_intervals = _build_task_busy_intervals(
        tasks=participant_tasks,
        window_start_at=window_start_at,
        window_end_at=window_end_at,
    )
    blocked_intervals = merge_intervals([*routine_busy_intervals, *task_busy_intervals])
    return _subtract_intervals(
        available_intervals=available_intervals,
        blocked_intervals=blocked_intervals,
    )


def pick_first_common_slot(
    *,
    participant_user_ids: list[int],
    window_start_at: datetime,
    window_end_at: datetime,
    minimum_duration_minutes: int,
    availability_blocks: Sequence[ParticipantTimeBlock],
    routine_blocks: Sequence[ParticipantTimeBlock],
    tasks: Sequence[ParticipantPlannedTask],
) -> tuple[datetime, datetime, Literal["found", "no_overlap", "no_participants"]]:
    """Return earliest common slot using participant free-window intersections."""
    window_start_at = normalize_datetime_to_utc(window_start_at)
    window_end_at = normalize_datetime_to_utc(window_end_at)
    minimum_duration = timedelta(minutes=minimum_duration_minutes)

    if not participant_user_ids:
        fallback_start_at = window_start_at
        fallback_end_at = window_start_at + minimum_duration
        return fallback_start_at, fallback_end_at, "no_participants"

    participant_free_intervals = [
        _build_participant_free_intervals(
            participant_user_id=participant_user_id,
            window_start_at=window_start_at,
            window_end_at=window_end_at,
            availability_blocks=availability_blocks,
            routine_blocks=routine_blocks,
            tasks=tasks,
        )
        for participant_user_id in participant_user_ids
    ]

    common_intervals = participant_free_intervals[0]
    for next_participant_intervals in participant_free_intervals[1:]:
        common_intervals = _intersect_intervals(
            common_intervals,
            next_participant_intervals,
        )
        if not common_intervals:
            break

    for interval_start_at, interval_end_at in common_intervals:
        candidate_end_at = interval_start_at + minimum_duration
        if candidate_end_at <= interval_end_at:
            return interval_start_at, candidate_end_at, "found"

    fallback_start_at = window_start_at
    fallback_end_at = window_start_at + minimum_duration
    return fallback_start_at, fallback_end_at, "no_overlap"
