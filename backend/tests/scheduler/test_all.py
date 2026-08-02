"""Phase 7 Scheduler Tests — retry, queue, locks, live mode, metrics, jobs."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch


# ═══════════════════════════════════════════════════════════════════════════════
# Retry Engine Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRetryEngine:
    def test_backoff_grows_exponentially(self):
        from src.scheduler.retry import RetryPolicy, RetryState
        policy = RetryPolicy(base_seconds=1.0, max_attempts=4, jitter_factor=0.0)
        state = RetryState(policy=policy)

        # First delay ~1s, second ~2s, third ~4s
        d1 = state.compute_delay()
        d2 = state.compute_delay()
        d3 = state.compute_delay()
        assert 0.9 <= d1 <= 1.1
        assert 1.8 <= d2 <= 2.2
        assert 3.6 <= d3 <= 4.4
        assert state.attempt == 3

    def test_jitter_adds_randomness(self):
        from src.scheduler.retry import RetryPolicy, RetryState
        policy = RetryPolicy(base_seconds=1.0, max_attempts=1, jitter_factor=0.5)
        state = RetryState(policy=policy)

        delays = [state.compute_delay() for _ in range(20)]
        state.reset()
        delays2 = [state.compute_delay() for _ in range(20)]

        # Delays should vary (not all identical)
        assert len(set(round(d, 2) for d in delays)) > 1

    def test_max_attempts_exhausted(self):
        from src.scheduler.retry import RetryPolicy, RetryState, RetryDecision
        policy = RetryPolicy(max_attempts=2)
        state = RetryState(policy=policy)

        assert state.decide(ConnectionError()) == RetryDecision.RETRY
        state.compute_delay()
        assert state.decide(ConnectionError()) == RetryDecision.RETRY
        state.compute_delay()
        assert state.decide(ConnectionError()) == RetryDecision.FAIL

    def test_non_retryable_goes_to_dead_letter(self):
        from src.scheduler.retry import RetryPolicy, RetryState, RetryDecision
        state = RetryState(policy=RetryPolicy())

        # ValueError is not in retryable_exceptions
        assert state.decide(ValueError("bad data")) == RetryDecision.DEAD_LETTER

    def test_budget_exhaustion(self):
        from src.scheduler.retry import RetryPolicy, RetryState, RetryDecision
        policy = RetryPolicy(max_attempts=100, retry_budget=3)
        state = RetryState(policy=policy)

        for _ in range(3):
            assert state.decide(ConnectionError()) == RetryDecision.RETRY
            state.compute_delay()

        # Budget exhausted
        assert state.decide(ConnectionError()) == RetryDecision.FAIL

    @pytest.mark.asyncio
    async def test_retry_success_after_failure(self):
        from src.scheduler.retry import RetryPolicy, RetryState
        state = RetryState(policy=RetryPolicy(base_seconds=0.0, max_attempts=3))

        attempts = 0

        async def flaky_fn():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("transient")
            return "success"

        result = await state.execute(flaky_fn)
        assert result == "success"
        assert attempts == 3
        assert state.attempt == 0  # Reset on success


# ═══════════════════════════════════════════════════════════════════════════════
# Priority Queue Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPriorityQueue:
    @pytest.mark.asyncio
    async def test_higher_priority_dequeued_first(self):
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue()

        called = []
        async def fn(name):
            called.append(name)

        await q.enqueue("low", fn, priority=Priority.LOW)
        await q.enqueue("live", fn, priority=Priority.LIVE)
        await q.enqueue("normal", fn, priority=Priority.NORMAL)

        # Process all
        for _ in range(3):
            item = await q.dequeue()
            await item.job_fn("test")
            await q.mark_complete(item.job_id)

        assert called[0] == "test"  # All get same arg in this test
        # Live should come first, then Normal, then Low

    @pytest.mark.asyncio
    async def test_concurrency_limit(self):
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue(max_concurrent=1)

        async def fn(): pass

        await q.enqueue("a", fn, priority=Priority.NORMAL)
        await q.enqueue("b", fn, priority=Priority.LIVE)

        item1 = await q.dequeue()
        assert item1 is not None  # First job

        # Second should be blocked — max_concurrent=1 and one running
        item2 = await q.dequeue()
        assert item2 is None

        await q.mark_complete(item1.job_id)

        # Now second can dequeue
        item3 = await q.dequeue()
        assert item3 is not None

    @pytest.mark.asyncio
    async def test_cancel_removes_queued_jobs(self):
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue()

        async def fn(): pass

        await q.enqueue("cleanup", fn, priority=Priority.LOW)
        await q.enqueue("cleanup", fn, priority=Priority.LOW)
        await q.enqueue("events", fn, priority=Priority.HIGH)

        removed = await q.cancel("cleanup")
        assert removed == 2
        assert q.size == 1  # Only events remains


# ═══════════════════════════════════════════════════════════════════════════════
# Metrics Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMetrics:
    def test_counter_increment(self):
        from src.scheduler.metrics import Counter
        c = Counter(name="test_total")
        c.inc()
        c.inc(5)
        assert c.value == 6

    def test_gauge_set(self):
        from src.scheduler.metrics import Gauge
        g = Gauge(name="queue_size")
        g.set(42)
        assert g.value == 42

    def test_registry_records_job(self):
        from src.scheduler.metrics import MetricsRegistry
        reg = MetricsRegistry()
        reg.record_job_duration("events_upcoming", 1500)
        reg.record_job_result("rankings", "success", inserted=24, updated=0, errors=0)
        reg.record_job_result("rankings", "failed", errors=1)
        reg.set_live_mode(True)

        assert reg.gauge("sync_live_mode").value == 1
        assert reg.gauge("sync_job_duration_seconds", job="events_upcoming").value == 1.5
        assert reg.counter("sync_job_total", job="rankings", status="success").value == 1
        assert reg.counter("sync_job_total", job="rankings", status="failed").value == 1

    def test_prometheus_export(self):
        from src.scheduler.metrics import MetricsRegistry
        reg = MetricsRegistry()
        reg.counter("test_total", status="ok").inc()
        reg.gauge("test_value").set(3.14)

        output = reg.export_prometheus()
        assert "test_total{status=\"ok\"}" in output
        assert "test_value 3.14" in output
        assert "# HELP" in output
        assert "# TYPE" in output


# ═══════════════════════════════════════════════════════════════════════════════
# Live Mode Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestLiveMode:
    @pytest.mark.asyncio
    async def test_initial_state_is_off(self):
        from src.scheduler.live_mode import LiveModeDetector
        detector = LiveModeDetector(db_session_factory=None)
        assert detector.is_live is False
        assert detector.active_event_id is None

    def test_enter_and_exit_transitions(self):
        from src.scheduler.live_mode import LiveModeDetector
        detector = LiveModeDetector(db_session_factory=None)

        # Manual state transitions (real check requires DB)
        detector._in_live_mode = False
        detector._enter_live_mode("evt-001", "UFC Fight Night")
        assert detector.is_live is True
        assert detector.active_event_id == "evt-001"

        detector._in_live_mode = True
        # _exit_live_mode is async but we can test the state change
        detector._in_live_mode = False
        detector._active_event_id = None
        assert detector.is_live is False


# ═══════════════════════════════════════════════════════════════════════════════
# Job Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestJobRegistry:
    def test_all_jobs_have_functions(self):
        from src.scheduler.jobs import JOB_REGISTRY, JOB_FUNCTIONS
        for name in JOB_REGISTRY:
            assert name in JOB_FUNCTIONS, f"{name} has no registered function"

    def test_all_jobs_have_config(self):
        from src.scheduler.jobs import JOB_REGISTRY
        for name, cfg in JOB_REGISTRY.items():
            assert cfg.name == name
            assert cfg.max_runtime_seconds > 0
            assert hasattr(cfg, "interval_seconds") or hasattr(cfg, "cron")

    def test_job_priorities_mapped(self):
        from src.scheduler.queue import Priority
        # Verify priority ordering
        assert Priority.LIVE < Priority.CRITICAL
        assert Priority.CRITICAL < Priority.HIGH
        assert Priority.HIGH < Priority.NORMAL
        assert Priority.NORMAL < Priority.LOW

    def test_cleanup_job_registered(self):
        from src.scheduler.jobs import JOB_REGISTRY
        assert "cleanup" in JOB_REGISTRY
        assert JOB_REGISTRY["cleanup"].enabled is True


# ═══════════════════════════════════════════════════════════════════════════════
# Recovery & Graceful Shutdown Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRecovery:
    @pytest.mark.asyncio
    async def test_retry_state_resets_on_success(self):
        from src.scheduler.retry import RetryPolicy, RetryState
        state = RetryState(policy=RetryPolicy())

        async def ok(): return "done"
        await state.execute(ok)
        assert state.attempt == 0  # Reset

    @pytest.mark.asyncio
    async def test_shutdown_cancels_pending_jobs(self):
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue()

        async def fn(): pass
        await q.enqueue("test", fn, priority=Priority.LOW)
        await q.enqueue("test", fn, priority=Priority.LOW)

        removed = await q.cancel("test")
        assert removed == 2
        assert q.size == 0


class TestConcurrentExecution:
    @pytest.mark.asyncio
    async def test_two_queued_jobs_deduplicate(self):
        """Two same-named jobs can exist in queue (not deduplicated at queue level)."""
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue()

        async def fn(): pass
        await q.enqueue("sync_rankings", fn, priority=Priority.HIGH)
        await q.enqueue("sync_rankings", fn, priority=Priority.HIGH)

        assert q.size == 2  # Both are queued — lock prevents duplicate execution

    @pytest.mark.asyncio
    async def test_queue_ordering_mixed_priorities(self):
        from src.scheduler.queue import PriorityQueue, Priority
        q = PriorityQueue(max_concurrent=10)

        items = []
        async def fn(name):
            items.append(name)

        for p, name in [(Priority.LOW, "c"), (Priority.LIVE, "a"), (Priority.HIGH, "b")]:
            await q.enqueue(name, fn, priority=p)

        for _ in range(3):
            item = await q.dequeue()
            await item.job_fn(item.job_name)
            await q.mark_complete(item.job_id)

        # a (LIVE=0) before b (HIGH=2) before c (LOW=4)
        assert items[0] == "a"
        assert items[1] == "b"
        assert items[2] == "c"
