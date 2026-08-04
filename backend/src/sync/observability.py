"""
Observability — structured logging, Prometheus metrics, health checks, alerting.

Four pillars of production observability layered onto the sync engine:

1. StructuredLogger   — every log carries run_id, plan, provider, entity context
2. MetricsExporter    — SyncMetrics → Prometheus text format (scrape endpoint)
3. HealthChecker      — provider reachability, scheduler, circuit breaker status
4. AlertManager       — threshold-based triggers (dead letters, circuits, failures)

All components are read-only observers — they never mutate sync state.
"""

import logging
import time as _time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from src.sync.dead_letter import DeadLetterQueue
from src.sync.failure import CircuitBreaker
from src.sync.metrics import SyncMetrics
from src.sync.result import SyncResult
from src.sync.types import EntityType

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Structured Logger
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class StructuredLogger:
    """Context-aware logger for sync operations.

    Every log entry automatically includes run_id, provider_slug, plan_name.
    Use with Python's logging.LogAdapter for structured JSON output.

    Usage:
        slog = StructuredLogger()
        slog.sync_started("abc-123", "full_sync", "espn", 9)
        slog.job_completed("abc-123", EntityType.FIGHTER, result)
        slog.sync_completed("abc-123", sync_result)
    """

    def sync_started(
        self, run_id: str, plan_name: str, provider_slug: str, job_count: int
    ) -> None:
        logger.info(
            "sync.started",
            extra={
                "run_id": run_id,
                "plan": plan_name,
                "provider": provider_slug,
                "job_count": job_count,
                "event": "sync_started",
            },
        )

    def sync_completed(self, run_id: str, result: SyncResult) -> None:
        logger.info(
            "sync.completed",
            extra={
                "run_id": run_id,
                "status": result.overall_status.value,
                "duration_ms": round(result.duration_ms, 1),
                "jobs_total": result.total_jobs,
                "jobs_completed": result.completed_jobs,
                "jobs_failed": result.failed_jobs,
                "inserted": result.total_inserted,
                "updated": result.total_updated,
                "skipped": result.total_skipped,
                "errors": result.total_errors,
                "api_calls": result.total_api_calls,
                "event": "sync_completed",
            },
        )

    def job_started(
        self, run_id: str, entity_type: EntityType, mode: str
    ) -> None:
        logger.info(
            "sync.job_started",
            extra={
                "run_id": run_id,
                "entity": entity_type.value,
                "mode": mode,
                "event": "job_started",
            },
        )

    def job_completed(
        self, run_id: str, entity_type: EntityType,
        inserted: int, updated: int, skipped: int, errors: int,
        duration_ms: float,
    ) -> None:
        logger.info(
            "sync.job_completed",
            extra={
                "run_id": run_id,
                "entity": entity_type.value,
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
                "duration_ms": round(duration_ms, 1),
                "event": "job_completed",
            },
        )

    def batch_progress(
        self, run_id: str, entity_type: EntityType,
        batch_num: int, items: int, progress_pct: float,
    ) -> None:
        logger.debug(
            "sync.batch",
            extra={
                "run_id": run_id,
                "entity": entity_type.value,
                "batch": batch_num,
                "items": items,
                "progress_pct": progress_pct,
                "event": "batch_complete",
            },
        )

    def failure(
        self, run_id: str, entity_type: EntityType | None,
        error: str, category: str,
    ) -> None:
        logger.error(
            "sync.failure",
            extra={
                "run_id": run_id,
                "entity": entity_type.value if entity_type else "unknown",
                "error": error[:200],
                "category": category,
                "event": "failure",
            },
        )

    def circuit_open(self, provider_slug: str, trips: int) -> None:
        logger.warning(
            "sync.circuit_open",
            extra={
                "provider": provider_slug,
                "total_trips": trips,
                "event": "circuit_open",
            },
        )

    def circuit_close(self, provider_slug: str) -> None:
        logger.info(
            "sync.circuit_close",
            extra={
                "provider": provider_slug,
                "event": "circuit_close",
            },
        )

    def dead_letter_added(
        self, entity_type: str, external_id: str, category: str,
    ) -> None:
        logger.warning(
            "sync.dead_letter",
            extra={
                "entity": entity_type,
                "external_id": external_id,
                "category": category,
                "event": "dead_letter",
            },
        )

    def alert_triggered(
        self, alert_name: str, severity: str, detail: str,
    ) -> None:
        logger.error(
            "sync.alert",
            extra={
                "alert": alert_name,
                "severity": severity,
                "detail": detail[:300],
                "event": "alert",
            },
        )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Metrics Exporter (Prometheus)
