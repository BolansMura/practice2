from collections import defaultdict
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from gateway.main import app


class FakeRedis:
    def __init__(self) -> None:
        self._kv: dict[str, str] = {}
        self._streams: dict[str, list[tuple[str, dict[str, str]]]] = defaultdict(list)
        self._stream_seq = 0
        self.get_always_fails = False
        self.fail_next_xadd = False

    async def get(self, key: str) -> str | None:
        if self.get_always_fails:
            import redis.asyncio as redis

            raise redis.ConnectionError("simulated")
        return self._kv.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._kv[key] = value
        return True

    async def xadd(self, name: str, fields: dict[str, str]) -> str:
        if self.fail_next_xadd:
            self.fail_next_xadd = False
            import redis.asyncio as redis

            raise redis.ConnectionError("simulated")
        self._stream_seq += 1
        message_id = f"{self._stream_seq}-0"
        self._streams[name].append((message_id, fields))
        return message_id

    async def xack(self, *args: object, **kwargs: object) -> int:
        return 1

    async def aclose(self) -> None:
        pass


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
async def client(fake_redis: FakeRedis) -> AsyncClient:
    async def _get_redis() -> FakeRedis:
        return fake_redis

    with patch("gateway.main.get_redis", new=_get_redis):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
