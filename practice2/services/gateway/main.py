import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from gateway.redis_client import close_redis, get_redis
from shared.config import STREAM_NAME
from shared.idempotency import is_valid_idempotency_key, result_key
from shared.metrics import (
    BUSINESS_TASKS_ACCEPTED,
    CACHE_HITS,
    CACHE_MISSES,
    HTTP_REQUEST_DURATION,
    HTTP_REQUESTS,
)
from shared.models import AcceptedResponse, ExecuteBody
from shared.retry import async_retry

logger = logging.getLogger(__name__)

REDIS_RETRYABLE = (redis.ConnectionError, redis.TimeoutError, redis.RedisError)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    await close_redis()


app = FastAPI(
    title="API Gateway",
    description="Идемпотентный шлюз с Redis Streams",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


async def _redis_get(client: redis.Redis, key: str) -> str | None:
    return await client.get(key)


async def _redis_xadd(client: redis.Redis, fields: dict[str, str]) -> str:
    return await client.xadd(STREAM_NAME, fields)


@app.post(
    "/execute",
    responses={
        200: {"description": "Кэшированный результат"},
        202: {"description": "Задача принята в очередь"},
        400: {"description": "Неверный запрос"},
        503: {"description": "Redis недоступен"},
    },
)
async def execute(
    body: ExecuteBody,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
) -> JSONResponse:
    start = time.perf_counter()
    endpoint = "/execute"
    method = "POST"

    try:
        if idempotency_key is None or not idempotency_key.strip():
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="400").inc()
            raise HTTPException(
                status_code=400,
                detail="Missing required header: Idempotency-Key",
            )

        key = idempotency_key.strip()
        if not is_valid_idempotency_key(key):
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="400").inc()
            raise HTTPException(
                status_code=400,
                detail="Invalid Idempotency-Key format",
            )

        try:
            redis_client = await get_redis()
            cached = await async_retry(
                lambda: _redis_get(redis_client, result_key(key)),
                retryable=REDIS_RETRYABLE,
            )
        except REDIS_RETRYABLE as exc:
            logger.exception("Redis unavailable on GET")
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="503").inc()
            raise HTTPException(status_code=503, detail="Redis service unavailable") from exc

        if cached:
            CACHE_HITS.inc()
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="200").inc()
            return JSONResponse(status_code=200, content=json.loads(cached))

        CACHE_MISSES.inc()
        payload = body.model_dump(mode="json")
        message = {
            "idempotency_key": key,
            "payload": json.dumps(payload),
        }
        try:
            await async_retry(
                lambda: _redis_xadd(redis_client, message),
                retryable=REDIS_RETRYABLE,
            )
        except REDIS_RETRYABLE as exc:
            logger.exception("Redis unavailable on XADD")
            HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="503").inc()
            raise HTTPException(status_code=503, detail="Redis service unavailable") from exc

        HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status="202").inc()
        BUSINESS_TASKS_ACCEPTED.labels(action=body.action.value).inc()
        response = AcceptedResponse(idempotency_key=key)
        return JSONResponse(status_code=202, content=response.model_dump())
    finally:
        HTTP_REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(
            time.perf_counter() - start
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    HTTP_REQUESTS.labels(method="POST", endpoint="/execute", status="422").inc()
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