# ═══════════════════════════════════════════════════════════════════════════════


class MetricsExporter:
    """Converts SyncMetrics to Prometheus text format.

    Usage: mount at /metrics for Prometheus scrape.
        exporter = MetricsExporter()
        text = exporter.to_prometheus(sync_metrics)
    """

    @staticmethod
    def to_prometheus(
        metrics: SyncMetrics,
        plan_name: str = "",
        provider_slug: str = "",
    ) -> str:
        """Export SyncMetrics as Prometheus text format.

        Produces counters and gauges with labels for entity, plan, provider.
        """
        lines: list[str] = []

        # ── HELP + TYPE ──────────────────────────────────────────────────
        lines.append("# HELP sync_inserted_total Number of rows inserted per entity")
        lines.append("# TYPE sync_inserted_total counter")
        for entity, m in metrics.entities.items():
            lines.append(
                f'sync_inserted_total{{entity="{entity}",plan="{plan_name}",'
                f'provider="{provider_slug}"}} {m.inserted}'
            )

        lines.append("# HELP sync_updated_total Number of rows updated per entity")
        lines.append("# TYPE sync_updated_total counter")
        for entity, m in metrics.entities.items():
            lines.append(
                f'sync_updated_total{{entity="{entity}",plan="{plan_name}",'
                f'provider="{provider_slug}"}} {m.updated}'
            )

        lines.append("# HELP sync_skipped_total Number of rows skipped per entity")
        lines.append("# TYPE sync_skipped_total counter")
        for entity, m in metrics.entities.items():
            lines.append(
                f'sync_skipped_total{{entity="{entity}",plan="{plan_name}",'
                f'provider="{provider_slug}"}} {m.skipped}'
            )

        lines.append("# HELP sync_errors_total Number of row-level errors per entity")
        lines.append("# TYPE sync_errors_total counter")
        for entity, m in metrics.entities.items():
            lines.append(
                f'sync_errors_total{{entity="{entity}",plan="{plan_name}",'
                f'provider="{provider_slug}"}} {m.errors}'
            )

        # ── Duration ─────────────────────────────────────────────────────
        lines.append("# HELP sync_duration_ms Total sync run duration in milliseconds")
        lines.append("# TYPE sync_duration_ms gauge")
        lines.append(
            f'sync_duration_ms{{plan="{plan_name}",provider="{provider_slug}"}} '
            f'{round(metrics.total_duration_ms, 1)}'
        )

        # ── Provider ─────────────────────────────────────────────────────
        lines.append("# HELP sync_api_calls_total Total provider API calls")
        lines.append("# TYPE sync_api_calls_total counter")
        lines.append(
            f'sync_api_calls_total{{provider="{provider_slug}"}} '
            f'{metrics.provider.calls}'
        )

        lines.append("# HELP sync_api_latency_ms Total provider latency")
        lines.append("# TYPE sync_api_latency_ms gauge")
        lines.append(
            f'sync_api_latency_ms{{provider="{provider_slug}"}} '
            f'{round(metrics.provider.latency_ms, 1)}'
        )

        lines.append("# HELP sync_rate_limited_total Number of 429 responses")
        lines.append("# TYPE sync_rate_limited_total counter")
        lines.append(
            f'sync_rate_limited_total{{provider="{provider_slug}"}} '
            f'{metrics.provider.rate_limited}'
        )

        # ── Database ─────────────────────────────────────────────────────
        lines.append("# HELP sync_db_inserts_total Database inserts")
        lines.append("# TYPE sync_db_inserts_total counter")
        lines.append(f"sync_db_inserts_total {metrics.database.inserts}")

        lines.append("# HELP sync_db_updates_total Database updates")
        lines.append("# TYPE sync_db_updates_total counter")
        lines.append(f"sync_db_updates_total {metrics.database.updates}")

        lines.append("# HELP sync_db_latency_ms Total database write latency")
        lines.append("# TYPE sync_db_latency_ms gauge")
        lines.append(
            f"sync_db_latency_ms {round(metrics.database.latency_ms, 1)}"
        )

        # ── HTTP ─────────────────────────────────────────────────────────
        lines.append("# HELP sync_http_2xx_total Successful HTTP responses")
        lines.append("# TYPE sync_http_2xx_total counter")
        lines.append(f"sync_http_2xx_total {metrics.http.total_2xx}")

        lines.append("# HELP sync_http_4xx_total Client error responses")
        lines.append("# TYPE sync_http_4xx_total counter")
        lines.append(f"sync_http_4xx_total {metrics.http.total_4xx}")

        lines.append("# HELP sync_http_5xx_total Server error responses")
        lines.append("# TYPE sync_http_5xx_total counter")
        lines.append(f"sync_http_5xx_total {metrics.http.total_5xx}")

        lines.append("# HELP sync_http_retries_total Total retries")
        lines.append("# TYPE sync_http_retries_total counter")
        lines.append(f"sync_http_retries_total {metrics.http.total_retries}")

        return "\n".join(lines) + "\n"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Health Checker
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ProviderHealth:
    """Health status of one data provider."""

    provider_slug: str
    reachable: bool = False
    last_check: datetime | None = None
    response_time_ms: float = 0.0
    error: str | None = None
    circuit_state: str = "CLOSED"


