"""Live Event Mode — detects active UFC events and enables high-frequency polling.

When a UFC event is live:
    Normal Mode (15-min polls)
        ↓
    Live Mode (30-sec polls)
        ↓
    Event finishes → Normal Mode

Detection: checks if any event in the DB has status=IN_PROGRESS 
or if today has a SCHEDULED event that should be starting soon.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class LiveModeDetector:
    """Detects when a UFC event is live and activates high-frequency polling."""

    def __init__(self, db_session_factory):
        self._db_factory = db_session_factory
        self._in_live_mode = False
        self._active_event_id: Optional[str] = None
        self._live_started_at: Optional[datetime] = None

    @property
    def is_live(self) -> bool:
        return self._in_live_mode

    @property
    def active_event_id(self) -> Optional[str]:
        return self._active_event_id

    async def check(self) -> bool:
        """Check whether we should enter, stay in, or exit live mode.

        Returns True if in live mode.
        """
        try:
            async with self._db_factory() as session:
                from sqlalchemy import select, text
                result = await session.execute(
                    text(
                        "SELECT id, name FROM events "
                        "WHERE status = 'IN_PROGRESS' "
                        "AND date_utc >= NOW() - INTERVAL '1 day' "
                        "LIMIT 1"
                    )
                )
                row = result.fetchone()
                if row:
                    if not self._in_live_mode:
                        self._enter_live_mode(str(row[0]), str(row[1]))
                    return True

                # Check for events starting soon (within 30 minutes)
                result = await session.execute(
                    text(
                        "SELECT id, name FROM events "
                        "WHERE status = 'SCHEDULED' "
                        "AND date_utc BETWEEN NOW() AND NOW() + INTERVAL '30 minutes' "
                        "LIMIT 1"
                    )
                )
                row = result.fetchone()
                if row:
                    if not self._in_live_mode:
                        self._enter_live_mode(str(row[0]), str(row[1]))
                    return True

                # No live or upcoming events — exit live mode
                if self._in_live_mode:
                    await self._exit_live_mode()
                return False

        except Exception as e:
            logger.error(f"Live mode check failed: {e}")
            return self._in_live_mode  # Stay in current state on error

    def _enter_live_mode(self, event_id: str, event_name: str) -> None:
        self._in_live_mode = True
        self._active_event_id = event_id
        self._live_started_at = datetime.now(timezone.utc)
        logger.info(f"⚡ LIVE MODE ON — {event_name} ({event_id}) — 30s polling")

    async def _exit_live_mode(self) -> None:
        duration = (datetime.now(timezone.utc) - self._live_started_at).total_seconds() if self._live_started_at else 0
        logger.info(f"🔽 LIVE MODE OFF — was active for {duration:.0f}s")
        self._in_live_mode = False
        self._active_event_id = None
        self._live_started_at = None
