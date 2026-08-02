"""Provider Monitoring — availability, latency, error rate tracking.

Tracks per-provider: ESPN, TheSportsDB, Octagon API.
Records: availability %, avg latency, error rate, consecutive failures,
last success/failure timestamps, rate limit hits.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderMetrics:
    name: str
    base_url: str = ""
    is_up: bool = True
    availability_pct: float = 100.0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0
    total_requests: int = 0
    total_errors: int = 0
    consecutive_failures: int = 0
    rate_limit_hits: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_error: str = ""

    def record_success(self, latency_ms: float) -> None:
        self.is_up = True
        self.total_requests += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now(timezone.utc)
        # Exponential moving average
        self.avg_latency_ms = (self.avg_latency_ms * 0.9) + (latency_ms * 0.1)
        self.error_rate = (self.total_errors / self.total_requests * 100) if self.total_requests > 0 else 0

    def record_failure(self, error: str = "") -> None:
        self.total_requests += 1
        self.total_errors += 1
        self.consecutive_failures += 1
        self.last_failure = datetime.now(timezone.utc)
        self.last_error = error
        self.error_rate = (self.total_errors / self.total_requests * 100)
        if self.consecutive_failures >= 3:
            self.is_up = False

    def record_rate_limit(self) -> None:
        self.rate_limit_hits += 1
        logger.warning(f"Rate limit hit on {self.name} (total: {self.rate_limit_hits})")


class ProviderMonitor:
    """Tracks health of all external providers."""

    def __init__(self):
        self._providers: dict[str, ProviderMetrics] = {}

    def register(self, name: str, base_url: str = "") -> ProviderMetrics:
        if name not in self._providers:
            self._providers[name] = ProviderMetrics(name=name, base_url=base_url)
        return self._providers[name]

    def get(self, name: str) -> ProviderMetrics:
        return self._providers.get(name) or self.register(name)

    def status(self) -> dict:
        return {
            name: {
                "is_up": p.is_up,
                "availability": f"{p.availability_pct:.1f}%",
                "avg_latency_ms": round(p.avg_latency_ms, 1),
                "error_rate": f"{p.error_rate:.1f}%",
                "total_requests": p.total_requests,
                "total_errors": p.total_errors,
                "consecutive_failures": p.consecutive_failures,
                "rate_limit_hits": p.rate_limit_hits,
                "last_success": p.last_success.isoformat() if p.last_success else None,
                "last_failure": p.last_failure.isoformat() if p.last_failure else None,
            }
            for name, p in self._providers.items()
        }