@dataclass
class SchedulerHealth:
    """Health status of the scheduler."""

    running: bool = False
    total_definitions: int = 0
    active_schedules: int = 0
    running_jobs: int = 0
    next_run: str | None = None


@dataclass
class SystemHealth:
    """Aggregate health check result."""

    status: str = "healthy"  # healthy, degraded, unhealthy
    checked_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    providers: dict[str, ProviderHealth] = field(default_factory=dict)
    scheduler: SchedulerHealth = field(default_factory=SchedulerHealth)
    dead_letters: dict[str, int] = field(default_factory=dict)
    circuit_breakers: dict[str, str] = field(default_factory=dict)


class HealthChecker:
    """Aggregates health information from all observability sources.

    Read-only — never mutates sync state. Safe to call from any thread.

    Usage: mount at /health for load balancer / Kubernetes liveness probe.
        checker = HealthChecker(providers, scheduler)
        health = await checker.check()
        if health.status != "healthy":
            alert()
    """

    def __init__(
        self,
        providers: dict[str, Any] | None = None,
        scheduler: Any | None = None,
        circuit_breakers: dict[str, CircuitBreaker] | None = None,
        dead_letter: DeadLetterQueue | None = None,
    ) -> None:
        self._providers = providers or {}
        self._scheduler = scheduler
        self._circuit_breakers = circuit_breakers or {}
        self._dead_letter = dead_letter

    async def check(self) -> SystemHealth:
        """Run a full health check across all components."""
        health = SystemHealth()
        degraded = False

        # ── Provider health ───────────────────────────────────────────────
        for slug, provider in self._providers.items():
            p_health = await self._check_provider(slug, provider)
            health.providers[slug] = p_health
            if not p_health.reachable:
                degraded = True

        # ── Scheduler health ──────────────────────────────────────────────
        if self._scheduler:
            health.scheduler = self._check_scheduler()

        # ── Circuit breaker status ────────────────────────────────────────
        for slug, cb in self._circuit_breakers.items():
            health.circuit_breakers[slug] = cb.state.value
            if cb.is_open:
                degraded = True

        # ── Dead letter stats ─────────────────────────────────────────────
        if self._dead_letter:
            health.dead_letters = self._dead_letter.stats()

        if degraded:
            health.status = "degraded"

        return health

    async def _check_provider(
        self, slug: str, provider: Any
    ) -> ProviderHealth:
        """Check if a provider is reachable with a lightweight request."""
        p_health = ProviderHealth(provider_slug=slug)
        p_health.last_check = datetime.now(UTC)

        # Check circuit breaker first
        cb = self._circuit_breakers.get(slug)
        if cb:
            p_health.circuit_state = cb.state.value

        # Lightweight probe: try a simple API call or HEAD request
        try:
            if hasattr(provider, "health_check"):
                start = _time.monotonic()
                await provider.health_check()
                p_health.response_time_ms = (_time.monotonic() - start) * 1000
                p_health.reachable = True
            else:
                # No health check method — assume reachable
                p_health.reachable = True
        except Exception as e:
            p_health.reachable = False
            p_health.error = str(e)[:200]

        return p_health

    def _check_scheduler(self) -> SchedulerHealth:
        """Check scheduler status."""
        if self._scheduler is None:
            return SchedulerHealth(running=False)
        try:
            status = self._scheduler.get_status()
            return SchedulerHealth(
                running=True,
                total_definitions=status.get("total_definitions", 0),
                active_schedules=status.get("active_schedules", 0),
                running_jobs=status.get("running_jobs", 0),
                next_run=(
                    status["jobs"][0]["next_run"]
                    if status.get("jobs")
                    else None
                ),
            )
        except Exception:
            return SchedulerHealth(running=False)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Alert Manager
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class AlertThresholds:
    """Configurable thresholds for alert triggers."""

    dead_letter_count: int = 50
    """Fire alert when dead-letter queue exceeds this count."""

    consecutive_failures: int = 3
    """Fire alert when a sync has this many consecutive failures."""

    circuit_open_providers: int = 1
    """Fire alert when this many providers have open circuits."""

    sync_duration_warning_ms: float = 300_000  # 5 minutes
    """Fire warning when sync duration exceeds this."""


