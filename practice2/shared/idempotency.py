import re

_IDEMPOTENCY_KEY_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    r"|^[a-zA-Z0-9_-]{8,128}$"
)


def is_valid_idempotency_key(key: str) -> bool:
    if not key or not key.strip():
        return False
    return bool(_IDEMPOTENCY_KEY_PATTERN.match(key.strip()))


def result_key(idempotency_key: str) -> str:
    from shared.config import RESULT_PREFIX

    return f"{RESULT_PREFIX}{idempotency_key.strip()}"
