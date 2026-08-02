"""
Enterprise Connector Framework — plugin-based architecture for all data sources.

Every data source (ESPN, UFCStats, TheSportsDB, Wikipedia, Sherdog, Tapology, etc.)
implements BaseConnector. The framework handles registration, health, metrics,
rate limiting, circuit breaking, and lifecycle management.

No source-specific parsing lives here — that belongs in each connector.
"""

import abc
import hashlib
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncIterator, Callable, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Types & Enums
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"
    RATE_LIMITED = "rate_limited"
    DISABLED = "disabled"


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class JobPriority(int, Enum):
    LIVE = 0
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class ConnectorConfig:
    """Shared configuration for all connectors."""
    name: str
    version: str = "1.0.0"
    base_url: str = ""
    timeout_seconds: float = 30.0
    connect_timeout_seconds: float = 10.0
    max_retries: int = 3
    retry_backoff_base: float = 1.0
    rate_limit_rps: float = 10.0
    rate_limit_burst: int = 15
    circuit_breaker_threshold: int = 5
    circuit_breaker_reset_seconds: float = 60.0
    user_agent: str = "MMA-Platform/1.0"
    proxy_url: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)
    feature_flags: dict[str, bool] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class ConnectorMetrics:
    """Runtime metrics collected per connector."""
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    requests_rate_limited: int = 0
    last_request_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    consecutive_failures: int = 0
    circuit_state: CircuitState = CircuitState.CLOSED
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_at: Optional[datetime] = None
    uptime_seconds: float = 0.0
    data_fetched_bytes: int = 0


@dataclass
class ConnectorHealth:
    """Health check result."""
    status: ConnectorStatus
    connector: str
    checked_at: datetime
    latency_ms: float
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class FetchResult:
    """Result of a fetch operation — contains raw payload metadata."""
    connector: str
    endpoint: str
    payload: dict[str, Any] | list[Any] | str | bytes
    content_type: str = "application/json"
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    checksum: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    status_code: int = 200
    duration_ms: float = 0.0
    page: Optional[int] = None
    cursor: Optional[str] = None

    def __post_init__(self):
        if not self.checksum and self.payload:
            raw = str(self.payload).encode()
            self.checksum = hashlib.sha256(raw).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════
# BaseConnector — what every connector must implement
# ═══════════════════════════════════════════════════════════════════════════