@dataclass
class Alert:
    """A triggered alert."""

    name: str
    severity: str  # info, warning, critical
    message: str
    triggered_at: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat()
    )
    detail: dict[str, Any] = field(default_factory=dict)


class AlertManager:
    """Threshold-based alert triggers.

    Does NOT send alerts directly. Instead, fires alerts that
    event handlers (Slack, email, PagerDuty) can subscribe to.

    Usage:
        alerts = AlertManager(dead_letter=dlq, thresholds=AlertThresholds())
        triggered = await alerts.check_all()
        for alert in triggered:
            await event_bus.fire_alert(alert)
    """

    def __init__(
        self,
        dead_letter: DeadLetterQueue | None = None,
        circuit_breakers: dict[str, CircuitBreaker] | None = None,
        thresholds: AlertThresholds | None = None,
        structured_logger: StructuredLogger | None = None,
    ) -> None:
        self._dead_letter = dead_letter
        self._circuit_breakers = circuit_breakers or {}
        self._thresholds = thresholds or AlertThresholds()
        self._slog = structured_logger or StructuredLogger()

    async def check_all(self) -> list[Alert]:
        """Run all alert checks. Returns triggered alerts."""
        alerts: list[Alert] = []

        alerts += await self.check_dead_letters()
        alerts += await self.check_circuit_breakers()
        # check_consecutive_failures and check_sync_duration are called
        # per-run, not globally — see check_run_result()

        return alerts

    async def check_dead_letters(self) -> list[Alert]:
        """Alert if dead-letter queue exceeds threshold."""
        if self._dead_letter is None:
            return []

        total = self._dead_letter.count()
        if total >= self._thresholds.dead_letter_count:
            stats = self._dead_letter.stats()
            msg = f"Dead-letter queue: {total} records (threshold: {self._thresholds.dead_letter_count})"
            alert = Alert(
                name="dead_letter_backlog",
                severity="critical" if total >= 200 else "warning",
                message=msg,
                detail={"count": total, "by_entity": stats},
            )
            self._slog.alert_triggered(alert.name, alert.severity, msg)
            return [alert]
        return []

    async def check_circuit_breakers(self) -> list[Alert]:
        """Alert if circuit breakers are open."""
        alerts: list[Alert] = []
        open_count = sum(1 for cb in self._circuit_breakers.values() if cb.is_open)

        if open_count >= self._thresholds.circuit_open_providers:
            open_providers = [
                slug for slug, cb in self._circuit_breakers.items()
                if cb.is_open
            ]
            msg = f"Circuit breakers OPEN: {open_providers}"
            alert = Alert(
                name="circuit_breakers_open",
                severity="critical",
                message=msg,
                detail={"open_providers": open_providers, "count": open_count},
            )
            self._slog.alert_triggered(alert.name, alert.severity, msg)
            alerts.append(alert)

        return alerts

    def check_run_result(self, run_id: str, result: SyncResult) -> list[Alert]:
        """Check a completed sync run for threshold violations."""
        alerts: list[Alert] = []

        if result.overall_status.value == "FAILED":
            failed_jobs = [
                j for j in result.job_results
                if j.status.value == "FAILED"
            ]
            msg = f"Sync run {run_id} FAILED: {len(failed_jobs)} jobs failed"
            alerts.append(Alert(
                name="sync_run_failed",
                severity="critical",
                message=msg,
                detail={"run_id": run_id, "failed_jobs": len(failed_jobs)},
            ))
            self._slog.alert_triggered("sync_run_failed", "critical", msg)

        if result.total_errors > 0:
            msg = f"Sync run {run_id}: {result.total_errors} total errors"
            alerts.append(Alert(
                name="sync_errors",
                severity="warning",
                message=msg,
                detail={"run_id": run_id, "errors": result.total_errors},
            ))

        if result.duration_ms > self._thresholds.sync_duration_warning_ms:
            msg = (
                f"Sync run {run_id}: {result.duration_ms:.0f}ms "
                f"(threshold: {self._thresholds.sync_duration_warning_ms:.0f}ms)"
            )
            alerts.append(Alert(
                name="sync_slow",
                severity="warning",
                message=msg,
                detail={"run_id": run_id, "duration_ms": result.duration_ms},
            ))
            self._slog.alert_triggered("sync_slow", "warning", msg)

        return alerts
