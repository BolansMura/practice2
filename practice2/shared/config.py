import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
STREAM_NAME = os.getenv("TASK_STREAM", "tasks:stream")
CONSUMER_GROUP = os.getenv("CONSUMER_GROUP", "workers")
RESULT_PREFIX = "result:"
RESULT_TTL_SECONDS = int(os.getenv("RESULT_TTL_SECONDS", "3600"))

RETRY_MAX_ATTEMPTS = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
RETRY_BASE_DELAY_SEC = float(os.getenv("RETRY_BASE_DELAY_SEC", "0.1"))
