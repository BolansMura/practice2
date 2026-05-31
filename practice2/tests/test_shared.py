import pytest
from pydantic import ValidationError

from shared.idempotency import is_valid_idempotency_key
from shared.models import ExecuteBody


def test_idempotency_key_uuid_valid() -> None:
    assert is_valid_idempotency_key("550e8400-e29b-41d4-a716-446655440000")


def test_idempotency_key_invalid() -> None:
    assert not is_valid_idempotency_key("x")


def test_execute_body_forbids_extra_fields() -> None:
    with pytest.raises(ValidationError):
        ExecuteBody.model_validate({"action": "process", "data": {}, "extra": 1})
