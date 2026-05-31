import asyncio
import json
import logging
import random
import signal
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import redis.asyncio as redis
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import ValidationError

from shared.config import (
    CONSUMER_GROUP,
    REDIS_URL,
    RESULT_TTL_SECONDS,
    STREAM_NAME,
)
from shared.idempotency import result_key
from shared.metrics import (
    WORKER_RETRIES,
    WORKER_TASK_DURATION,
    WORKER_TASKS_PROCESSED,
)
from shared.models import ExecuteBody, TaskResult
from shared.retry import async_retry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

CONSUMER_NAME = "worker-1"
_running = True
TRANSIENT_ERRORS = (RuntimeError, ConnectionError, TimeoutError)


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(generate_latest())
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        return


def start_metrics_server(port: int = 9090) -> HTTPServer:
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


async def ensure_consumer_group(client: redis.Redis) -> None:
    try:
        await client.xgroup_create(STREAM_NAME, CONSUMER_GROUP, id="0", mkstream=True)
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def run_business_logic(body: ExecuteBody) -> dict:
    """Имитация бизнес-логики с возможной транзиентной ошибкой (10%)."""
    if random.random() < 0.1:
        raise RuntimeError("Simulated transient processing error")

    delay_ms = random.randint(50, 200)
    await asyncio.sleep(delay_ms / 1000.0)

    return {
        "processed": True,
        "action": body.action.value,
        "delay_ms": delay_ms,
        "echo": body.model_dump(mode="json"),
    }


async def process_task(
    client: redis.Redis,
    message_id: str,
    fields: dict[str, str],
) -> None:
    start = time.perf_counter()
    idempotency_key = fields.get("idempotency_key", "")
    raw_payload = fields.get("payload", "{}")

    try:
        payload_dict = json.loads(raw_payload)
        body = ExecuteBody.model_validate(payload_dict)
    except (json.JSONDecodeError, ValidationError) as exc:
        logger.error("Invalid task payload for %s: %s", idempotency_key, exc)
        error_result = TaskResult(
            status="failed",
            idempotency_key=idempotency_key,
            error=f"Invalid payload: {exc}",
        )
        await client.set(
            result_key(idempotency_key),
            error_result.model_dump_json(),
            ex=RESULT_TTL_SECONDS,
        )
        await client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)
        WORKER_TASKS_PROCESSED.labels(status="invalid").inc()
        return

    try:
        attempt = 0

        async def _run() -> dict:
            nonlocal attempt
            attempt += 1
            if attempt > 1:
                WORKER_RETRIES.inc()
            return await run_business_logic(body)

        result_data = await async_retry(_run, retryable=TRANSIENT_ERRORS)
        task_result = TaskResult(
            status="completed",
            idempotency_key=idempotency_key,
            result=result_data,
        )
        await client.set(
            result_key(idempotency_key),
            task_result.model_dump_json(),
            ex=RESULT_TTL_SECONDS,
        )
        await client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)
        WORKER_TASKS_PROCESSED.labels(status="success").inc()
    except TRANSIENT_ERRORS as exc:
        logger.error("Task %s failed after retries: %s", idempotency_key, exc)
        error_result = TaskResult(
            status="failed",
            idempotency_key=idempotency_key,
            error=str(exc),
        )
        await client.set(
            result_key(idempotency_key),
            error_result.model_dump_json(),
            ex=RESULT_TTL_SECONDS,
        )
        await client.xack(STREAM_NAME, CONSUMER_GROUP, message_id)
        WORKER_TASKS_PROCESSED.labels(status="error").inc()
    except redis.RedisError:
        WORKER_TASKS_PROCESSED.labels(status="error").inc()
        raise
    finally:
        WORKER_TASK_DURATION.observe(time.perf_counter() - start)


async def worker_loop() -> None:
    client = redis.from_url(REDIS_URL, decode_responses=True)
    await ensure_consumer_group(client)

    while _running:
        try:
            entries = await client.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={STREAM_NAME: ">"},
                count=1,
                block=5000,
            )
        except redis.RedisError as exc:
            logger.warning("Redis read error: %s", exc)
            await asyncio.sleep(1)
            continue

        if not entries:
            continue

        for _stream, messages in entries:
            for message_id, fields in messages:
                await process_task(client, message_id, fields)

    await client.aclose()


def shutdown_handler(*_args: object) -> None:
    global _running
    _running = False


def main() -> None:
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    start_metrics_server(int(__import__("os").getenv("WORKER_METRICS_PORT", "9090")))
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()
