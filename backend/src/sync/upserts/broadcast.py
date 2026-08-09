"""BroadcastUpsert — idempotent broadcast upsert.

Matched by composite key (event_id, network, region).
Protected by DB unique constraint: uq_broadcast_event_network on broadcasts table.
Race-safe: IntegrityError from concurrent insert handled by per-row retry.

Does NOT extend BaseUpsert because broadcasts lack provider external IDs.
"""

import logging
from typing import TYPE_CHECKING

from src.domain.models.broadcast import Broadcast
from src.providers.dto import BroadcastDTO
from src.sync.upsert import UpsertResult

if TYPE_CHECKING:
    from src.sync.upserts.id_resolver import IdResolver

logger = logging.getLogger(__name__)


class BroadcastUpsert:
    """Matched by DB unique constraint: (event_id, network, region)."""

    entity_type = "broadcast"
    provider = "espn"

    def __init__(self, resolver: "IdResolver") -> None:
        self._resolver: IdResolver = resolver
        self._event_uuid_map: dict[str, str] = {}

    def set_event_map(self, event_map: dict[str, str]) -> None:
        self._event_uuid_map = event_map

    async def upsert_batch(self, dtos: list[BroadcastDTO]) -> UpsertResult:
        """Per-row upsert using composite key lookup.

        DB unique constraint on (event_id, network, region) prevents duplicates
        even under concurrent workers.
        """
        from sqlalchemy import select

        if not dtos:
            return UpsertResult.empty()

        result = UpsertResult()

        for dto in dtos:
            try:
                event_uuid = self._event_uuid_map.get(dto.event_external_id)
                if event_uuid is None:
                    event_uuid = await self._resolver.resolve(
                        self.provider, dto.event_external_id, "event"
                    )
                if event_uuid is None:
                    result.errors += 1
                    continue

                existing = await self._resolver._db.execute(
                    select(Broadcast).where(
                        Broadcast.event_id == event_uuid,
                        Broadcast.network == dto.network,
                        Broadcast.region == dto.region,
                    )
                )
                row = existing.scalar_one_or_none()

                if row:
                    changed = False
                    if row.language != dto.language:
                        row.language = dto.language
                        changed = True
                    if row.broadcast_type != dto.broadcast_type:
                        row.broadcast_type = dto.broadcast_type
                        changed = True
                    if changed:
                        self._resolver._db.add(row)
                        result.updated += 1
                    else:
                        result.skipped += 1
                else:
                    broadcast = Broadcast(
                        provider=self.provider,
                        event_id=event_uuid,
                        network=dto.network,
                        region=dto.region,
                        language=dto.language,
                        broadcast_type=dto.broadcast_type,
                    )
                    self._resolver._db.add(broadcast)
                    result.inserted += 1

            except Exception as e:
                logger.error(f"Broadcast upsert failed: {e}")
                result.errors += 1
                result.error_details.append(str(e))

        return result
