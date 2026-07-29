import time
from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


@dataclass
class CacheEntry[T]:
    value: T
    expires_at: float


class TTLCache[T]:
    """Small in-process cache for a single-node deployment."""

    def __init__(self) -> None:
        self._values: dict[str, CacheEntry[T]] = {}
        self._lock = Lock()

    def get(self, key: str) -> T | None:
        with self._lock:
            entry = self._values.get(key)
            if entry is None or entry.expires_at < time.monotonic():
                self._values.pop(key, None)
                return None
            return entry.value

    def set(self, key: str, value: T, ttl_seconds: int = 300) -> None:
        with self._lock:
            self._values[key] = CacheEntry(value, time.monotonic() + ttl_seconds)


class BackgroundJobs:
    """Bounded local worker pool; replaceable by a durable queue for multi-node releases."""

    def __init__(self, workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="careerpilot")
        self._jobs: dict[str, Future[object]] = {}

    def submit[T](self, operation: Callable[..., T], *args: object, **kwargs: object) -> str:
        job_id = str(uuid4())
        self._jobs[job_id] = self._executor.submit(operation, *args, **kwargs)
        return job_id

    def status(self, job_id: str) -> str:
        job = self._jobs.get(job_id)
        if job is None:
            return "missing"
        if job.cancelled():
            return "cancelled"
        if job.done():
            return "failed" if job.exception() else "completed"
        return "running"


cache: TTLCache[object] = TTLCache()
background_jobs = BackgroundJobs()
