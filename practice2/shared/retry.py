import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from shared.config import RETRY_BASE_DELAY_SEC, RETRY_MAX_ATTEMPTS

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def async_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = RETRY_MAX_ATTEMPTS,
    base_delay: float = RETRY_BASE_DELAY_SEC,
    retryable: tuple[type[BaseException], ...] = (Exception,),
) -> T:
    last_error: BaseException | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except retryable as exc:
            last_error = exc
            if attempt >= max_attempts:
                logger.error("Operation failed after %s attempts: %s", max_attempts, exc)
                raise
            delay = base_delay * (2 ** (attempt - 1))
            logger.warning(
                "Attempt %s/%s failed (%s), retry in %.2fs",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            await asyncio.sleep(delay)
    assert last_error is not None
    raise last_error
