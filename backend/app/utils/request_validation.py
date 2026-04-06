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


def ensure_optional_non_empty_text(value: str | None, *, field_name: str) -> None:
    """Ensure optional string fields are non-empty when provided."""
    if value is None:
        return
    ensure_non_empty_text(value, field_name=field_name)


def normalize_required_text(value: object, *, field_name: str) -> object:
    """Trim required text and reject empty values.

    Returns non-string values unchanged so schema type validators can handle them.
    """
    if not isinstance(value, str):
        return value
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must not be empty")
    return normalized_value


def normalize_optional_text(value: object, *, field_name: str) -> object:
    """Trim optional text when provided and reject empty values.

    Returns non-string values unchanged so schema type validators can handle them.
    """
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must not be empty")
    return normalized_value


def normalize_optional_text_to_none(value: object) -> object:
    """Strip optional text and collapse empty/blank values to None."""
    if value is None:
        return None
    if not isinstance(value, str):
        return value
    normalized_value = value.strip()
    if not normalized_value:
        return None
    return normalized_value


def ensure_payload_has_updates(payload: BaseModel, *, field_names: tuple[str, ...]) -> None:
    """Ensure update requests include at least one field to modify."""
    if not any(getattr(payload, field_name) is not None for field_name in field_names):
        raise BadRequestError(
            "empty request body: provide at least one field to update"
        )


def ensure_optional_id_is_positive(value: int | None, *, field_name: str) -> None:
    """Ensure optional id fields are positive when provided."""
    if value is not None and value <= 0:
        raise BadRequestError(f"{field_name} must be a positive integer")


def ensure_time_range(*, start_time: time | None, end_time: time | None, context: str) -> None:
    """Ensure time range updates do not invert start and end times."""
    if start_time is not None and end_time is not None and start_time >= end_time:
        raise BadRequestError(
            f"invalid {context}: start_time must be earlier than end_time"
        )


def ensure_distinct_ids(left_value: int, right_value: int, *, context: str) -> None:
    """Ensure two ids in one request are not the same when not allowed."""
    if left_value == right_value:
        raise BadRequestError(f"invalid {context}: both ids cannot be the same")


def ensure_participant_ids_list(participant_user_ids: list[int], *, context: str) -> None:
    """Ensure participant list is usable for scheduling logic."""
    if len(participant_user_ids) < 2:
        raise BadRequestError(
            f"invalid {context}: at least two participants are required"
        )
    if len(set(participant_user_ids)) != len(participant_user_ids):
        raise BadRequestError(f"invalid {context}: participant ids must be unique")
    for participant_user_id in participant_user_ids:
        ensure_positive_id(participant_user_id, field_name="participant_user_ids[]")


def ensure_id_in_list(
    *,
    value: int,
    values: list[int],
    field_name: str,
    context: str,
    container_field_name: str = "participant_user_ids",
) -> None:
    """Ensure one id exists inside a related id list."""
    if value not in values:
        raise BadRequestError(
            f"invalid {context}: {field_name} must be part of {container_field_name}"
        )


def ensure_model_fields_present(payload: BaseModel, *, fields: tuple[str, ...], context: str) -> None:
    """Ensure a create payload has required meaningful values after parsing."""
    for field_name in fields:
        value: Any = getattr(payload, field_name)
        if value is None:
            raise BadRequestError(f"invalid {context}: {field_name} is required")
