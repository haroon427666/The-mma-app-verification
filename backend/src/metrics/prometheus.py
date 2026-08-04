"""Production Prometheus Metrics — full prometheus_client integration.

Every metric the Grafana dashboards need. No more lightweight mock.
Exported at GET /metrics in Prometheus text format.

Metrics:
    api_requests_total{method, endpoint, status}
    api_latency_seconds{method, endpoint}          — Histogram (P50/P90/P99)
    sync_job_duration_seconds{job, status}         — Histogram
    sync_jobs_total{job, status}                    — Counter
    sync_records_total{job, operation}              — Counter (inserted/updated/errors)
    provider_requests_total{provider, status}       — Counter
    provider_latency_seconds{provider}              — Histogram
    scheduler_running_jobs                          — Gauge
    scheduler_queued_jobs                           — Gauge
    scheduler_failed_jobs_total                     — Counter
    cache_hits_total                                — Counter
    cache_misses_total                              — Counter
    db_connections_active                           — Gauge
    db_connections_idle                             — Gauge
    db_query_duration_seconds                       — Histogram
    login_attempts_total{status}                    — Counter
    failed_logins_total                             — Counter
    jwt_created_total                               — Counter
    jwt_revoked_total                               — Counter
    notification_sent_total{type}                   — Counter
    payload_archive_size_bytes                      — Gauge
"""

import logging
from typing import Any

try:
    from prometheus_client import REGISTRY, Counter, Gauge, Histogram, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)


class _NoOpMetric:
    """Dummy metric that silently accepts calls (no prometheus_client)."""

    def labels(self, **kw: Any) -> Any:
        return self

    def inc(self, amount: int = 1) -> None:
        pass

    def dec(self, amount: int = 1) -> None:
        pass

    def set(self, value: Any) -> None:
        pass

    def observe(self, value: Any) -> None:
        pass

    def time(self) -> Any:
        return _NoOpTimer()


class _NoOpTimer:
    def __enter__(self) -> Any:
        return self

    def __exit__(self, *a: object) -> None:
        pass


class Metrics:
    """Central metrics registry — all application metrics in one place.

    All metrics default to no-ops so they are safe to touch before
    ``setup()`` runs (e.g. during tests or before app startup).
    """

    api_requests: Any
    api_latency: Any
    sync_job_duration: Any
    sync_jobs_total: Any
    sync_records_total: Any
    provider_requests: Any
    provider_latency: Any
    scheduler_running: Any
    scheduler_queued: Any
    scheduler_failed: Any
    scheduler_retries: Any
    cache_hits: Any
    cache_misses: Any
    db_connections_active: Any
    db_connections_idle: Any
    db_query_duration: Any
    login_attempts: Any
    failed_logins: Any
    jwt_created: Any
    jwt_revoked: Any
    notifications_sent: Any
    payload_archive_size: Any

    def __init__(self) -> None:
        self._started = False
        self._init_mock()

    def setup(self) -> None:
        """Initialize all metrics. Call once at startup."""
        if self._started:
            return
        self._started = True

        if not PROMETHEUS_AVAILABLE:
            logger.warning("prometheus_client not installed — metrics disabled")
            return

        self._init_real()
        logger.info("Prometheus metrics initialized")

    def _init_real(self) -> None:
        # ── API ────────────────────────────────────────────────────
        self.api_requests = Counter(
            "api_requests_total", "Total API requests",
            ["method", "endpoint", "status"],
        )
        self.api_latency = Histogram(
            "api_latency_seconds", "API request latency",
            ["method", "endpoint"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        # ── Sync ───────────────────────────────────────────────────
        self.sync_job_duration = Histogram(
            "sync_job_duration_seconds", "Sync job duration",
            ["job", "status"],
            buckets=[1, 5, 15, 30, 60, 120, 300, 600, 900],
        )
        self.sync_jobs_total = Counter(
            "sync_jobs_total", "Sync job runs", ["job", "status"],
        )
        self.sync_records_total = Counter(
            "sync_records_total", "Records synced", ["job", "operation"],
        )

        # ── Provider ───────────────────────────────────────────────
        self.provider_requests = Counter(
            "provider_requests_total", "Provider API requests",
            ["provider", "status"],
        )
        self.provider_latency = Histogram(
            "provider_latency_seconds", "Provider API latency",
            ["provider"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )

        # ── Scheduler ──────────────────────────────────────────────
        self.scheduler_running = Gauge(
            "scheduler_running_jobs", "Currently running jobs",
        )
        self.scheduler_queued = Gauge(
            "scheduler_queued_jobs", "Jobs waiting in queue",
        )
        self.scheduler_failed = Counter(
            "scheduler_failed_jobs_total", "Total failed jobs", ["job"],
        )
        self.scheduler_retries = Counter(
            "scheduler_retries_total", "Job retry count", ["job"],
        )

        # ── Cache ──────────────────────────────────────────────────
        self.cache_hits = Counter("cache_hits_total", "Cache hits")
        self.cache_misses = Counter("cache_misses_total", "Cache misses")

        # ── Database ────────────────────────────────────────────────
        self.db_connections_active = Gauge(
            "db_connections_active", "Active DB connections",
        )
        self.db_connections_idle = Gauge(
            "db_connections_idle", "Idle DB connections",
        )
        self.db_query_duration = Histogram(
            "db_query_duration_seconds", "Database query duration",
            ["operation"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
        )

        # ── Auth ───────────────────────────────────────────────────
        self.login_attempts = Counter(
            "login_attempts_total", "Login attempts", ["status"],
        )
        self.failed_logins = Counter(
            "failed_logins_total", "Failed login attempts",
        )
        self.jwt_created = Counter("jwt_created_total", "JWTs issued")
        self.jwt_revoked = Counter("jwt_revoked_total", "JWTs revoked")

        # ── Notifications ──────────────────────────────────────────
        self.notifications_sent = Counter(
            "notification_sent_total", "Notifications sent", ["type"],
        )

        # ── Payload Archive ────────────────────────────────────────
        self.payload_archive_size = Gauge(
            "payload_archive_size_bytes", "Estimated payload archive size",
        )

    def _init_mock(self) -> None:
        """Wire up no-op metrics (default until ``setup()`` runs)."""
        self.api_requests = _NoOpMetric()
        self.api_latency = _NoOpMetric()
        self.sync_job_duration = _NoOpMetric()
        self.sync_jobs_total = _NoOpMetric()
        self.sync_records_total = _NoOpMetric()
        self.provider_requests = _NoOpMetric()
        self.provider_latency = _NoOpMetric()
        self.scheduler_running = _NoOpMetric()
        self.scheduler_queued = _NoOpMetric()
        self.scheduler_failed = _NoOpMetric()
        self.scheduler_retries = _NoOpMetric()
        self.cache_hits = _NoOpMetric()
        self.cache_misses = _NoOpMetric()
        self.db_connections_active = _NoOpMetric()
        self.db_connections_idle = _NoOpMetric()
        self.db_query_duration = _NoOpMetric()
        self.login_attempts = _NoOpMetric()
        self.failed_logins = _NoOpMetric()
        self.jwt_created = _NoOpMetric()
        self.jwt_revoked = _NoOpMetric()
        self.notifications_sent = _NoOpMetric()
        self.payload_archive_size = _NoOpMetric()

    def export(self) -> str:
        if PROMETHEUS_AVAILABLE:
            return generate_latest(REGISTRY).decode()
        return "# prometheus_client not installed\n"


# Singleton
_metrics = Metrics()


def get_metrics() -> Metrics:
    return _metrics


def setup_metrics() -> None:
    _metrics.setup()
