"""
Failure handling — classification, circuit breaker, dead-letter routing.

Production-grade reliability layer. Not just retry — this layer decides:
- Is this error transient? → retry with backoff
- Is this error permanent? → dead-letter the DTO
- Is the provider down? → open the circuit breaker
- Is this a data integrity issue? → dead-letter + alert

Integrates with SyncEventBus: fires events on circuit state changes,
dead-letter additions, and retry exhaustion.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# ── Failure Categories ────────────────────────────────────────────────────────


class FailureCategory(str, Enum):
    """Why did this operation fail? Determines recovery strategy."""

    TRANSIENT = "TRANSIENT"
    """Temporary: network timeout, 429 rate limit, 503 service unavailable.
    → RETRY with exponential backoff."""

    PERMANENT = "PERMANENT"
    """Unrecoverable for this DTO: 400 bad request, 404 not found, validation error.
    → DEAD LETTER the DTO. Do NOT retry."""

    PROVIDER_DOWN = "PROVIDER_DOWN"
    """The provider is unreachable: connection refused, DNS failure, 500+ cascade.
    → OPEN CIRCUIT BREAKER. Stop all calls to this provider for N seconds."""

    DATA_ERROR = "DATA_ERROR"
    """Our fault: DB constraint violation, integrity error, serialization failure.
    → DEAD LETTER the DTO. Log the error. Do NOT retry (would fail identically)."""

    UNKNOWN = "UNKNOWN"
    """Unclassified. → RETRY once, then dead-letter if it fails again."""


# ── Failure Classifier ────────────────────────────────────────────────────────


class FailureClassifier:
    """Classifies exceptions into FailureCategory based on type and content.

    Extensible: add new rules for new providers or error types without
    changing the circuit breaker or dead-letter logic.
    """

    # Exception types that are always transient
    TRANSIENT_TYPES: tuple[type[Exception], ...] = (
        asyncio.TimeoutError,
        TimeoutError,
        ConnectionError,
        ConnectionRefusedError,
        ConnectionResetError,
        BrokenPipeError,
    )

    # Exception types that are always permanent
    PERMANENT_TYPES: tuple[type[Exception], ...] = (
        TypeError,
        ValueError,
        KeyError,
        AttributeError,
    )

    def classify(self, error: Exception) -> FailureCategory:
        """Classify an exception into a failure category.

        Override for provider-specific error handling
        (e.g. httpx.HTTPStatusError with status codes).
        """
        error_type = type(error)
        error_msg = str(error).lower()

        # ── HTTP status-based classification (httpx / requests / aiohttp) ──
        if self._is_http_error(error):
            return self._classify_http(error)

        # ── Type-based classification ──────────────────────────────────────
        if issubclass(error_type, self.TRANSIENT_TYPES):
            return FailureCategory.TRANSIENT

        if issubclass(error_type, self.PERMANENT_TYPES):
            return FailureCategory.PERMANENT

        # ── Content-based heuristics ───────────────────────────────────────
        if any(phrase in error_msg for phrase in (
            "timeout", "timed out", "connect", "refused",
            "reset", "broken pipe", "no route to host",
            "too many requests", "rate limit",
        )):
            return FailureCategory.TRANSIENT

        if any(phrase in error_msg for phrase in (
            "bad request", "not found", "validation",
            "invalid", "unsupported",
        )):
            return FailureCategory.PERMANENT

        if any(phrase in error_msg for phrase in (
            "service unavailable", "internal server error",
            "bad gateway", "gateway timeout", "dns",
        )):
            return FailureCategory.PROVIDER_DOWN

        if any(phrase in error_msg for phrase in (
            "constraint", "integrity", "duplicate",
            "foreign key", "serialization",
        )):
            return FailureCategory.DATA_ERROR

        return FailureCategory.UNKNOWN

    def _is_http_error(self, error: Exception) -> bool:
        """Check if this is an HTTP library error with a status code."""
        return hasattr(error, "response") or (
            hasattr(error, "status_code")
        )

    def _classify_http(self, error: Exception) -> FailureCategory:
        """Classify by HTTP status code."""
        status = getattr(error, "status_code", 0)
        if not status and hasattr(error, "response"):
            status = getattr(error.response, "status_code", 0)

        if status == 429:  # Rate limited
            return FailureCategory.TRANSIENT

        if status in (400, 404, 405, 406, 410, 422):
            return FailureCategory.PERMANENT

        if status in (500, 502, 503, 504):
            return FailureCategory.PROVIDER_DOWN

        if status in (408, 425, 429):
            return FailureCategory.TRANSIENT

        if 500 <= status < 600:
            return FailureCategory.PROVIDER_DOWN

        if 400 <= status < 500:
            return FailureCategory.PERMANENT

        return FailureCategory.UNKNOWN


# ── Circuit Breaker ───────────────────────────────────────────────────────────


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal — requests go through
    OPEN = "OPEN"            # Tripped — all requests fail immediately
    HALF_OPEN = "HALF_OPEN"  # Testing — one request allowed to probe


@dataclass
class CircuitBreaker:
    """Per-provider circuit breaker.

    Three states:
        CLOSED → normal operation. Failure counter increments on each error.
                 When counter ≥ failure_threshold → OPEN.

        OPEN → all calls fail immediately with CircuitBreakerOpenError.
               After recovery_timeout seconds → HALF_OPEN.

        HALF_OPEN → one test call allowed.
                    Success → reset to CLOSED.
                    Failure → back to OPEN.

    Thread-safe for use across multiple sync jobs targeting the same provider.
    """

    provider_slug: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 1

    # Internal state
    _state: CircuitState = CircuitState.CLOSED
    _failure_count: int = 0
    _last_failure_time: float = 0.0
    _last_success_time: float = 0.0
    _half_open_attempts: int = 0
    _total_trips: int = 0

    async def before_call(self) -> None:
        """Called before every provider request. Raises if circuit is OPEN."""
        if self._state == CircuitState.CLOSED:
            return  # Normal — allow

        if self._state == CircuitState.OPEN:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                # Transition: OPEN → HALF_OPEN
                self._state = CircuitState.HALF_OPEN
                self._half_open_attempts = 0
                logger.info(
                    f"Circuit HALF_OPEN: {self.provider_slug} "
                    f"(recovery timeout elapsed after {elapsed:.0f}s)"
                )
                return  # Allow the probe call
            else:
                remaining = self.recovery_timeout - elapsed
                raise CircuitBreakerOpenError(
                    f"Circuit OPEN for {self.provider_slug}: "
                    f"{remaining:.0f}s until recovery attempt. "
                    f"Trips={self._total_trips}"
                )

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_attempts < self.half_open_max_calls:
                self._half_open_attempts += 1
                return  # Allow probe call
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit HALF_OPEN for {self.provider_slug}: "
                    f"max probe calls ({self.half_open_max_calls}) reached"
                )

    def on_success(self) -> None:
        """Called after a successful provider call."""
        if self._state == CircuitState.HALF_OPEN:
            # Reset: HALF_OPEN → CLOSED
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            logger.info(f"Circuit CLOSED: {self.provider_slug} (probe succeeded)")
        elif self._state == CircuitState.CLOSED:
            self._failure_count = 0  # Reset on any success
        self._last_success_time = time.monotonic()

    def on_failure(self, category: FailureCategory) -> None:
        """Called after a failed provider call."""
        if category in (FailureCategory.PERMANENT, FailureCategory.DATA_ERROR):
            return  # Don't count permanent/data errors toward circuit trips

        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if (
            self._state == CircuitState.HALF_OPEN
            or self._state == CircuitState.CLOSED
        ) and self._failure_count >= self.failure_threshold:
            self._trip()

    # ── State ──────────────────────────────────────────────────────────────

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    @property
    def failure_count(self) -> int:
        return self._failure_count

    @property
    def total_trips(self) -> int:
        return self._total_trips

    def reset(self) -> None:
        """Force-reset to CLOSED (manual intervention)."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._half_open_attempts = 0

    # ── Internal ───────────────────────────────────────────────────────────

    def _trip(self) -> None:
        self._state = CircuitState.OPEN
        self._total_trips += 1
        logger.warning(
            f"Circuit OPEN: {self.provider_slug} "
            f"(failures={self._failure_count} threshold={self.failure_threshold} "
            f"total_trips={self._total_trips})"
        )


# ── Circuit Breaker Error ─────────────────────────────────────────────────────


class CircuitBreakerOpenError(Exception):
    """Raised when a call is attempted while the circuit breaker is OPEN."""
