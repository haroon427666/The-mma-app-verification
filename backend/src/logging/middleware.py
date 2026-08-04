"""Request context middleware — injects correlation IDs into every request."""

import logging
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.logging.config import set_request_id

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Injects X-Request-ID and logs every request with duration.

    Headers set:
        X-Request-ID → client-provided or generated UUID
        X-Correlation-ID → inherited from incoming or same as request ID
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        # Extract or generate request ID
        rid = request.headers.get("X-Request-ID") or set_request_id()
        cid = request.headers.get("X-Correlation-ID", rid)

        set_request_id(rid)

        start = time.monotonic()
        response: Response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        # Echo back correlation headers
        response.headers["X-Request-ID"] = rid
        response.headers["X-Correlation-ID"] = cid

        # Log request
        logger.info(
            f"{request.method} {request.url.path} → {response.status_code}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        # Prometheus API metrics (safe — no-ops until setup() runs)
        try:
            from src.monitoring.scheduler_metrics import SchedulerMetricsCollector
            SchedulerMetricsCollector().record_api_request(
                request.method, request.url.path, response.status_code, duration_ms,
            )
        except Exception:
            pass

        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs security-relevant actions: login, logout, admin writes."""

    AUDIT_PATHS = {
        "/api/v1/auth/login": "login",
        "/api/v1/auth/logout": "logout",
        "/api/v1/auth/register": "register",
        "/api/v1/auth/change-password": "password_change",
        "/api/sync/full": "sync_trigger",
        "/api/sync": "sync_trigger",
    }

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response: Response = await call_next(request)

        action = self.AUDIT_PATHS.get(request.url.path)
        if action is None:
            # Partial match for /sync/* paths
            for prefix, act in self.AUDIT_PATHS.items():
                if request.url.path.startswith(prefix):
                    action = act
                    break

        if action:
            logger.info(
                f"AUDIT: {action}",
                extra={
                    "action": action,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "client_ip": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("User-Agent", "")[:100],
                },
            )

        return response
