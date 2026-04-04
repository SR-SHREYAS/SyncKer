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


def test_ensure_non_empty_text_rejects_whitespace() -> None:
    with pytest.raises(BadRequestError):
        ensure_non_empty_text("   ", field_name="title")


def test_ensure_optional_non_empty_text_allows_none() -> None:
    ensure_optional_non_empty_text(None, field_name="description")


def test_ensure_payload_has_updates_rejects_empty_patch() -> None:
    with pytest.raises(BadRequestError):
        ensure_payload_has_updates(_UpdatePayload(), field_names=("name", "priority"))


def test_ensure_participant_ids_list_rejects_duplicates() -> None:
    with pytest.raises(BadRequestError):
        ensure_participant_ids_list([1, 2, 2], context="suggestion generation")
