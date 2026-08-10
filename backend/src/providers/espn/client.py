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
import os
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self, cast
from urllib.parse import urlencode

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
        if (
            self.state == CircuitState.OPEN
            and now - self.last_failure_time >= self.recovery_timeout
        ):
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
        """Wait until a token is available, then consume it.

        Standard token bucket: refill under the lock, but sleep OUTSIDE the
        lock (so other tasks can refill meanwhile) and RE-CHECK after waking.

        The previous implementation released the lock mid-wait and refilled
        from a shared global timestamp — under concurrent waiters it leaked
        tokens: live benchmark showed 8 workers sustaining ~8.4 req/s with a
        3 req/s configured rate. The re-check loop below enforces the rate
        (1 token per 1/rate seconds, burst-capped).
        """
        while True:
            async with self._lock:
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(
                    float(self.burst_size), self.tokens + elapsed * self.rate
                )
                self.last_refill = now
                if self.tokens >= 1.0:
                    self.tokens -= 1.0
                    return
                wait = (1.0 - self.tokens) / self.rate
            await asyncio.sleep(wait)


# ── Response Cache ──────────────────────────────────────────────────────────────

@dataclass
class ResponseCache:
    """TTL response cache for ESPN API responses.

    Keyed by canonicalized URL (path + sorted query params). Size-bounded
    (evicts oldest entry when over cap). In-flight dedup is handled by the
    client (pending map), not here.
    """

    ttl_seconds: float = 300.0
    max_entries: int = 10_000
    _data: dict[str, tuple[float, dict[str, Any]]] = field(default_factory=dict, repr=False)

    def get(self, key: str) -> dict[str, Any] | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        inserted_at, payload = entry
        if time.monotonic() - inserted_at > self.ttl_seconds:
            self._data.pop(key, None)
            return None
        return payload

    def set(self, key: str, payload: dict[str, Any]) -> None:
        if len(self._data) >= self.max_entries:
            # Evict oldest entry (dict preserves insertion order)
            self._data.pop(next(iter(self._data)), None)
        self._data[key] = (time.monotonic(), payload)

    def clear(self) -> None:
        self._data.clear()

    @property
    def size(self) -> int:
        return len(self._data)


# ── HTTP Client ────────────────────────────────────────────────────────────────


