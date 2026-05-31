import uuid

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_missing_idempotency_key(client: AsyncClient) -> None:
    response = await client.post(
        "/execute",
        json={"action": "process", "data": {}},
    )
    assert response.status_code == 400
    assert "Idempotency-Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_idempotency_key_format(client: AsyncClient) -> None:
    response = await client.post(
        "/execute",
        json={"action": "process", "data": {}},
        headers={"Idempotency-Key": "bad!"},
    )
    assert response.status_code == 400
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_successful_task_creation(client: AsyncClient, fake_redis) -> None:
    key = str(uuid.uuid4())
    response = await client.post(
        "/execute",
        json={"action": "process", "data": {"value": 42}},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["idempotency_key"] == key
    assert len(fake_redis._streams.get("tasks:stream", [])) == 1


@pytest.mark.asyncio
async def test_cache_hit_returns_stored_result(client: AsyncClient, fake_redis) -> None:
    import json

    from shared.idempotency import result_key

    key = str(uuid.uuid4())
    cached_payload = {
        "status": "completed",
        "idempotency_key": key,
        "result": {"processed": True},
    }
    fake_redis._kv[result_key(key)] = json.dumps(cached_payload)

    response = await client.post(
        "/execute",
        json={"action": "process", "data": {}},
        headers={"Idempotency-Key": key},
    )
    assert response.status_code == 200
    assert response.json() == cached_payload
    assert len(fake_redis._streams.get("tasks:stream", [])) == 0


@pytest.mark.asyncio
async def test_invalid_body_rejected(client: AsyncClient) -> None:
    response = await client.post(
        "/execute",
        json={"action": "unknown_action", "data": {}},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_redis_unavailable_returns_503(client: AsyncClient, fake_redis) -> None:
    fake_redis.get_always_fails = True
    response = await client.post(
        "/execute",
        json={"action": "process", "data": {}},
        headers={"Idempotency-Key": str(uuid.uuid4())},
    )
    assert response.status_code == 503
