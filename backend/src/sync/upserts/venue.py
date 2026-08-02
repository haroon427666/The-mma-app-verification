"""VenueUpsert — idempotent venue upsert."""

from src.domain.models.venue import Venue
from src.providers.dto import VenueDTO
from src.sync.upserts.base import BaseUpsert


class VenueUpsert(BaseUpsert):
    entity_type = "venue"
    provider = "espn"

    FIELD_MAP = {
        "name": "name",
        "city": "city",
        "state": "state",
        "country": "country",
        "latitude": "latitude",
        "longitude": "longitude",
        "capacity": "capacity",
    }

    @property
    def _model_class(self) -> type:
        return Venue

    def _extract_external_id(self, dto: VenueDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: VenueDTO) -> Venue:
        return Venue(
            name=dto.name,
            city=dto.city,
            state=dto.state,
            country=dto.country,
            latitude=dto.latitude,
            longitude=dto.longitude,
            capacity=dto.capacity,
        )
