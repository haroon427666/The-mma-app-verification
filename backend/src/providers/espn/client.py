"""
ESPN HTTP Client.

A production-grade async HTTP client for the ESPN API with:
- Token bucket rate limiting (respects ESPN's rate limits)
- Exponential backoff retry (429, 5xx)
- Circuit breaker (stops calling a failing API)
- Configurable timeouts
- Structured logging of every API call
- Automatic pagination (yields pages as async generator)

This is the ONLY module that makes HTTP calls to ESPN. Every other module
in the provider layer works with already-fetched data.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator

import httpx

from src.providers.espn.config import ESPNClientConfig

logger = logging.getLogger(__name__)


# ── Circuit Breaker ────────────────────────────────────────────────────────────


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation — requests pass through
    OPEN = "open"  # Failing — requests are rejected immediately
    HALF_OPEN = "half_open"  # Testing recovery — one probe request allowed


@dataclass
class CircuitBreaker:
    """Prevents cascading failures by stopping calls to a failing API."""

    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def _transition(self) -> None:
        now = time.monotonic()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: OPEN → HALF_OPEN (recovery attempt)")

    async def before_call(self) -> None:
        """Called before each HTTP request. Raises if circuit is open."""
        async with self._lock:
            await self._transition()
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker is OPEN. "
                    f"Retry in {self.recovery_timeout - (time.monotonic() - self.last_failure_time):.0f}s"
                )

    async def on_success(self) -> None:
        """Called after a successful HTTP response."""
        async with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info("Circuit breaker: HALF_OPEN → CLOSED (recovered)")

    async def on_failure(self) -> None:
        """Called after a failed HTTP response or exception."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.monotonic()
            if (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.failure_threshold
            ):
                self.state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker: CLOSED → OPEN "
                    f"({self.failure_count} consecutive failures)"
                )
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker: HALF_OPEN → OPEN (probe failed)")


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open and a request is attempted."""
    pass


# ── Rate Limiter (Token Bucket) ────────────────────────────────────────────────


@dataclass
class TokenBucket:
    """Token bucket rate limiter — allows bursts up to `burst_size`, then
    enforces `rate` tokens per second."""

    rate: float  # tokens per second
    burst_size: int
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.monotonic)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.tokens = float(self.burst_size)

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(float(self.burst_size), self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1.0:
                wait = (1.0 - self.tokens) / self.rate
                self.tokens = 0.0
                # Release lock while waiting
                self._lock.release()
                await asyncio.sleep(wait)
                await self._lock.acquire()
                # Recheck after waiting
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(
                    float(self.burst_size), self.tokens + elapsed * self.rate
                )
                self.last_refill = now

            self.tokens -= 1.0


# ── HTTP Client ────────────────────────────────────────────────────────────────


@dataclass
class ESPNClient:
    """Async HTTP client for the ESPN API.

    Usage:
        client = ESPNClient(config=ESPNClientConfig())
        data = await client.get("/leagues/9")
        # Or use the paginated generator:
        async for page in client.paginate("/athletes", params={"limit": 100}):
            for athlete in page["items"]:
                ...
    """

    config: ESPNClientConfig = field(default_factory=ESPNClientConfig)
    _http: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
    _rate_limiter: TokenBucket = field(init=False, repr=False)
    _circuit_breaker: CircuitBreaker = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rate_limiter = TokenBucket(
            rate=self.config.rate_limit_per_second,
            burst_size=self.config.burst_size,
        )
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery,
        )

    async def __aenter__(self) -> "ESPNClient":
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def start(self) -> None:
        """Initialize the HTTP client. Call before making requests."""
        if self._http is None:
            self._http = httpx.AsyncClient(
                base_url=self.config.base_url,
                timeout=httpx.Timeout(
                    connect=self.config.connect_timeout,
                    read=self.config.request_timeout,
                    write=self.config.request_timeout,
                    pool=self.config.request_timeout,
                ),
                headers={"User-Agent": self.config.user_agent},
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                ),
            )

    async def close(self) -> None:
        """Close the HTTP client. Call when done."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    # ── Core Request Methods ────────────────────────────────────────────────

    async def request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make an HTTP request with rate limiting, retry, and circuit breaker.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path (appended to base_url)
            **kwargs: Passed to httpx.AsyncClient.request()

        Returns:
            httpx.Response

        Raises:
            CircuitBreakerOpenError: If the circuit breaker is open.
            httpx.HTTPError: After all retries are exhausted.
        """
        if self._http is None:
            raise RuntimeError("ESPNClient not started. Call `await client.start()` first.")

        await self._circuit_breaker.before_call()

        for attempt in range(self.config.max_retries + 1):
            try:
                await self._rate_limiter.acquire()

                start_time = time.monotonic()
                response = await self._http.request(method, path, **kwargs)
                elapsed_ms = (time.monotonic() - start_time) * 1000

                logger.debug(
                    "ESPN API call",
                    extra={
                        "method": method,
                        "path": path,
                        "status": response.status_code,
                        "elapsed_ms": round(elapsed_ms, 2),
                        "attempt": attempt + 1,
                    },
                )

                # Success: 2xx
                if response.is_success:
                    await self._circuit_breaker.on_success()
                    return response

                # Rate limited: 429
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait = (
                        float(retry_after)
                        if retry_after
                        else self.config.retry_backoff_base ** attempt
                    )
                    logger.warning(
                        f"ESPN rate limited (429). Waiting {wait:.1f}s (attempt {attempt + 1})"
                    )
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(wait)
                        continue
                    else:
                        await self._circuit_breaker.on_failure()
                        response.raise_for_status()

                # Server error: 5xx — retryable
                if response.status_code in self.config.retry_status_codes:
                    wait = self.config.retry_backoff_base ** attempt
                    logger.warning(
                        f"ESPN server error ({response.status_code}). "
                        f"Retrying in {wait:.1f}s (attempt {attempt + 1})"
                    )
                    if attempt < self.config.max_retries:
                        await asyncio.sleep(wait)
                        continue
                    else:
                        await self._circuit_breaker.on_failure()
                        response.raise_for_status()

                # Client error: 4xx (except 429) — not retryable
                await self._circuit_breaker.on_failure()
                response.raise_for_status()

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                wait = self.config.retry_backoff_base ** attempt
                logger.warning(
                    f"ESPN connection error: {e}. Retrying in {wait:.1f}s (attempt {attempt + 1})"
                )
                if attempt < self.config.max_retries:
                    await asyncio.sleep(wait)
                    continue
                await self._circuit_breaker.on_failure()
                raise

        # Should not reach here — final fallback
        await self._circuit_breaker.on_failure()
        raise httpx.HTTPError(f"All {self.config.max_retries + 1} attempts failed for {method} {path}")

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        """GET request (convenience wrapper)."""
        return await self.request("GET", path, **kwargs)

    # ── JSON Helpers ────────────────────────────────────────────────────────

    async def get_json(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """GET request, returns parsed JSON."""
        response = await self.get(path, **kwargs)
        return response.json()

    # ── Reference Resolution ────────────────────────────────────────────────

    async def resolve_ref(self, ref_url: str) -> dict[str, Any]:
        """Resolve an ESPN $ref link to its full JSON payload.

        ESPN's API uses $ref extensively — instead of embedding data,
        it returns URLs like:
            {"$ref": "https://sports.core.api.espn.com/v2/sports/mma/athletes/12345"}

        This method follows that URL and returns the full resolved JSON.
        Results are NOT cached here — caching is the responsibility of
        the sync engine's reference resolver (see reference.py).
        """
        # Remove base_url prefix if present, since the client already has it
        if ref_url.startswith(self.config.base_url):
            path = ref_url[len(self.config.base_url):]
        else:
            path = ref_url

        return await self.get_json(path)

    # ── Pagination ──────────────────────────────────────────────────────────

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate through ESPN API results.

        ESPN returns paginated results with:
        {
            "count": 100,
            "pageIndex": 0,
            "pageCount": 5,
            "items": [...]
        }

        This generator yields one page at a time (the full JSON for each page).

        Args:
            path: API path
            params: Query parameters
            limit: Maximum items to yield (None = all pages)

        Yields:
            Full JSON response for each page.
        """
        if params is None:
            params = {}
        params.setdefault("limit", self.config.page_limit)
        params.setdefault("offset", 0)

        total_yielded = 0

        while True:
            response = await self.get_json(path, params=params)
            items = response.get("items", [])
            if not items:
                break

            yield response

            total_yielded += len(items)
            if limit is not None and total_yielded >= limit:
                break

            # Check if there are more pages
            page_index = response.get("pageIndex", 0)
            page_count = response.get("pageCount", 1)
            if page_index + 1 >= page_count:
                break

            params["offset"] = (page_index + 1) * params["limit"]

    # ── Health Check ────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Quick check: is the ESPN API reachable?"""
        try:
            response = await self.get("/leagues", params={"limit": 1})
            return response.is_success
        except Exception:
            return False
