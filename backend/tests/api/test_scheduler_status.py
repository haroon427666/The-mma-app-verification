"""Scheduler status route tests — T06 (graceful degradation).

GET /scheduler/status must return 503 (not 500) when the sync backend is
degraded — e.g. Redis configured but unreachable while SYNC_ENABLED=true.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from src.api.sync import get_manager, scheduler_status, set_sync_manager


@pytest.fixture(autouse=True)
def _reset_manager():
    set_sync_manager(None)
    yield
    set_sync_manager(None)


class TestSchedulerStatus:
    def test_returns_dashboard_when_manager_healthy(self):
        manager = AsyncMock()
        manager.get_status = AsyncMock(
            return_value={"running": True, "queue": {"pending": 0}}
        )
        set_sync_manager(manager)

        result = asyncio.run(scheduler_status())
        assert result == {"running": True, "queue": {"pending": 0}}

    def test_503_when_status_raises(self):
        """Redis unreachable / backend degraded → 503 with explicit message,
        never a 500."""
        manager = AsyncMock()
        manager.get_status = AsyncMock(
            side_effect=ConnectionError("Redis connection refused")
        )
        set_sync_manager(manager)

        with pytest.raises(HTTPException) as exc:
            asyncio.run(scheduler_status())
        assert exc.value.status_code == 503
        assert "Redis" in exc.value.detail

    def test_503_when_manager_not_initialized(self):
        with pytest.raises(HTTPException) as exc:
            get_manager()
        assert exc.value.status_code == 503
