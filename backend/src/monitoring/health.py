"""Production Health Checks — Kubernetes-ready, multi-level.

Endpoints:
    GET /health           — app alive
    GET /health/live      — liveness (basic)
    GET /health/ready     — readiness (DB + Redis + providers)
    GET /health/database  — DB connectivity
    GET /health/redis     — Redis connectivity
    GET /health/providers — ESPN + TSDB + Octagon status
    GET /health/scheduler — Scheduler jobs + queue status

Each returns: {"status": "healthy", "checks": {...}} or "degraded" / "failed"
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class HealthStatus:
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


@dataclass
class HealthCheck:
    name: str
    status: str = HealthStatus.HEALTHY
    detail: str = ""
    duration_ms: float = 0.0


class HealthChecker:
    """Runs all health checks and aggregates results."""

    def __init__(self):
        self._checks: dict[str, Callable] = {}
        self._started_at = datetime.now(timezone.utc)

    def register(self, name: str, check_fn: Callable) -> None:
        self._checks[name] = check_fn

    async def run_check(self, name: str) -> HealthCheck:
        check_fn = self._checks.get(name)
        if check_fn is None:
            return HealthCheck(name=name, status=HealthStatus.FAILED,
                              detail=f"Unknown check: {name}")

        start = time.monotonic()
        try:
            result = await check_fn()
            status = HealthStatus.HEALTHY if result else HealthStatus.FAILED
            return HealthCheck(
                name=name, status=status,
                detail="OK" if result else "FAILED",
                duration_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as e:
            return HealthCheck(
                name=name, status=HealthStatus.FAILED,
                detail=str(e),
                duration_ms=(time.monotonic() - start) * 1000,
            )

    async def run_all(self) -> dict:
        checks = {}
        for name in self._checks:
            checks[name] = await self.run_check(name)

        overall = HealthStatus.HEALTHY
        failures = [c for c in checks.values() if c.status == HealthStatus.FAILED]
        degraded = [c for c in checks.values() if c.status == HealthStatus.DEGRADED]

        if failures:
            overall = HealthStatus.FAILED
        elif degraded:
            overall = HealthStatus.DEGRADED

        return {
            "status": overall,
            "uptime_seconds": (datetime.now(timezone.utc) - self._started_at).total_seconds(),
            "checks": {
                name: {"status": c.status, "detail": c.detail, "duration_ms": round(c.duration_ms, 2)}
                for name, c in checks.items()
            },
        }

    async def run_liveness(self) -> dict:
        """Kubernetes liveness — just confirms the process is alive."""
        return {"status": HealthStatus.HEALTHY, "uptime_seconds":
                (datetime.now(timezone.utc) - self._started_at).total_seconds()}

    async def run_readiness(self) -> dict:
        """Kubernetes readiness — DB + Redis must be up."""
        checks = {}
        for name in ("database", "redis"):
            if name in self._checks:
                checks[name] = await self.run_check(name)

        overall = HealthStatus.HEALTHY
        if any(c.status == HealthStatus.FAILED for c in checks.values()):
            overall = HealthStatus.FAILED

        return {
            "status": overall,
            "checks": {n: {"status": c.status, "detail": c.detail} for n, c in checks.items()},
        }


# ── Pre-built health check functions ──────────────────────────────────────

async def check_database(db_session_factory=None) -> bool:
    """Ping the database."""
    if db_session_factory is None:
        return False  # Not configured
    try:
        async with db_session_factory() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def check_redis(redis_client=None) -> bool:
    """Ping Redis."""
    if redis_client is None:
        return False
    try:
        return await redis_client.ping()
    except Exception:
        return False


async def check_provider_espn(http_client=None) -> bool:
    """Check ESPN API reachability."""
    if http_client is None:
        return True  # Assume OK if no client configured
    try:
        resp = await http_client.get(
            "https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc?limit=1",
            timeout=10,
        )
        return resp.status_code == 200
    except Exception:
        return False


async def check_scheduler(manager=None) -> bool:
    """Check scheduler is running and not stuck."""
    if manager is None:
        return True
    try:
        status = await manager.get_status()
        # Degraded if any job has 3+ consecutive failures
        for job_name, job in status.get("health", {}).get("jobs", {}).items():
            if job.get("consecutive_failures", 0) >= 3:
                return False
        return status.get("running", False)
    except Exception:
        return False
