"""Connector Registry, Manager, Health Service, Configuration.

registry.py — ConnectorRegistry: dynamic registration, lookup by name/tag
manager.py  — ConnectorManager: lifecycle orchestration, parallel health checks
health.py   — ConnectorHealthService: periodic health polling, alerting, dashboard
config.py   — ConnectorConfigLoader: env + file-based configuration
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from . import (
    BaseConnector, ConnectorConfig, ConnectorHealth, ConnectorStatus,
    ConnectorMetrics,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Connector Registry — dynamic registration and lookup
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorRegistry:
    """Central registry for all connectors. Supports dynamic loading.

    Usage:
        registry = ConnectorRegistry()
        registry.register(ESPNConnector(config))
        connector = registry.get("espn")
        all_connectors = registry.list_active()
    """

    def __init__(self):
        self._connectors: dict[str, BaseConnector] = {}
        self._by_tag: dict[str, list[str]] = {}

    def register(self, connector: BaseConnector) -> None:
        name = connector.config.name
        if name in self._connectors:
            raise ValueError(f"Connector '{name}' already registered")
        self._connectors[name] = connector
        for tag in connector.config.tags.values():
            self._by_tag.setdefault(tag, []).append(name)
        logger.info(f"Registered connector: {name} v{connector.version()}")

    def unregister(self, name: str) -> None:
        if name not in self._connectors:
            raise KeyError(f"Connector '{name}' not found")
        del self._connectors[name]
        for tag_list in self._by_tag.values():
            if name in tag_list:
                tag_list.remove(name)

    def get(self, name: str) -> BaseConnector:
        if name not in self._connectors:
            raise KeyError(f"Connector '{name}' not found")
        return self._connectors[name]

    def get_by_tag(self, tag: str) -> list[BaseConnector]:
        names = self._by_tag.get(tag, [])
        return [self._connectors[n] for n in names if n in self._connectors]

    def list_all(self) -> list[BaseConnector]:
        return list(self._connectors.values())

    def list_active(self) -> list[BaseConnector]:
        return [c for c in self._connectors.values()
                if c.status() != ConnectorStatus.DISABLED]

    def list_names(self) -> list[str]:
        return list(self._connectors.keys())

    @property
    def count(self) -> int:
        return len(self._connectors)

    def summary(self) -> dict[str, dict]:
        return {name: c.metadata() for name, c in self._connectors.items()}


# ═══════════════════════════════════════════════════════════════════════════
# Connector Manager — lifecycle orchestration
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorManager:
    """Orchestrates connector lifecycle: connect → health → shutdown.

    Handles parallel initialization and graceful shutdown of all connectors.
    """

    def __init__(self, registry: ConnectorRegistry):
        self.registry = registry
        self._started = False

    async def start_all(self) -> dict[str, bool]:
        """Connect and authenticate all registered connectors in parallel."""
        self._started = True
        results = {}

        async def _start_one(connector: BaseConnector):
            try:
                await connector.connect()
                await connector.authenticate()
                results[connector.config.name] = True
            except Exception as e:
                logger.error(f"Failed to start {connector.config.name}: {e}")
                results[connector.config.name] = False

        tasks = [_start_one(c) for c in self.registry.list_all()]
        await asyncio.gather(*tasks)
        return results

    async def shutdown_all(self):
        """Gracefully shut down all connectors."""
        self._started = False
        for connector in self.registry.list_all():
            try:
                await connector.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down {connector.config.name}: {e}")

    async def health_check_all(self) -> list[ConnectorHealth]:
        """Run health checks on all active connectors in parallel."""
        connectors = self.registry.list_active()
        results = await asyncio.gather(
            *[c.health_check() for c in connectors],
            return_exceptions=True,
        )
        health_results = []
        for connector, result in zip(connectors, results):
            if isinstance(result, Exception):
                health_results.append(ConnectorHealth(
                    status=ConnectorStatus.DOWN,
                    connector=connector.config.name,
                    checked_at=datetime.now(timezone.utc),
                    latency_ms=0,
                    message=str(result),
                ))
            else:
                health_results.append(result)
        return health_results

    def global_status(self) -> ConnectorStatus:
        """Aggregate status across all connectors."""
        statuses = [c.status() for c in self.registry.list_active()]
        if not statuses:
            return ConnectorStatus.UNKNOWN
        if any(s == ConnectorStatus.DOWN for s in statuses):
            return ConnectorStatus.DEGRADED
        if all(s == ConnectorStatus.HEALTHY for s in statuses):
            return ConnectorStatus.HEALTHY
        return ConnectorStatus.DEGRADED


# ═══════════════════════════════════════════════════════════════════════════
# Connector Health Service — periodic polling + alerting
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorHealthService:
    """Periodic health poller with alerting and dashboard API.

    Usage:
        health_svc = ConnectorHealthService(manager, interval=60)
        await health_svc.start()
        dashboard = health_svc.get_dashboard()
    """

    def __init__(
        self,
        manager: ConnectorManager,
        interval_seconds: float = 60.0,
        alert_threshold: int = 3,
        on_alert: Optional[callable] = None,
    ):
        self._manager = manager
        self._interval = interval_seconds
        self._alert_threshold = alert_threshold
        self._on_alert = on_alert
        self._history: list[list[ConnectorHealth]] = []
        self._failure_count: dict[str, int] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _poll_loop(self):
        while self._running:
            try:
                results = await self._manager.health_check_all()
                self._history.append(results)
                if len(self._history) > 100:
                    self._history = self._history[-100:]

                for health in results:
                    name = health.connector
                    if health.status == ConnectorStatus.DOWN:
                        self._failure_count[name] = self._failure_count.get(name, 0) + 1
                        if self._failure_count[name] >= self._alert_threshold:
                            if self._on_alert:
                                self._on_alert(name, health)
                    else:
                        self._failure_count[name] = 0

            except Exception as e:
                logger.error(f"Health poll error: {e}")

            await asyncio.sleep(self._interval)

    def get_dashboard(self) -> dict:
        """Dashboard API data — current health + history."""
        latest = self._history[-1] if self._history else []
        return {
            "global_status": self._manager.global_status().value,
            "connectors": [
                {
                    "name": h.connector,
                    "status": h.status.value,
                    "latency_ms": h.latency_ms,
                    "message": h.message,
                    "consecutive_failures": self._failure_count.get(h.connector, 0),
                }
                for h in latest
            ],
            "history_length": len(self._history),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


# ═══════════════════════════════════════════════════════════════════════════
# Connector Config Loader — env + file based
# ═══════════════════════════════════════════════════════════════════════════

class ConnectorConfigLoader:
    """Load connector configurations from environment variables and config files.

    Priority: env vars > config file > defaults
    """

    PRESETS: dict[str, dict] = {
        "espn": {
            "base_url": "https://sports.core.api.espn.com/v2/sports/mma",
            "rate_limit_rps": 8.0,
            "rate_limit_burst": 15,
            "timeout_seconds": 30.0,
            "user_agent": "MMA-Platform/1.0 (Data Collection)",
            "tags": {"category": "structured", "org": "ufc", "type": "api"},
        },
        "ufcstats": {
            "base_url": "http://ufcstats.com",
            "rate_limit_rps": 3.0,
            "rate_limit_burst": 5,
            "timeout_seconds": 45.0,
            "user_agent": "MMA-Platform/1.0 (Research)",
            "tags": {"category": "statistics", "org": "ufc", "type": "web"},
        },
        "thesportsdb": {
            "base_url": "https://www.thesportsdb.com/api/v1/json",
            "rate_limit_rps": 20.0,
            "rate_limit_burst": 30,
            "tags": {"category": "media", "org": "multi", "type": "api"},
        },
        "wikipedia": {
            "base_url": "https://en.wikipedia.org/w/api.php",
            "rate_limit_rps": 5.0,
            "rate_limit_burst": 10,
            "tags": {"category": "reference", "org": "multi", "type": "web"},
        },
        "sherdog": {
            "base_url": "https://www.sherdog.com",
            "rate_limit_rps": 2.0,
            "rate_limit_burst": 3,
            "timeout_seconds": 45.0,
            "tags": {"category": "records", "org": "multi", "type": "web"},
        },
        "tapology": {
            "base_url": "https://www.tapology.com",
            "rate_limit_rps": 2.0,
            "rate_limit_burst": 3,
            "timeout_seconds": 45.0,
            "tags": {"category": "rankings", "org": "multi", "type": "web"},
        },
        "official_ufc": {
            "base_url": "https://api.ufc.com",
            "rate_limit_rps": 10.0,
            "tags": {"category": "official", "org": "ufc", "type": "api"},
        },
    }

    @classmethod
    def load(cls, name: str, overrides: dict[str, Any] | None = None) -> ConnectorConfig:
        """Load config from presets + optional overrides."""
        if name not in cls.PRESETS:
            raise ValueError(f"No preset for connector '{name}'. Available: {list(cls.PRESETS.keys())}")

        preset = cls.PRESETS[name]
        merged = {**preset, **(overrides or {})}
        return ConnectorConfig(name=name, **merged)

    @classmethod
    def load_all(
        cls, names: list[str] | None = None, overrides: dict[str, dict] | None = None,
    ) -> dict[str, ConnectorConfig]:
        """Load configs for multiple connectors."""
        names = names or list(cls.PRESETS.keys())
        configs = {}
        for name in names:
            override = (overrides or {}).get(name, {})
            configs[name] = cls.load(name, override)
        return configs
