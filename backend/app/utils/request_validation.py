"""Reusable API request guards for handler layer checks."""

from datetime import time
from typing import Any

from pydantic import BaseModel

from app.core.exceptions import BadRequestError


def ensure_positive_id(value: int, *, field_name: str) -> None:
    """Ensure route/path ids are valid positive integers."""
    if value <= 0:
        raise BadRequestError(f"{field_name} must be a positive integer")


def ensure_non_empty_text(value: str, *, field_name: str) -> None:
    """Ensure string request fields are not blank or whitespace only."""
    if not value.strip():
        raise BadRequestError(f"{field_name} cannot be empty")


def ensure_payload_has_updates(payload: BaseModel, *, field_names: tuple[str, ...]) -> None:
    """Ensure update requests include at least one field to modify."""
    if not any(getattr(payload, field_name) is not None for field_name in field_names):
        raise BadRequestError("empty request body: provide at least one field to update")


def ensure_optional_id_is_positive(value: int | None, *, field_name: str) -> None:
    """Ensure optional id fields are positive when provided."""
    if value is not None and value <= 0:
        raise BadRequestError(f"{field_name} must be a positive integer")


def ensure_time_range(*, start_time: time | None, end_time: time | None, context: str) -> None:
    """Ensure time range updates do not invert start and end times."""
    if start_time is not None and end_time is not None and start_time >= end_time:
        raise BadRequestError(f"invalid {context}: start_time must be earlier than end_time")


def ensure_distinct_ids(left_value: int, right_value: int, *, context: str) -> None:
    """Ensure two ids in one request are not the same when not allowed."""
    if left_value == right_value:
        raise BadRequestError(f"invalid {context}: both ids cannot be the same")


def ensure_model_fields_present(payload: BaseModel, *, fields: tuple[str, ...], context: str) -> None:
    """Ensure a create payload has required meaningful values after parsing."""
    for field_name in fields:
        value: Any = getattr(payload, field_name)
        if value is None:
            raise BadRequestError(f"invalid {context}: {field_name} is required")
