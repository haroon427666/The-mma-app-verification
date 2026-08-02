"""
Clock abstraction — injectable time source.

Never call datetime.now() or time.monotonic() directly in sync code.
Inject a Clock instead. Testing becomes trivial: freeze time, advance time, verify.

Usage:
    clock = SystemClock()
    now = clock.now()           # datetime
    elapsed = clock.elapsed()   # monotonic seconds since creation
"""

import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone


class Clock(ABC):
    """Abstract time source. Inject into SyncContext."""

    @abstractmethod
    def now(self) -> datetime:
        """Current UTC datetime."""
        ...

    @abstractmethod
    def monotonic(self) -> float:
        """Monotonic seconds (for measuring durations)."""
        ...

    @abstractmethod
    def elapsed(self) -> float:
        """Seconds since this clock was created."""
        ...


class SystemClock(Clock):
    """Production clock — delegates to real system time."""

    def __init__(self) -> None:
        self._start = time.monotonic()

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonic(self) -> float:
        return time.monotonic()

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self._start


class FrozenClock(Clock):
    """Test clock — time is frozen at a fixed point. Advance manually."""

    def __init__(self, frozen_at: datetime | None = None) -> None:
        self._now = frozen_at or datetime(2026, 1, 1, tzinfo=timezone.utc)
        self._ticks: float = 0.0  # Monotonic counter

    def now(self) -> datetime:
        return self._now

    def monotonic(self) -> float:
        return self._ticks

    @property
    def elapsed(self) -> float:
        return self._ticks

    def advance(self, seconds: float) -> None:
        """Advance the clock by the given number of seconds."""
        from datetime import timedelta
        self._now += timedelta(seconds=seconds)
        self._ticks += seconds

    def set(self, dt: datetime) -> None:
        """Set the clock to a specific datetime."""
        self._now = dt
