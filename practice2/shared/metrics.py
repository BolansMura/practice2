from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
CACHE_HITS = Counter("cache_hits_total", "Idempotency cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Idempotency cache misses")

WORKER_TASKS_PROCESSED = Counter(
    "worker_tasks_processed_total",
    "Tasks processed by worker",
    ["status"],
)
WORKER_TASK_DURATION = Histogram(
    "worker_task_duration_seconds",
    "Worker task processing duration",
    buckets=(0.05, 0.1, 0.15, 0.2, 0.25, 0.5, 1.0),
)
WORKER_RETRIES = Counter("worker_task_retries_total", "Worker task retry attempts")
