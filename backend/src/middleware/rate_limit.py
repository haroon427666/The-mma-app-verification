"""Rate limiting middleware — simple in-memory sliding window.

100 requests per minute per client IP (configurable).
"""

import time
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RateLimiter(BaseHTTPMiddleware):
    """Sliding window rate limiter per client IP."""

    def __init__(self, app: Any, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._clients: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.monotonic()

        # Remove expired entries
        cutoff = now - self.window
        self._clients[client_ip] = [t for t in self._clients.get(client_ip, []) if t > cutoff]

        if len(self._clients[client_ip]) >= self.max_requests:
            retry_after = int(self._clients[client_ip][0] + self.window - now)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry after {retry_after}s",
                headers={"Retry-After": str(retry_after)},
            )

        self._clients[client_ip].append(now)
        return await call_next(request)
