import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from careerpilot.core.config import Settings
from careerpilot.core.security import decode_access_token

logger = structlog.get_logger()
metrics = {"requests_total": 0, "errors_total": 0, "duration_ms_total": 0.0}


class OperationsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests: int, window_seconds: int, settings: Settings) -> None:
        super().__init__(app)
        self.requests = requests
        self.window_seconds = window_seconds
        self.settings = settings
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid4()))
        request.state.request_id = request_id
        public_paths = {
            "/health",
            "/ready",
            "/diagnostics",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        }
        if self.settings.auth_enabled and request.url.path not in public_paths:
            authorization = request.headers.get("authorization", "")
            if not authorization.startswith("Bearer "):
                return Response(
                    '{"detail":"Authentication required"}',
                    status_code=401,
                    media_type="application/json",
                    headers={"X-Request-ID": request_id},
                )
            try:
                request.state.principal = decode_access_token(
                    authorization.removeprefix("Bearer "), self.settings
                )
            except Exception:
                return Response(
                    '{"detail":"Invalid token"}',
                    status_code=401,
                    media_type="application/json",
                    headers={"X-Request-ID": request_id},
                )
        now = time.monotonic()
        key = request.client.host if request.client else "unknown"
        hits = self.hits[key]
        while hits and hits[0] < now - self.window_seconds:
            hits.popleft()
        if len(hits) >= self.requests and request.url.path not in public_paths:
            return Response(
                '{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds), "X-Request-ID": request_id},
            )
        hits.append(now)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            metrics["errors_total"] += 1
            logger.exception("request_failed", request_id=request_id, path=request.url.path)
            raise
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'; base-uri 'self'"
        )
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        metrics["requests_total"] += 1
        metrics["duration_ms_total"] += duration_ms
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
        )
        return response
