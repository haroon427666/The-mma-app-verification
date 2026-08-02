"""
Retry policies — injectable retry, backoff, and timeout strategies.

Nothing in the sync engine hardcodes retry logic. Policies are injected
into the SyncPipeline, making them reusable across all provider operations.

Usage:
    policy = RetryPolicy(
        max_attempts=3,
        backoff=ExponentialBackoff(base=2.0, max_delay=30.0),
        timeout=TimeoutPolicy(total=120.0),
        retry_on=(httpx.TimeoutException, httpx.HTTPStatusError),
    )
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)


# ── Backoff Strategies ────────────────────────────────────────────────────────


@dataclass
class ExponentialBackoff:
    """Exponential backoff: delay = base ^ attempt seconds."""

    base: float = 2.0
    max_delay: float = 60.0
    jitter: bool = True  # Add random jitter to avoid thundering herd

    async def wait(self, attempt: int) -> None:
        import random
        delay = min(self.base ** attempt, self.max_delay)
        if self.jitter:
            delay = delay * (0.5 + random.random())  # 50%-150% of calculated delay
        logger.debug(f"Backoff: waiting {delay:.1f}s (attempt {attempt})")
        await asyncio.sleep(delay)


@dataclass
class FixedBackoff:
    """Fixed delay between retries."""

    delay: float = 5.0

    async def wait(self, _attempt: int) -> None:
        await asyncio.sleep(self.delay)


@dataclass
class NoBackoff:
    """No delay between retries — retry immediately."""

    async def wait(self, _attempt: int) -> None:
        pass


# ── Timeout Policy ────────────────────────────────────────────────────────────


@dataclass
class TimeoutPolicy:
    """Total timeout for an operation including all retries."""

    total: float = 120.0  # Total seconds allowed for the entire operation
    per_attempt: float | None = None  # Per-attempt timeout (None = no per-attempt limit)


# ── Retry Policy ──────────────────────────────────────────────────────────────


@dataclass
class RetryPolicy:
    """Configurable retry strategy for sync operations.

    Usage:
        policy = RetryPolicy(
            max_attempts=3,
            backoff=ExponentialBackoff(base=2.0),
            timeout=TimeoutPolicy(total=120.0),
            retry_on=(TimeoutError, ConnectionError),
        )

        async with policy:
            result = await some_operation()
    """

    max_attempts: int = 3
    backoff: ExponentialBackoff | FixedBackoff | NoBackoff = field(
        default_factory=lambda: ExponentialBackoff()
    )
    timeout: TimeoutPolicy = field(default_factory=TimeoutPolicy)
    retry_on: tuple[type[Exception], ...] = (Exception,)  # Which exceptions are retryable

    async def execute(
        self,
        operation: Callable[[], Coroutine[Any, Any, Any]],
        context: str = "operation",
    ) -> Any:
        """Execute an operation with retry logic.

        Args:
            operation: Async callable to retry.
            context: Description for logging (e.g. "fetch_fighters").

        Returns:
            The operation's return value.

        Raises:
            The last exception after all retries are exhausted.
        """
        last_error: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return await asyncio.wait_for(
                    operation(),
                    timeout=self.timeout.per_attempt,
                )
            except tuple(self.retry_on) as e:
                last_error = e
                if attempt < self.max_attempts:
                    logger.warning(
                        f"Retry [{attempt}/{self.max_attempts}] {context}: {e}"
                    )
                    await self.backoff.wait(attempt)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed for {context}: {e}"
                    )
            except Exception as e:
                # Non-retryable exception — fail immediately
                logger.error(f"Non-retryable error in {context}: {e}")
                raise

        # All retries exhausted
        raise last_error or RuntimeError(f"{context}: all retries exhausted")


# ── Pre-built Policies ────────────────────────────────────────────────────────

# Default for most sync operations
DEFAULT_RETRY = RetryPolicy(
    max_attempts=3,
    backoff=ExponentialBackoff(base=2.0, max_delay=30.0),
    timeout=TimeoutPolicy(total=120.0),
)

# For live/realtime checks — fast fail
AGGRESSIVE_RETRY = RetryPolicy(
    max_attempts=1,
    backoff=NoBackoff(),
    timeout=TimeoutPolicy(total=30.0),
)

# For long-running bulk fetches
LONG_RUNNING_RETRY = RetryPolicy(
    max_attempts=5,
    backoff=ExponentialBackoff(base=2.0, max_delay=60.0),
    timeout=TimeoutPolicy(total=600.0, per_attempt=120.0),
)