def canonicalize(path: str, params: dict[str, Any] | None = None) -> str:
    """Canonical URL key for caching/dedup: path + sorted query params.

    Ensures {"limit": 100, "page": 1} and {"page": 1, "limit": 100} hit
    the same cache entry.
    """
    if not params:
        return path
    sorted_params = sorted((str(k), str(v)) for k, v in params.items())
    return f"{path}?{urlencode(sorted_params)}"


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

    Request efficiency (research-driven):
    - Response cache with URL canonicalization (TTL, size-bounded)
    - In-flight dedup: concurrent identical requests share one HTTP call
    - Bounded concurrency for parallel resolution (max_concurrency)
    - Token-bucket rate limiting at the measured safe envelope (2–5 rps)
    """

    config: ESPNClientConfig = field(default_factory=ESPNClientConfig)
    _http: httpx.AsyncClient | None = field(default=None, init=False, repr=False)
    _rate_limiter: TokenBucket = field(init=False, repr=False)
    _circuit_breaker: CircuitBreaker = field(init=False, repr=False)
    _cache: ResponseCache = field(init=False, repr=False)
    _pending: dict[str, asyncio.Future[dict[str, Any]]] = field(
        default_factory=dict, init=False, repr=False
    )
    _semaphore: asyncio.Semaphore = field(init=False, repr=False)

    # Metrics counters
    metrics: dict[str, int] = field(
        default_factory=lambda: {
            "requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "deduped": 0,
            "retries": 0,
            "rate_limited_429": 0,
            "server_errors_5xx": 0,
            "client_errors_4xx": 0,
            "network_errors": 0,
        },
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        self._rate_limiter = TokenBucket(
            rate=self.config.rate_limit_per_second,
            burst_size=self.config.burst_size,
        )
        self._circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.circuit_breaker_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery,
        )
        self._cache = ResponseCache(
            ttl_seconds=self.config.cache_ttl_seconds,
            max_entries=self.config.cache_max_entries,
        )
        self._semaphore = asyncio.Semaphore(self.config.max_concurrency)

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *args: object) -> None:
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

                self.metrics["requests"] += 1

                # Rate limited: 429
                if response.status_code == 429:
                    self.metrics["rate_limited_429"] += 1
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
                        self.metrics["retries"] += 1
                        await asyncio.sleep(wait)
                        continue
                    else:
                        await self._circuit_breaker.on_failure()
                        response.raise_for_status()

                # Server error: 5xx — retryable
                if response.status_code in self.config.retry_status_codes:
                    self.metrics["server_errors_5xx"] += 1
                    wait = self.config.retry_backoff_base ** attempt
                    logger.warning(
                        f"ESPN server error ({response.status_code}). "
                        f"Retrying in {wait:.1f}s (attempt {attempt + 1})"
                    )
                    if attempt < self.config.max_retries:
                        self.metrics["retries"] += 1
                        await asyncio.sleep(wait)
                        continue
                    else:
                        await self._circuit_breaker.on_failure()
                        response.raise_for_status()

                # Client error: 4xx (except 429) — not retryable. These are
                # permanent per-resource responses: ESPN returns 404 for
                # content-dependent surfaces (records/statistics/eventlog,
                # leagues without rankings) when no data exists. That is
                # NORMAL API behavior, NOT a system failure — it must not
                # trip the circuit breaker (research: never retry 400/404;
                # the breaker guards system-level failures only). Five such
                # 404s used to open the breaker and poison the whole run.
                self.metrics["client_errors_4xx"] += 1
                response.raise_for_status()

            except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError) as e:
                self.metrics["network_errors"] += 1
                wait = self.config.retry_backoff_base ** attempt
                logger.warning(
                    f"ESPN connection error: {e}. Retrying in {wait:.1f}s (attempt {attempt + 1})"
                )
                if attempt < self.config.max_retries:
                    self.metrics["retries"] += 1
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

    async def get_json(
        self, path: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """GET request with response cache + in-flight dedup, returns parsed JSON.

        Args:
            path: API path (appended to base_url).
            params: Query params (used for cache key canonicalization).
            **kwargs: Extra httpx kwargs (merged with params if given).
        """
        if params is None:
            params = kwargs.pop("params", None)
        key = canonicalize(path, params) if params else path

        if self.config.cache_enabled:
            cached = self._cache.get(key)
            if cached is not None:
                self.metrics["cache_hits"] += 1
                return cached
            self.metrics["cache_misses"] += 1

            # In-flight dedup: share one HTTP call for concurrent identical requests
            pending = self._pending.get(key)
            if pending is not None and not pending.done():
                self.metrics["deduped"] += 1
                return await asyncio.shield(pending)

            future: asyncio.Future[dict[str, Any]] = asyncio.ensure_future(
                self._fetch_json(path, params=params, **kwargs)
            )
            self._pending[key] = future

            def _on_fetch_done(fut: asyncio.Future[dict[str, Any]]) -> None:
                """Cache the completed payload and drop the pending entry.

                Runs when the shared fetch finishes — even if the original
                awaiter was cancelled — so a completed result is never lost
                and later callers never re-fetch a URL already in flight.
                """
                self._pending.pop(key, None)
                if (
                    self.config.cache_enabled
                    and not fut.cancelled()
                    and fut.exception() is None
                ):
                    self._cache.set(key, fut.result())

            future.add_done_callback(_on_fetch_done)
            return await asyncio.shield(future)

        return await self._fetch_json(path, params=params, **kwargs)

    async def _fetch_json(
        self, path: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Raw fetch (no cache/dedup) under the bounded-concurrency semaphore."""
        async with self._semaphore:
            response = await self.get(path, params=params, **kwargs)
        return cast(dict[str, Any], response.json())

    # ── Reference Resolution ────────────────────────────────────────────────

    async def resolve_ref(self, ref_url: str) -> dict[str, Any]:
        """Resolve an ESPN $ref link to its full JSON payload.

        ESPN's API uses $ref extensively — instead of embedding data,
        it returns URLs like:
            {"$ref": "https://sports.core.api.espn.com/v2/sports/mma/athletes/12345"}

        This method follows that URL and returns the full resolved JSON.
        Resolution is cached (client response cache) and deduplicated in-flight,
        so the same $ref is never downloaded twice in a run.
        """
        # Remove base_url prefix if present, since the client already has it
        if ref_url.startswith(self.config.base_url):
            path = ref_url[len(self.config.base_url):]
        else:
            path = ref_url

        return await self.get_json(path)

    # ── Pagination ──────────────────────────────────────────────────────────

    # Hard cap on pages per paginate() call — defense-in-depth against
    # endpoints that never signal the end.
    # Overridable via ESPN_MAX_PAGES env var (bounded runs, acceptance tests).
    MAX_PAGINATION_PAGES = 200

    def _pagination_cap(self) -> int:
        """Max pages per paginate() call; env override wins when valid."""
        try:
            return int(os.environ.get("ESPN_MAX_PAGES", self.MAX_PAGINATION_PAGES))
        except ValueError:
            return self.MAX_PAGINATION_PAGES

    async def paginate(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        limit: int | None = None,
        start_page: int = 1,
    ) -> AsyncIterator[dict[str, Any]]:
        """Paginate through ESPN API results.

        ESPN returns paginated results with:
        {
            "count": 100,
            "pageIndex": 1,
            "pageCount": 5,
            "items": [...]
        }

        ESPN v2 core API pagination is `limit` (page size, default 25, max 1000)
        + `page` (1-indexed page number). The `offset` param is ignored by ESPN
        (verified live on athletes/leagues/events/rankings endpoints), so we
        drive the walk with `page` and trust the echoed `pageIndex`/`pageCount`.

        This generator yields one page at a time (the full JSON for each page).

        Args:
            path: API path
            params: Query parameters
            limit: Maximum items to yield (None = all pages)
            start_page: First page to fetch (resumable walks pass the last
                processed page + 1 so an interrupted census never restarts
                from page 1; default 1 preserves the original behavior).

        Yields:
            Full JSON response for each page.
        """
        if params is None:
            params = {}
        params.setdefault("limit", self.config.page_limit)
        params.setdefault("page", start_page)

        total_yielded = 0
        pages_yielded = 0
        seen_item_ids: set[Any] = set()
        max_pages = self._pagination_cap()

        while True:
            response = await self.get_json(path, params=params)
            items = response.get("items", [])
            if not items:
                break

            yield response

            total_yielded += len(items)
            pages_yielded += 1
            if limit is not None and total_yielded >= limit:
                break
            if pages_yielded >= max_pages:
                logger.warning(
                    f"Pagination cap reached ({max_pages} pages) "
                    f"for {path} — stopping"
                )
                break

            # No-progress guard: a full page of already-seen item IDs means
            # the server is re-serving data and paging is not working.
            page_ids = {
                item.get("id")
                for item in items
                if isinstance(item, dict) and item.get("id") is not None
            }
            if page_ids and page_ids <= seen_item_ids:
                logger.warning(
                    f"Pagination stalled (duplicate page) for {path} — stopping"
                )
                break
            seen_item_ids |= page_ids

            try:
                page_index = int(response.get("pageIndex") or params["page"])
                page_count = int(response.get("pageCount") or 0)
            except (TypeError, ValueError):
                logger.warning(
                    f"Pagination metadata unparseable for {path} — stopping"
                )
                break

            # Reached the last page (pageIndex is 1-based; ESPN echoes the
            # requested page number in pageIndex).
            if page_count and page_index >= page_count:
                break

            requested_page = int(params["page"])
            next_page = page_index + 1
            if next_page <= requested_page:
                logger.warning(
                    f"Pagination did not advance past page {requested_page} "
                    f"for {path} — stopping"
                )
                break
            params["page"] = next_page

    # ── Health Check ────────────────────────────────────────────────────────

    async def health_check(self) -> bool:
        """Quick check: is the ESPN API reachable?"""
        try:
            response = await self.get("/leagues", params={"limit": 1})
            return response.is_success
        except Exception:
            return False
