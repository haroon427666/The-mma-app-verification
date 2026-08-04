"""Health/readiness endpoint tests — real check wiring, no live services."""

from typing import Any

import pytest

from src.config import settings
from src.monitoring.health import HealthChecker, HealthStatus


class TestHealthChecker:
    async def test_readiness_healthy_when_checks_pass(self) -> None:
        checker = HealthChecker()

        async def ok() -> bool:
            return True

        checker.register("database", ok)
        checker.register("redis", ok)
        result = await checker.run_readiness()
        assert result["status"] == HealthStatus.HEALTHY
        assert set(result["checks"]) == {"database", "redis"}

    async def test_readiness_failed_when_check_fails(self) -> None:
        checker = HealthChecker()

        async def ok() -> bool:
            return True

        async def broken() -> bool:
            return False

        checker.register("database", ok)
        checker.register("redis", broken)
        result = await checker.run_readiness()
        assert result["status"] == HealthStatus.FAILED

    async def test_run_all_aggregates_failures(self) -> None:
        checker = HealthChecker()

        async def ok() -> bool:
            return True

        async def broken() -> bool:
            raise RuntimeError("down")

        checker.register("database", ok)
        checker.register("providers", broken)
        result = await checker.run_all()
        assert result["status"] == HealthStatus.FAILED
        assert result["checks"]["providers"]["status"] == HealthStatus.FAILED

    async def test_liveness_always_healthy(self) -> None:
        checker = HealthChecker()
        result = await checker.run_liveness()
        assert result["status"] == HealthStatus.HEALTHY


class TestHealthEndpoints:
    @pytest.mark.asyncio
    async def test_health_database_reports_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.api.main import health_database
        async def broken(*args: Any) -> bool:
            return False
        monkeypatch.setattr("src.monitoring.health.check_database", broken)
        result = await health_database()
        assert result == {"status": "failed", "check": "database"}

    @pytest.mark.asyncio
    async def test_health_redis_not_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.api.main import health_redis
        monkeypatch.setattr(settings, "redis_url", "")
        result = await health_redis()
        assert result["status"] == "healthy"
        assert result["message"] == "not configured"

    @pytest.mark.asyncio
    async def test_health_redis_failed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from src.api.main import health_redis
        monkeypatch.setattr(settings, "redis_url", "redis://localhost:6379/0")
        async def down() -> bool:
            return False
        monkeypatch.setattr("src.middleware.redis.ping_redis", down)
        result = await health_redis()
        assert result == {"status": "failed", "check": "redis"}

    @pytest.mark.asyncio
    async def test_health_ready_reports_failed_when_services_down(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.api.main import health_ready
        async def down() -> bool:
            return False
        monkeypatch.setattr("src.monitoring.health.check_database", down)
        monkeypatch.setattr("src.middleware.redis.ping_redis", down)
        result = await health_ready()
        assert result["status"] == HealthStatus.FAILED

    @pytest.mark.asyncio
    async def test_health_live_schema(self) -> None:
        from src.api.main import health_live
        result: Any = await health_live()
        assert result["status"] == HealthStatus.HEALTHY