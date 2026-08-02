"""Retry Engine — exponential backoff with jitter and budget.

Production retry policy for sync jobs that fail transiently.
Never retries indefinitely — enforces a per-job retry budget.

Algorithm: sleep = min(base * (2 ^ attempt) + jitter, max_backoff)
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RetryDecision(Enum):
    RETRY = "retry"
    FAIL = "fail"
    DEAD_LETTER = "dead_letter"


@dataclass
class RetryPolicy:
    """Configurable retry behavior for a sync job."""

    max_attempts: int = 4
    base_seconds: float = 1.0
    max_backoff: float = 60.0
    jitter_factor: float = 0.3  # ±30% of computed delay
    retry_budget: int = 10       # Max total retries across all runs per hour

    # Transient errors worth retrying
    retryable_exceptions: tuple = (
        asyncio.TimeoutError,
        ConnectionError,
        OSError,
    )


@dataclass
class RetryState:
    """Mutable retry state tracked per job."""

    policy: RetryPolicy
    attempt: int = 0
    total_retries_this_hour: int = 0
    last_retry_window_start: float = field(default_factory=time.monotonic)

    def _reset_budget_if_expired(self) -> None:
        now = time.monotonic()
        if now - self.last_retry_window_start > 3600:
            self.total_retries_this_hour = 0
            self.last_retry_window_start = now

    def decide(self, exception: Exception) -> RetryDecision:
        self._reset_budget_if_expired()

        # Don't retry non-retryable errors
        if not isinstance(exception, self.policy.retryable_exceptions):
            return RetryDecision.DEAD_LETTER

        # Budget exhausted
        if self.total_retries_this_hour >= self.policy.retry_budget:
            logger.warning(f"Retry budget exhausted ({self.policy.retry_budget}/hour)")
            return RetryDecision.FAIL

        # Max attempts reached
        if self.attempt >= self.policy.max_attempts:
            return RetryDecision.FAIL

        return RetryDecision.RETRY

    def compute_delay(self) -> float:
        self.attempt += 1
        self.total_retries_this_hour += 1

        base = self.policy.base_seconds * (2 ** (self.attempt - 1))
        capped = min(base, self.policy.max_backoff)
        jitter = capped * self.policy.jitter_factor * random.uniform(-1, 1)
        delay = max(0.1, capped + jitter)

        logger.debug(f"Retry {self.attempt}/{self.policy.max_attempts}: waiting {delay:.1f}s")
        return delay

    async def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute fn with retries. Returns result or raises on failure."""
        while True:
            try:
                result = await fn(*args, **kwargs)
                self.attempt = 0  # Reset on success
                return result
            except Exception as e:
                decision = self.decide(e)
                if decision == RetryDecision.RETRY:
                    await asyncio.sleep(self.compute_delay())
                    continue
                elif decision == RetryDecision.DEAD_LETTER:
                    logger.error(f"Non-retryable error, routing to dead letter: {e}")
                    raise
                else:  # FAIL
                    logger.error(f"All retries exhausted ({self.attempt} attempts): {e}")
                    raise

    def reset(self) -> None:
        self.attempt = 0
