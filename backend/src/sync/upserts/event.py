"""EventUpsert — idempotent event upsert."""

from src.domain.models.event import Event
from src.providers.dto import EventDTO
from src.sync.upserts.base import BaseUpsert


class EventUpsert(BaseUpsert):
    entity_type = "event"
    provider = "espn"

    FIELD_MAP = {
        "name": "name",
        "short_name": "short_name",
        "status": "status",
    }

    @property
    def _model_class(self) -> type:
        return Event

    def _extract_external_id(self, dto: EventDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: EventDTO) -> Event:
        return Event(
            name=dto.name,
            short_name=dto.short_name,
            date=dto.date,
            status=dto.status,
            slug=dto.slug or "",
            promotion_id=None,  # resolved by sync engine
            venue_id=None,      # resolved by sync engine
        )

    # date and slug are Optional/datetime — need special comparison
    def _special_fields(self, existing: Event, dto: EventDTO) -> set[str]:
        changes: set[str] = set()
        if existing.date != dto.date:
            changes.add("date")
        if existing.slug != (dto.slug or ""):
            changes.add("slug")
        return changes

    def _apply_special_fields(self, model: Event, dto: EventDTO, fields: set[str]) -> None:
        if "date" in fields:
            model.date = dto.date
        if "slug" in fields:
            model.slug = dto.slug or ""
