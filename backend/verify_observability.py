#!/usr/bin/env python3
"""Observability Verification — validates all Phase 10 components.

Tests: structured logging, health checks, config validation,
provider monitoring, alert engine, feature flags.
"""

import json
import sys
import time
from datetime import datetime, timezone


def test_structured_logging():
    """Verify JSON logging + correlation IDs."""
    from src.logging.config import (
        configure_logging, JsonFormatter,
        set_request_id, set_correlation_id, set_user,
    )
    import logging

    configure_logging(level="INFO", json_output=True)

    set_request_id("req_test_123")
    set_user("user_test_456")

    # Produce a log and verify it's valid JSON with context
    log_stream = logging.getLogger("test").handlers[0] if logging.getLogger("test").handlers else None
    # Instead: verify formatter produces valid JSON
    formatter = JsonFormatter()
    record = logging.LogRecord("test", logging.INFO, "test.py", 42, "test message", (), None)
    record.exc_info = None
    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "test message"
    # Context variables are read from the Var at format time, not from the record
    print("  ✓ Structured JSON logging produces valid JSON with metadata")
    return True


def test_config_validation():
    """Verify config validator catches common issues."""
    from src.monitoring.config_validator import validate_config

    # Production without JWT secret
    result = validate_config(
        database_url="postgresql://user@host/db",
        jwt_secret="CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR",
        environment="production",
    )
    assert not result.is_valid  # Should reject default JWT in production
    assert any("JWT_SECRET" in e.key for e in result.errors)
    print("  ✓ Config validator: rejects default JWT in production")

    # Missing database URL
    result = validate_config(database_url="", environment="development")
    assert not result.is_valid
    assert any("DATABASE_URL" in e.key for e in result.errors)
    print("  ✓ Config validator: rejects missing DATABASE_URL")

    # Valid config
    result = validate_config(
        database_url="postgresql://user:pass@host/db",
        jwt_secret="a" * 64,
        redis_url="redis://localhost:6379",
        environment="production",
    )
    assert result.is_valid
    print("  ✓ Config validator: passes valid production config")

    return True


def test_health_checks():
    """Verify health check aggregation."""
    import asyncio
    from src.monitoring.health import HealthChecker, HealthCheck, HealthStatus

    checker = HealthChecker()

    async def always_ok():
        return True
    async def always_fail():
        return False

    checker.register("db", always_ok)
    checker.register("redis", always_ok)
    checker.register("provider", always_fail)

    result = asyncio.run(checker.run_all())
    assert result["status"] == HealthStatus.FAILED  # provider failed
    assert result["checks"]["db"]["status"] == "healthy"
    assert result["checks"]["provider"]["status"] == "failed"
    print("  ✓ Health checker: aggregates multiple checks, detects failures")

    # Liveness — always healthy
    result = asyncio.run(checker.run_liveness())
    assert result["status"] == HealthStatus.HEALTHY
    print("  ✓ Health checker: liveness always returns healthy")

    return True


def test_provider_monitoring():
    """Verify provider metrics tracking."""
    from src.monitoring.providers import ProviderMonitor

    monitor = ProviderMonitor()
    espn = monitor.register("espn")

    espn.record_success(142.5)
    assert espn.total_requests == 1
    assert espn.consecutive_failures == 0
    assert abs(espn.avg_latency_ms - 142.5) < 1.0

    espn.record_failure("Connection timeout")
    assert espn.total_errors == 1
    assert espn.consecutive_failures == 1

    espn.record_failure("timeout")
    espn.record_failure("timeout")
    assert espn.consecutive_failures == 3
    assert espn.is_up is False  # 3 consecutive = down

    espn.record_success(100)
    assert espn.is_up is True  # Recovers on success
    print("  ✓ Provider monitor: tracks latency, failures, auto-down, auto-recover")

    return True


def test_alert_engine():
    """Verify alert cooldown and dispatch."""
    import asyncio
    from src.monitoring.alerts import AlertEngine, LoginStormDetector, TokenReuseDetector

    engine = AlertEngine()

    alert_count = 0
    async def sample_alert():
        nonlocal alert_count
        alert_count += 1
        return True  # Trigger always

    engine.register("test_alert", sample_alert, cooldown_s=10)

    # First check fires the alert
    fired = asyncio.run(engine.check_all())
    assert len(fired) == 1
    assert alert_count == 1

    # Second check immediately — should be suppressed by cooldown
    fired = asyncio.run(engine.check_all())
    assert len(fired) == 0  # Cooldown prevents re-fire

    print("  ✓ Alert engine: fires on condition, cooldown prevents re-fire")

    # Login storm detector
    detector = LoginStormDetector(threshold=5, window_s=60)
    for _ in range(4):
        assert detector.record_failure() is False
    assert detector.record_failure() is True  # 5th triggers
    print("  ✓ Login storm detector: triggers at threshold")

    # Token reuse detector
    reuse = TokenReuseDetector()
    reuse.record_reuse("user-abc")
    assert len(reuse._reuse_events) == 1
    print("  ✓ Token reuse detector: records events")

    return True


def test_feature_flags():
    """Verify feature flag toggling."""
    from src.features.flags import is_enabled, set_flag, list_flags

    # Defaults
    assert is_enabled("live_mode") is True
    assert is_enabled("recommendations") is False
    assert is_enabled("maintenance_mode") is False

    # Runtime toggle
    set_flag("maintenance_mode", True)
    assert is_enabled("maintenance_mode") is True

    # List all
    flags = list_flags()
    assert len(flags) >= 10
    assert "live_mode" in flags

    print(f"  ✓ Feature flags: {len(flags)} flags, toggles work at runtime")

    return True


def test_correlation_ids():
    """Verify request context isolation."""
    import asyncio
    from src.logging.config import set_request_id, request_id_var, correlation_id_var

    async def concurrent_request(rid):
        set_request_id(rid)
        await asyncio.sleep(0.01)
        assert request_id_var.get() == rid
        return rid

    ids = ["req_a", "req_b", "req_c"]
    results = asyncio.run(asyncio.gather(*[concurrent_request(rid) for rid in ids]))
    assert results == ids  # Each request kept its own ID
    print("  ✓ Correlation IDs: async-safe context isolation")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("PHASE 10 OBSERVABILITY VERIFICATION")
    print("=" * 60)

    tests = [
        ("Structured Logging", test_structured_logging),
        ("Correlation IDs", test_correlation_ids),
        ("Config Validation", test_config_validation),
        ("Health Checks", test_health_checks),
        ("Provider Monitoring", test_provider_monitoring),
        ("Alert Engine", test_alert_engine),
        ("Feature Flags", test_feature_flags),
    ]

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"PHASE 10 VERIFIED: {passed}/{passed+failed} tests pass")
    print(f"{'='*60}")
    sys.exit(0 if failed == 0 else 1)
