import json
from unittest.mock import AsyncMock, patch

import pytest

from shared.idempotency import result_key
from shared.models import ActionType, ExecuteBody
from shared.retry import async_retry
from worker.main import MetricsHandler, process_task, run_business_logic


@pytest.mark.asyncio
async def test_async_retry_succeeds_after_transient_failures() -> None:
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("transient")
        return "ok"

    result = await async_retry(flaky, max_attempts=3, base_delay=0.01, retryable=(RuntimeError,))
    assert result == "ok"
    assert attempts == 3


@pytest.mark.asyncio
async def test_process_task_stores_completed_result(fake_redis) -> None:
    key = "550e8400-e29b-41d4-a716-446655440000"
    payload = ExecuteBody(action=ActionType.PROCESS, data={"x": 1})
    fields = {
        "idempotency_key": key,
        "payload": json.dumps(payload.model_dump(mode="json")),
    }

    with patch("worker.main.run_business_logic", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = {"processed": True, "delay_ms": 50}
        await process_task(fake_redis, "1-0", fields)

    stored = json.loads(fake_redis._kv[result_key(key)])
    assert stored["status"] == "completed"
    assert stored["result"]["processed"] is True


@pytest.mark.asyncio
async def test_process_task_invalid_payload_stores_failed(fake_redis) -> None:
    key = "550e8400-e29b-41d4-a716-446655440001"
    fields = {"idempotency_key": key, "payload": "not-json"}

    await process_task(fake_redis, "2-0", fields)

    stored = json.loads(fake_redis._kv[result_key(key)])
    assert stored["status"] == "failed"
    assert "Invalid payload" in stored["error"]


@pytest.mark.asyncio
async def test_run_business_logic_eventually_succeeds() -> None:
    with patch("worker.main.random.random", return_value=0.5):
        body = ExecuteBody(action=ActionType.PING, data={})
        result = await run_business_logic(body)
    assert result["processed"] is True
    assert result["action"] == "ping"


def test_worker_health_handler() -> None:
    from io import BytesIO

    handler = MetricsHandler.__new__(MetricsHandler)
    handler.path = "/health"
    handler.wfile = BytesIO()
    handler.status = None
    handler.send_response = lambda code: setattr(handler, "status", code)
    handler.send_header = lambda *_args, **_kwargs: None
    handler.end_headers = lambda: None
    handler.do_GET()
    assert handler.status == 200
    assert b'"status":"ok"' in handler.wfile.getvalue()
