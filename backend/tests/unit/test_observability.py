"""Observability tests — metrics wiring, no-op safety, cache/metrics hooks."""

from typing import Any

import pytest

from src.metrics.prometheus import get_metrics, setup_metrics


class TestMetricsRegistry:
    def test_metrics_are_noop_before_setup(self) -> None:
        """All metrics must be usable (no-op) before setup() runs."""
        m = get_metrics()
        m.api_requests.labels(method="GET", endpoint="/x", status="200").inc()
        m.api_latency.labels(method="GET", endpoint="/x").observe(0.05)
        m.cache_hits.inc()
        m.cache_misses.inc()
        m.db_connections_active.set(1)
        m.login_attempts.labels(status="failed").inc()
        m.export()  # Never raises

    def test_setup_initializes_real_metrics(self) -> None:
        setup_metrics()  # idempotent
        m = get_metrics()
        # Real prometheus_client metric classes expose inc/observe
        m.api_requests.labels(method="GET", endpoint="/health", status="200").inc()
        m.sync_jobs_total.labels(job="rankings", status="success").inc()
        output = m.export()
        assert "api_requests_total" in output
        assert "sync_jobs_total" in output

    def test_setup_is_idempotent(self) -> None:
        setup_metrics()
        setup_metrics()  # No error on second call


class TestSchedulerMetricsCollector:
    def test_collector_never_raises_before_setup(self) -> None:
        from src.monitoring.scheduler_metrics import SchedulerMetricsCollector
        c = SchedulerMetricsCollector()
        c.record_job_start("rankings")
        c.record_job_finish("rankings", "success", 123.4)
        c.record_job_failed("rankings", 50.0)
        c.record_retry("rankings")
        c.record_queue_size(3, 1)
        c.record_records_synced("rankings", inserted=5, updated=2, errors=1)
        c.record_provider_call("espn", "success", 250.0)
        c.record_login("failed")
        c.record_jwt_created()
        c.record_jwt_revoked()
        c.record_cache(True)
        c.record_api_request("GET", "/api/v1/events", 200, 12.5)

    def test_collector_records_into_prometheus_after_setup(self) -> None:
        from src.metrics.prometheus import get_metrics as gm

        setup_metrics()
        before = _counter_value(gm().scheduler_failed, job="rankings")
        from src.monitoring.scheduler_metrics import SchedulerMetricsCollector
        SchedulerMetricsCollector().record_job_failed("rankings")
        after = _counter_value(gm().scheduler_failed, job="rankings")
        assert after == before + 1


def _counter_value(counter: Any, **labels: Any) -> int:
    from prometheus_client import Counter

    if isinstance(counter, Counter):
        if labels:
            return int(counter.labels(**labels)._value.get())
        return int(counter._value.get())
    return -1  # no-op metrics


class TestCacheMetricsHook:
    @pytest.mark.asyncio
    async def test_cache_hit_increments_prometheus_counter(self) -> None:
        from src.metrics.prometheus import get_metrics as gm
        from src.middleware.cache import MemoryCacheManager

        setup_metrics()
        cache = MemoryCacheManager()
        await cache.get("missing")

        misses_before = _counter_value(gm().cache_misses)
        assert misses_before >= 1

    @pytest.mark.asyncio
    async def test_cache_metrics_recorded_on_set_get(self) -> None:
        from src.metrics.prometheus import get_metrics as gm
        from src.middleware.cache import MemoryCacheManager

        setup_metrics()
        cache = MemoryCacheManager()

        hits_before = _counter_value(gm().cache_hits)
        await cache.set("k", "v", 300)
        await cache.get("k")
        hits_after = _counter_value(gm().cache_hits)
        assert hits_after == hits_before + 1
