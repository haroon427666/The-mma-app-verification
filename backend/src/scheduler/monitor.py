"""Health Monitor — tracks sync job health and provider status."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ProviderHealth:
    name: str
    is_up: bool = True
    last_check: datetime | None = None
    last_success: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class JobHealth:
    name: str
    last_run: datetime | None = None
    last_success: datetime | None = None
    last_duration_ms: float = 0.0
    total_runs: int = 0
    total_successes: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    is_running: bool = False


class HealthMonitor:
    """Tracks the health of all sync jobs and providers."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobHealth] = {}
        self._providers: dict[str, ProviderHealth] = {}
        self._started_at = datetime.now(UTC)

    # ── Job tracking ────────────────────────────────────────────────────

    def register_job(self, name: str) -> JobHealth:
        if name not in self._jobs:
            self._jobs[name] = JobHealth(name=name)
        return self._jobs[name]

    def job_started(self, name: str) -> None:
        h = self.register_job(name)
        h.last_run = datetime.now(UTC)
        h.total_runs += 1
        h.is_running = True

    def job_succeeded(self, name: str, duration_ms: float) -> None:
        h = self.register_job(name)
        h.last_success = datetime.now(UTC)
        h.last_duration_ms = duration_ms
        h.total_successes += 1
        h.consecutive_failures = 0
        h.is_running = False

    def job_failed(self, name: str, error: str) -> None:
        h = self.register_job(name)
        h.total_failures += 1
        h.consecutive_failures += 1
        h.is_running = False
        logger.warning(f"Job '{name}' failed (consecutive: {h.consecutive_failures}): {error}")

    def consecutive_failures(self, job_name: str) -> int:
        """Consecutive failure count for a job (0 if never run)."""
        h = self._jobs.get(job_name)
        return h.consecutive_failures if h else 0

    # ── Provider tracking ───────────────────────────────────────────────

    def register_provider(self, name: str) -> ProviderHealth:
        if name not in self._providers:
            self._providers[name] = ProviderHealth(name=name)
        return self._providers[name]

    def provider_ok(self, name: str, latency_ms: float) -> None:
        p = self.register_provider(name)
        p.is_up = True
        p.last_check = datetime.now(UTC)
        p.last_success = datetime.now(UTC)
        p.consecutive_failures = 0
        p.avg_latency_ms = (p.avg_latency_ms * 0.9) + (latency_ms * 0.1)  # EMA

    def provider_down(self, name: str, error: str) -> None:
        p = self.register_provider(name)
        p.is_up = False
        p.last_check = datetime.now(UTC)
        p.last_error = error
        p.consecutive_failures += 1
        logger.warning(f"Provider '{name}' DOWN (x{p.consecutive_failures}): {error}")

    # ── Reports ─────────────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        """Full health report for dashboard / API."""
        return {
            "uptime_seconds": (datetime.now(UTC) - self._started_at).total_seconds(),
            "jobs": {
                name: {
                    "last_run": h.last_run.isoformat() if h.last_run else None,
                    "last_success": h.last_success.isoformat() if h.last_success else None,
                    "last_duration_ms": h.last_duration_ms,
                    "total_runs": h.total_runs,
                    "success_rate": (
                        h.total_successes / h.total_runs if h.total_runs > 0 else 0
                    ),
                    "consecutive_failures": h.consecutive_failures,
                    "is_running": h.is_running,
                    "status": "running" if h.is_running else
                              "unhealthy" if h.consecutive_failures >= 3 else "healthy",
                }
                for name, h in self._jobs.items()
            },
            "providers": {
                name: {
                    "is_up": p.is_up,
                    "last_success": p.last_success.isoformat() if p.last_success else None,
                    "consecutive_failures": p.consecutive_failures,
                    "avg_latency_ms": round(p.avg_latency_ms, 1),
                }
                for name, p in self._providers.items()
            },
        }

    def is_healthy(self) -> bool:
        """Overall health check. False if any job has 3+ consecutive failures."""
        for job in self._jobs.values():
            if job.consecutive_failures >= 3:
                return False
        return True
