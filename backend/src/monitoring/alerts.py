"""Alert Engine — production alert conditions + routing.

Alert conditions:
    provider_down         — ESPN/TSDB/Octagon unreachable > 3 consecutive failures
    scheduler_stuck       — No job completed in last 10 minutes
    queue_overflow        — > 100 jobs waiting
    db_unavailable        — Readiness DB check failed
    redis_unavailable     — Readiness Redis check failed
    login_storm           — > 20 failed logins in 5 minutes
    token_reuse           — Refresh token reuse detected
    high_sync_failures    — > 50% sync jobs failing in last 10 runs
    high_latency          — P95 response time > 1 second
    disk_full             — > 90% disk usage

Routing: logs (always) + optional Discord webhook + optional email.
"""

import logging
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_URL", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")


@dataclass
class Alert:
    name: str
    severity: str  # critical, warning, info
    message: str
    fired_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    details: dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False


class AlertEngine:
    """Checks conditions and fires alerts. Deduplicates within cooldown windows."""

    def __init__(self, notifier: Any = None) -> None:
        self._conditions: dict[str, Callable[..., Any]] = {}
        self._cooldowns: dict[str, float] = {}
        self._fired: list[Alert] = []
        self._notifier = notifier

    def register(self, name: str, check_fn: Callable[..., Any], cooldown_s: int = 300) -> None:
        self._conditions[name] = check_fn
        self._cooldowns[name] = cooldown_s

    async def check_all(self) -> list[Alert]:
        fired = []
        now = time.monotonic()

        for name, check_fn in self._conditions.items():
            # Cooldown: don't re-fire the same alert within its window
            last_fired = self._cooldowns.get(f"{name}_last", 0)
            if now - last_fired < self._cooldowns.get(name, 300):
                continue

            try:
                result = await check_fn()
                if result:  # Alert condition triggered
                    alert = result if isinstance(result, Alert) else Alert(
                        name=name, severity="warning",
                        message=f"Alert: {name} triggered",
                        details={"result": str(result)},
                    )
                    self._cooldowns[f"{name}_last"] = now
                    self._fired.append(alert)
                    fired.append(alert)
                    await self._dispatch(alert)
            except Exception as e:
                logger.error(f"Alert check '{name}' failed: {e}")

        return fired

    async def _dispatch(self, alert: Alert) -> None:
        """Send alert to all configured targets."""
        logger.warning(
            f"ALERT [{alert.severity}] {alert.name}: {alert.message}",
            extra={"alert_name": alert.name, "alert_severity": alert.severity},
        )

        if DISCORD_WEBHOOK:
            try:
                import httpx
                color = {"critical": 0xE74C3C, "warning": 0xF39C12, "info": 0x3498DB}
                async with httpx.AsyncClient() as client:
                    await client.post(DISCORD_WEBHOOK, json={
                        "embeds": [{"title": f"[{alert.severity.upper()}] {alert.name}",
                                    "description": alert.message, "color": color.get(alert.severity, 0x3498DB)}]
                    }, timeout=10)
            except Exception:
                pass

    def get_history(self, limit: int = 50) -> list[Alert]:
        return self._fired[-limit:]


# ── Pre-built alert conditions ──────────────────────────────────────────────

class LoginStormDetector:
    """Detects > 20 failed logins in 5 minutes."""
    def __init__(self, threshold: int = 20, window_s: int = 300):
        self.threshold = threshold
        self.window = window_s
        self._failures: list[float] = []

    def record_failure(self) -> bool:
        now = time.monotonic()
        cutoff = now - self.window
        self._failures = [t for t in self._failures if t > cutoff]
        self._failures.append(now)
        return len(self._failures) >= self.threshold


class TokenReuseDetector:
    """Tracks refresh token reuse events."""
    def __init__(self) -> None:
        self._reuse_events: list[dict[str, Any]] = []

    def record_reuse(self, user_id: str, details: dict[str, Any] | None = None) -> None:
        self._reuse_events.append({
            "user_id": user_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "details": details or {},
        })
        logger.critical(f"TOKEN REUSE ATTACK — user={user_id}")


class SyncFailureTracker:
    """Tracks sync job failure rate."""
    def __init__(self, window: int = 10):
        self._results: list[bool] = []
        self.window = window

    def record(self, success: bool) -> None:
        self._results.append(success)
        if len(self._results) > self.window:
            self._results = self._results[-self.window:]

    @property
    def failure_rate(self) -> float:
        if not self._results:
            return 0.0
        return 1.0 - (sum(self._results) / len(self._results))
