"""WeightClassUpsert — idempotent weight class upsert."""

from src.domain.models.weight_class import WeightClass
from src.providers.dto import WeightClassDTO
from src.sync.upserts.base import BaseUpsert


class WeightClassUpsert(BaseUpsert):
    entity_type = "weight_class"
    provider = "espn"

    FIELD_MAP = {
        "name": "name",
        "abbreviation": "abbreviation",
        "min_weight_kg": "min_weight_kg",
        "max_weight_kg": "max_weight_kg",
        "gender": "gender",
    }

    @property
    def _model_class(self) -> type:
        return WeightClass

    def _extract_external_id(self, dto: WeightClassDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: WeightClassDTO) -> WeightClass:
        return WeightClass(
            name=dto.name,
            abbreviation=dto.abbreviation,
            min_weight_kg=dto.min_weight_kg,
            max_weight_kg=dto.max_weight_kg,
            gender=dto.gender,
        )
