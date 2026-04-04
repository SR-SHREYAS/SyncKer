from pydantic import BaseModel
import pytest

from app.core.exceptions import BadRequestError
from app.utils.request_validation import (
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_participant_ids_list,
    ensure_payload_has_updates,
    ensure_positive_id,
)


class _UpdatePayload(BaseModel):
    name: str | None = None
    priority: int | None = None


def test_ensure_positive_id_rejects_non_positive() -> None:
    with pytest.raises(BadRequestError):
        ensure_positive_id(0, field_name="user_id")


def test_ensure_positive_id_allows_positive_value() -> None:
    ensure_positive_id(1, field_name="user_id")


def test_ensure_non_empty_text_rejects_whitespace() -> None:
    with pytest.raises(BadRequestError):
        ensure_non_empty_text("   ", field_name="title")


def test_ensure_non_empty_text_allows_non_empty_value() -> None:
    ensure_non_empty_text("Title", field_name="title")


def test_ensure_optional_non_empty_text_allows_none() -> None:
    ensure_optional_non_empty_text(None, field_name="description")


def test_ensure_optional_non_empty_text_rejects_empty_string() -> None:
    with pytest.raises(BadRequestError):
        ensure_optional_non_empty_text("", field_name="description")


def test_ensure_optional_non_empty_text_rejects_whitespace_only() -> None:
    with pytest.raises(BadRequestError):
        ensure_optional_non_empty_text("   ", field_name="description")


def test_ensure_payload_has_updates_rejects_empty_patch() -> None:
    with pytest.raises(BadRequestError):
        ensure_payload_has_updates(_UpdatePayload(), field_names=("name", "priority"))


def test_ensure_payload_has_updates_accepts_when_any_field_is_set() -> None:
    ensure_payload_has_updates(
        _UpdatePayload(name="Updated Task Name"),
        field_names=("name", "priority"),
    )


def test_ensure_participant_ids_list_rejects_duplicates() -> None:
    with pytest.raises(BadRequestError):
        ensure_participant_ids_list([1, 2, 2], context="suggestion generation")


def test_ensure_participant_ids_list_accepts_valid_unique_positive_values() -> None:
    ensure_participant_ids_list([1, 2, 3], context="suggestion generation")


def test_ensure_participant_ids_list_rejects_too_few_participants() -> None:
    with pytest.raises(BadRequestError):
        ensure_participant_ids_list([1], context="suggestion generation")


def test_ensure_participant_ids_list_rejects_non_positive_ids() -> None:
    with pytest.raises(BadRequestError):
        ensure_participant_ids_list([1, -2], context="suggestion generation")
