from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.models.enums import TaskPriority, TaskStatus
from app.schemas.task import TaskCreateRequest, TaskUpdateRequest


def _build_task_create_payload() -> dict[str, object]:
    return {
        "title": "Prepare sprint review",
        "description": "Finalize and present status updates",
        "priority": TaskPriority.HIGH,
        "status": TaskStatus.PENDING,
        "estimated_minutes": 90,
        "deadline_at": None,
        "skill_id": None,
    }


def test_task_create_request_allows_valid_planned_time_range() -> None:
    now = datetime.now(UTC)
    payload = _build_task_create_payload()
    payload["planned_start_at"] = now
    payload["planned_end_at"] = now + timedelta(minutes=45)

    request = TaskCreateRequest(**payload)

    assert request.planned_start_at == payload["planned_start_at"]
    assert request.planned_end_at == payload["planned_end_at"]


def test_task_create_request_rejects_invalid_planned_time_range() -> None:
    now = datetime.now(UTC)
    payload = _build_task_create_payload()
    payload["planned_start_at"] = now
    payload["planned_end_at"] = now

    with pytest.raises(ValidationError):
        TaskCreateRequest(**payload)


def test_task_update_request_allows_single_planned_boundary() -> None:
    now = datetime.now(UTC)

    request = TaskUpdateRequest(planned_start_at=now)

    assert request.planned_start_at == now
    assert request.planned_end_at is None


def test_task_update_request_rejects_invalid_planned_time_range() -> None:
    now = datetime.now(UTC)

    with pytest.raises(ValidationError):
        TaskUpdateRequest(
            planned_start_at=now + timedelta(minutes=15),
            planned_end_at=now,
        )
