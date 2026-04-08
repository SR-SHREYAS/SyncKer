from pydantic import BaseModel
import pytest

from app.core.exceptions import BadRequestError
from app.utils.request_validation import (
    ensure_id_in_list,
    ensure_non_empty_text,
    ensure_optional_non_empty_text,
    ensure_participant_ids_list,
    ensure_payload_has_updates,
    ensure_positive_id,
    normalize_optional_text_to_none,
)


class _UpdatePayload(BaseModel):
    name: str | None = None
    priority: int | None = None


def test_ensure_positive_id_rejects_non_positive() -> None:
    with pytest.raises(BadRequestError):
        ensure_positive_id(0, field_name="user_id")


def test_ensure_positive_id_rejects_negative() -> None:
    with pytest.raises(BadRequestError):
        ensure_positive_id(-1, field_name="user_id")


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


def test_normalize_optional_text_to_none_with_none_returns_none() -> None:
    assert normalize_optional_text_to_none(None) is None


def test_normalize_optional_text_to_none_with_non_blank_string_returns_unchanged() -> (
    None
):
    assert normalize_optional_text_to_none("Some description") == "Some description"


def test_normalize_optional_text_to_none_with_empty_or_whitespace_returns_none() -> (
    None
):
    assert normalize_optional_text_to_none("") is None
    assert normalize_optional_text_to_none("   ") is None


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


def test_ensure_id_in_list_allows_present_value() -> None:
    ensure_id_in_list(
        value=5,
        values=[2, 5, 8],
        field_name="current_user_id",
        context="suggestion generation",
    )


def test_ensure_id_in_list_rejects_missing_value() -> None:
    with pytest.raises(BadRequestError):
        ensure_id_in_list(
            value=5,
            values=[2, 8],
            field_name="current_user_id",
            context="suggestion generation",
        )


def test_ensure_id_in_list_rejects_missing_value_with_custom_container_name() -> None:
    with pytest.raises(BadRequestError) as raised_error:
        ensure_id_in_list(
            value=7,
            values=[2, 8],
            field_name="actor_user_id",
            context="team assignment",
            container_field_name="assignee_user_ids",
        )
    assert "assignee_user_ids" in str(raised_error.value)
