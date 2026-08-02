"""Notifications — sync started, completed, failed, provider offline.

Supports: structured logs (always), Discord webhook (optional), email (optional).

Configure via environment:
    DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
    ALERT_EMAIL=ops@example.com
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Config from environment
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")
ALERT_EMAIL = os.environ.get("ALERT_EMAIL", "")


class Notifier:
    """Sends notifications about sync events."""

    def __init__(self):
        self._http_client = None

    async def _ensure_client(self):
        if self._http_client is None:
            import httpx
            self._http_client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        if self._http_client:
            await self._http_client.aclose()

    # ── Sync Notifications ──────────────────────────────────────────────

    async def sync_started(self, mode: str, entities: list[str] | None = None) -> None:
        msg = f"🔄 Sync started — mode={mode}"
        if entities:
            msg += f" entities={entities}"
        logger.info(msg)

        if DISCORD_WEBHOOK_URL:
            await self._send_discord("Sync Started", msg, color=0x3498DB)

    async def sync_completed(
        self, mode: str, duration_ms: float, inserted: int, updated: int, errors: int,
    ) -> None:
        msg = (
            f"✅ Sync completed — {inserted} inserted, {updated} updated"
            f"{f', {errors} ERRORS!' if errors > 0 else ''} "
            f"({duration_ms/1000:.1f}s)"
        )
        color = 0x2ECC71 if errors == 0 else 0xE67E22

        if errors > 0:
            logger.warning(msg)
        else:
            logger.info(msg)

        if DISCORD_WEBHOOK_URL:
            await self._send_discord("Sync Completed", msg, color=color)

        if errors > 0 and ALERT_EMAIL:
            await self._send_email("Sync completed with errors", msg)

    async def sync_failed(self, mode: str, error: str) -> None:
        msg = f"❌ Sync FAILED — mode={mode}: {error}"
        logger.error(msg)

        if DISCORD_WEBHOOK_URL:
            await self._send_discord("Sync Failed 🚨", msg, color=0xE74C3C)

        if ALERT_EMAIL:
            await self._send_email("URGENT: Sync failed", msg)

    async def provider_offline(self, provider: str, error: str) -> None:
        msg = f"⚠️ Provider OFFLINE — {provider}: {error}"
        logger.warning(msg)

        if DISCORD_WEBHOOK_URL:
            await self._send_discord("Provider Offline", msg, color=0xF39C12)

    async def recovery_succeeded(self, job_name: str) -> None:
        msg = f"🔧 Recovery succeeded — {job_name} resumed from checkpoint"
        logger.info(msg)

        if DISCORD_WEBHOOK_URL:
            await self._send_discord("Recovery Succeeded", msg, color=0x27AE60)

    # ── Transport ─────────────────────────────────────────────────────────

    async def _send_discord(self, title: str, message: str, color: int = 0x3498DB) -> None:
        if not DISCORD_WEBHOOK_URL:
            return  # Silently skip if not configured
        try:
            await self._ensure_client()
            payload = {
                "embeds": [{
                    "title": title,
                    "description": message,
                    "color": color,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }]
            }
            await self._http_client.post(DISCORD_WEBHOOK_URL, json=payload)
        except Exception as e:
            logger.debug(f"Discord notification failed (non-critical): {e}")

    async def _send_email(self, subject: str, body: str) -> None:
        if not ALERT_EMAIL:
            return
        # In production: use SMTP or a transactional email service (SendGrid, SES).
        # For now, log the alert — email integration is environment-specific.
        logger.info(f"[EMAIL] To:{ALERT_EMAIL} Subject:{subject} Body:{body[:200]}")
