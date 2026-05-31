import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    PROCESS = "process"
    VALIDATE = "validate"
    PING = "ping"


class ExecuteBody(BaseModel):
    """Тело запроса POST /execute."""

    action: ActionType = Field(..., description="Тип операции")
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Произвольные данные задачи (до 4 KB в JSON)",
    )

    model_config = {"extra": "forbid"}

    @field_validator("data")
    @classmethod
    def validate_data_size(cls, value: dict[str, Any]) -> dict[str, Any]:
        encoded = json.dumps(value, ensure_ascii=False)
        if len(encoded) > 4096:
            raise ValueError("Field 'data' must not exceed 4096 bytes when serialized to JSON")
        return value


class AcceptedResponse(BaseModel):
    status: str = "accepted"
    idempotency_key: str
    message: str = "Task queued for processing"


class TaskResult(BaseModel):
    status: str
    idempotency_key: str
    result: dict[str, Any] | None = None
    error: str | None = None
