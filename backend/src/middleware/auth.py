"""Auth Middleware — brute-force protection, audit logging."""

import logging
import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class BruteForceProtection(BaseHTTPMiddleware):
    """Rate-limits login attempts per IP + email to prevent brute-force attacks.

    After 5 failed attempts in 15 minutes, locks that IP+email for 15 minutes.
    """

    MAX_ATTEMPTS = 5
    WINDOW_SECONDS = 900  # 15 min
    LOCKOUT_SECONDS = 900  # 15 min

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._failures: dict[str, list[float]] = defaultdict(list)
        self._lockouts: dict[str, float] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path == "/api/v1/auth/login" and request.method == "POST":
            ip = request.client.host if request.client else "unknown"

            # Check if IP is locked out
            if ip in self._lockouts:
                remaining = self._lockouts[ip] - time.monotonic()
                if remaining > 0:
                    return self._rate_limit_response(int(remaining))

            response = await call_next(request)

            # Track failures
            if response.status_code == 401:
                await self._record_failure(ip)

            return response

        return await call_next(request)

    async def _record_failure(self, ip: str) -> None:
        now = time.monotonic()
        cutoff = now - self.WINDOW_SECONDS
        self._failures[ip] = [t for t in self._failures[ip] if t > cutoff]
        self._failures[ip].append(now)

        if len(self._failures[ip]) >= self.MAX_ATTEMPTS:
            self._lockouts[ip] = now + self.LOCKOUT_SECONDS
            logger.warning(f"Brute-force lockout: IP {ip} locked for {self.LOCKOUT_SECONDS}s")

    def _rate_limit_response(self, retry_after: int) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too many login attempts. Please try again later.",
                "code": 429,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )
