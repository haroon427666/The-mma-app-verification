"""Exception Tracking Middleware — captures unhandled errors with full context."""

import logging
import traceback
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

RequestResponseEndpoint = Callable[[Request], Awaitable[Response]]


class ExceptionTrackerMiddleware(BaseHTTPMiddleware):
    """Catches unhandled exceptions, logs with full context, returns 500 JSON.

    Every error includes: request_id, user, endpoint, method, stack trace,
    query params, payload size — everything needed for debugging.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            error_id = str(uuid.uuid4())[:8]
            return await self._handle_exception(request, exc, error_id)

    async def _handle_exception(self, request: Request, exc: Exception, error_id: str) -> JSONResponse:
        # Collect full context
        body = None
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                body = body_bytes.decode()[:1000] if body_bytes else None
            except Exception:
                body = "[unreadable]"

        context = {
            "error_id": error_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", "")[:200],
            "body": body,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)[:500],
            "stack_trace": traceback.format_exc()[-2000:],
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Log with all context
        logger.error(
            f"Unhandled exception [{error_id}] {type(exc).__name__}: {str(exc)[:200]}",
            extra=context,
        )

        # Return safe error (don't leak stack trace to client)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "code": 500,
                "error_id": error_id,
                "message": "An unexpected error occurred. Reference this ID when contacting support.",
            },
        )


class ProfilerMiddleware(BaseHTTPMiddleware):
    """Records P50/P95/P99 latency percentiles for API endpoints.

    Stores last 1000 requests per endpoint for percentile calculation.
    """

    def __init__(self, app: Any, max_samples: int = 1000):
        super().__init__(app)
        self._samples: dict[str, list[float]] = {}
        self._max_samples = max_samples

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        import time
        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        key = f"{request.method}:{request.url.path}"
        if key not in self._samples:
            self._samples[key] = []
        samples = self._samples[key]
        samples.append(duration_ms)
        if len(samples) > self._max_samples:
            samples[:] = samples[-self._max_samples:]

        # Update Prometheus metric
        try:
            from src.monitoring.scheduler_metrics import SchedulerMetricsCollector
            SchedulerMetricsCollector().record_api_request(
                request.method, request.url.path, response.status_code, duration_ms,
            )
        except Exception:
            pass

        return response

    def get_percentiles(self, endpoint: str) -> dict[str, float | int]:
        """Get P50/P95/P99 for an endpoint."""
        samples = sorted(self._samples.get(endpoint, []))
        if not samples:
            return {"p50": 0, "p95": 0, "p99": 0, "count": 0}

        def percentile(data: list[float], p: float) -> float:
            k = (len(data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(data):
                return data[f] + c * (data[f + 1] - data[f])
            return data[f]

        return {
            "p50": round(percentile(samples, 0.50), 2),
            "p95": round(percentile(samples, 0.95), 2),
            "p99": round(percentile(samples, 0.99), 2),
            "count": len(samples),
        }

    def get_all_percentiles(self) -> dict[str, dict[str, float | int]]:
        return {ep: self.get_percentiles(ep) for ep in self._samples}