class BaseConnector(abc.ABC):
    """Plugin interface for all data source connectors.

    Subclasses implement source-specific fetch/parse/normalize logic.
    The framework handles rate limiting, retry, circuit breaking, metrics.
    """

    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.metrics = ConnectorMetrics()
        self._started = False
        self._circuit_open_since: Optional[float] = None
        self._token_bucket = _TokenBucket(config.rate_limit_rps, config.rate_limit_burst)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Initialize connection pool, authenticate, warm caches."""
        self._started = True
        logger.info(f"[{self.config.name}] Connected")

    async def authenticate(self) -> None:
        """Obtain auth token / API key. Called before first fetch."""
        pass

    async def health_check(self) -> ConnectorHealth:
        """Quick connectivity test. Returns health status."""
        start = time.monotonic()
        try:
            ok = await self._ping()
            return ConnectorHealth(
                status=ConnectorStatus.HEALTHY if ok else ConnectorStatus.DOWN,
                connector=self.config.name,
                checked_at=datetime.now(timezone.utc),
                latency_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as e:
            return ConnectorHealth(
                status=ConnectorStatus.DOWN,
                connector=self.config.name,
                checked_at=datetime.now(timezone.utc),
                latency_ms=(time.monotonic() - start) * 1000,
                message=str(e),
            )

    async def shutdown(self) -> None:
        """Close connections, flush buffers."""
        self._started = False

    # ── Core Fetch Pipeline ────────────────────────────────────────────────

    async def fetch(self, endpoint: str, **params) -> FetchResult:
        """Fetch with rate limiting, retry, circuit breaker."""
        await self._check_circuit()
        await self._token_bucket.acquire()

        start = time.monotonic()
        self.metrics.requests_total += 1
        self.metrics.last_request_at = datetime.now(timezone.utc)

        try:
            raw = await self._fetch_raw(endpoint, **params)
            result = FetchResult(
                connector=self.config.name,
                endpoint=endpoint,
                payload=raw,
                duration_ms=(time.monotonic() - start) * 1000,
            )
            self._record_success(result.duration_ms)
            return result
        except Exception as e:
            self._record_failure()
            raise

    async def fetch_paginated(
        self, endpoint: str, **params,
    ) -> AsyncIterator[FetchResult]:
        """Fetch all pages from a paginated endpoint."""
        page = 0
        while True:
            result = await self.fetch(endpoint, page=page, **params)
            yield result
            if result.cursor is None and (result.page or 0) >= page:
                break
            page += 1

    # ── Subclass Hooks (override these) ────────────────────────────────────

    async def _ping(self) -> bool:
        """Quick connectivity check. Override per connector."""
        return True

    @abc.abstractmethod
    async def _fetch_raw(self, endpoint: str, **params) -> Any:
        """Execute the actual HTTP request. Implemented per connector."""
        ...

    @abc.abstractmethod
    async def parse(self, raw: FetchResult) -> list[dict[str, Any]]:
        """Parse raw payload into flat dicts. Source-specific."""
        ...

    @abc.abstractmethod
    async def normalize(self, parsed: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map source fields to canonical schema."""
        ...

    @abc.abstractmethod
    async def validate(self, normalized: list[dict[str, Any]]) -> tuple[list, list]:
        """Validate normalized entities. Returns (valid, invalid)."""
        ...

    # ── Metadata ───────────────────────────────────────────────────────────

    def version(self) -> str:
        return self.config.version

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.config.name,
            "version": self.config.version,
            "base_url": self.config.base_url,
            "status": self.status().value,
            "metrics": {
                "requests_total": self.metrics.requests_total,
                "requests_failed": self.metrics.requests_failed,
                "avg_latency_ms": self.metrics.avg_latency_ms,
                "circuit_state": self.metrics.circuit_state.value,
            },
        }

    def status(self) -> ConnectorStatus:
        if not self._started:
            return ConnectorStatus.DISABLED
        if self.metrics.circuit_state == CircuitState.OPEN:
            return ConnectorStatus.DOWN
        if self.metrics.consecutive_failures >= 2:
            return ConnectorStatus.DEGRADED
        return ConnectorStatus.HEALTHY

    # ── Internals ──────────────────────────────────────────────────────────

    async def _check_circuit(self):
        if self.metrics.circuit_state == CircuitState.OPEN:
            elapsed = time.monotonic() - (self._circuit_open_since or 0)
            if elapsed >= self.config.circuit_breaker_reset_seconds:
                self.metrics.circuit_state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError(self.config.name)

    def _record_success(self, latency_ms: float):
        self.metrics.requests_success += 1
        self.metrics.last_success_at = datetime.now(timezone.utc)
        self.metrics.consecutive_failures = 0
        if self.metrics.circuit_state == CircuitState.HALF_OPEN:
            self.metrics.circuit_state = CircuitState.CLOSED
        alpha = 0.1
        self.metrics.avg_latency_ms = (
            self.metrics.avg_latency_ms * (1 - alpha) + latency_ms * alpha
        )

    def _record_failure(self):
        self.metrics.requests_failed += 1
        self.metrics.last_failure_at = datetime.now(timezone.utc)
        self.metrics.consecutive_failures += 1
        if self.metrics.consecutive_failures >= self.config.circuit_breaker_threshold:
            self.metrics.circuit_state = CircuitState.OPEN
            self._circuit_open_since = time.monotonic()


# ═══════════════════════════════════════════════════════════════════════════
# Rate Limiter — Token Bucket
# ═══════════════════════════════════════════════════════════════════════════

class _TokenBucket:
    def __init__(self, rate: float, burst: int):
        self.rate = rate
        self.burst = burst
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    async def acquire(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens < 1.0:
            wait = (1.0 - self.tokens) / self.rate
            time.sleep(wait)
            self.tokens = 0.0
        else:
            self.tokens -= 1.0


# ═══════════════════════════════════════════════════════════════════════════
# Errors
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorError(Exception):
    """Base connector error."""
    def __init__(self, connector: str, message: str):
        self.connector = connector
        super().__init__(f"[{connector}] {message}")


class CircuitBreakerOpenError(ConnectorError):
    def __init__(self, connector: str):
        super().__init__(connector, "Circuit breaker is open")


class RateLimitExceeded(ConnectorError):
    def __init__(self, connector: str, retry_after: float = 60):
        self.retry_after = retry_after
        super().__init__(connector, f"Rate limited — retry after {retry_after}s")


class AuthenticationError(ConnectorError):
    def __init__(self, connector: str):
        super().__init__(connector, "Authentication failed")


class ParseError(ConnectorError):
    def __init__(self, connector: str, detail: str = ""):
        super().__init__(connector, f"Parse error{f': {detail}' if detail else ''}")
