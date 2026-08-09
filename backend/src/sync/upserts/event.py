"""EventUpsert — idempotent event upsert."""

import logging

from src.domain.models.event import Event
from src.providers.dto import EventDTO
from src.sync.upserts.base import BaseUpsert

logger = logging.getLogger(__name__)


class EventUpsert(BaseUpsert):
    entity_type = "event"
    provider = "espn"

    FIELD_MAP = {
        "name": "name",
        "short_name": "short_name",
        "status": "status",
    }

    @property
    def _model_class(self) -> type[Event]:
        return Event

    def _extract_external_id(self, dto: EventDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: EventDTO) -> Event:
        return Event(
            name=dto.name,
            short_name=dto.short_name,
            date_utc=dto.date,
            status=dto.status,
            slug=dto.slug or "",
            promotion_id=None,  # resolved in _enrich_model
            venue_id=None,      # resolved in _enrich_model
        )

    async def _enrich_model(self, model: Event, dto: EventDTO) -> None:
        """Resolve the event's promotion (NOT NULL FK) and venue (nullable)."""
        if dto.promotion_external_id:
            promo_uuid = await self._resolver.resolve(
                self.provider, dto.promotion_external_id, "promotion"
            )
            if promo_uuid:
                model.promotion_id = promo_uuid
            else:
                raise ValueError(
                    f"Event {dto.external_id}: promotion "
                    f"{dto.promotion_external_id} not synced"
                )
        if dto.venue_external_id:
            venue_uuid = await self._resolver.resolve(
                self.provider, dto.venue_external_id, "venue"
            )
            if venue_uuid:
                model.venue_id = venue_uuid

    # date_utc and slug are Optional/datetime — need special comparison
    def _special_fields(self, existing: Event, dto: EventDTO) -> set[str]:
        changes: set[str] = set()
        if existing.date_utc != dto.date:
            changes.add("date_utc")
        if existing.slug != (dto.slug or ""):
            changes.add("slug")
        return changes

    def _apply_special_fields(self, model: Event, dto: EventDTO, fields: set[str]) -> None:
        if "date_utc" in fields:
            model.date_utc = dto.date
        if "slug" in fields:
            model.slug = dto.slug or ""
