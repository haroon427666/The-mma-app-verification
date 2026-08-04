"""Provider Payload Store — raw JSON archive.

Stores raw provider API responses for:
- Debugging parser issues
- Replaying parsers after code changes
- Testing new parser versions against historical data
- Schema migration validation

Payloads are archived in the provider_payloads table (JSONB).
Not queried by business logic — pure audit/replay infrastructure.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast

from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from src.db.models.support import ProviderPayload

logger = logging.getLogger(__name__)


class PayloadStore:
    """Archives raw provider JSON for debugging and replay."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def store(
        self,
        provider: str,
        endpoint: str,
        entity_type: str,
        external_id: str | None,
        payload: dict[str, Any] | list[Any],
    ) -> str:
        """Archive a raw JSON payload. Returns payload ID."""
        from sqlalchemy.dialects.postgresql import insert

        from src.db.base import new_uuid
        from src.db.models.support import ProviderPayload

        payload_id = new_uuid()
        values: dict[str, Any] = {
            "id": payload_id,
            "provider": provider,
            "endpoint": endpoint,
            "entity_type": entity_type,
            "external_id": external_id,
            "payload": payload,
            "fetched_at": datetime.now(UTC),
        }

        await self._session.execute(insert(ProviderPayload).values(**values))
        return payload_id

    async def get_payload(self, payload_id: str) -> dict[str, Any] | None:
        """Retrieve an archived payload."""
        from sqlalchemy import select

        from src.db.models.support import ProviderPayload

        result = await self._session.execute(
            select(ProviderPayload.payload).where(ProviderPayload.id == payload_id)
        )
        row = result.scalar_one_or_none()
        return row if row else None

    async def get_payloads_for_entity(
        self, provider: str, entity_type: str, external_id: str,
    ) -> list[ProviderPayload]:
        """Retrieve all archived payloads for a specific entity."""
        from sqlalchemy import select

        from src.db.models.support import ProviderPayload

        result = await self._session.execute(
            select(ProviderPayload)
            .where(
                ProviderPayload.provider == provider,
                ProviderPayload.entity_type == entity_type,
                ProviderPayload.external_id == external_id,
            )
            .order_by(ProviderPayload.fetched_at.desc())
        )
        return list(result.scalars().all())

    async def prune_old(self, days: int = 90) -> int:
        """Delete payloads older than N days. Returns count deleted."""
        from sqlalchemy import delete

        from src.db.models.support import ProviderPayload

        cutoff = datetime.now(UTC) - timedelta(days=days)
        result = await self._session.execute(
            delete(ProviderPayload).where(ProviderPayload.fetched_at < cutoff)
        )
        cursor = cast(CursorResult[Any], result)
        return int(cursor.rowcount or 0)
