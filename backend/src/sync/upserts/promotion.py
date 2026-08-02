"""PromotionUpsert — idempotent promotion upsert."""

from src.domain.models.promotion import Promotion
from src.providers.dto import PromotionDTO
from src.sync.upserts.base import BaseUpsert


class PromotionUpsert(BaseUpsert):
    entity_type = "promotion"
    provider = "espn"

    FIELD_MAP = {
        "name": "name",
        "slug": "slug",
        "country": "country",
        "logo_url": "logo_url",
        "season_year": "season_year",
    }

    @property
    def _model_class(self) -> type:
        return Promotion

    def _extract_external_id(self, dto: PromotionDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: PromotionDTO) -> Promotion:
        return Promotion(
            name=dto.name,
            slug=dto.slug,
            country=dto.country,
            logo_url=dto.logo_url,
            season_year=dto.season_year,
            is_active=dto.season_year is not None and dto.season_year >= 2024,
        )

    # is_active is derived from season_year — needs special handling
    def _special_fields(self, existing: Promotion, dto: PromotionDTO) -> set[str]:
        changes: set[str] = set()
        is_active = dto.season_year is not None and dto.season_year >= 2024
        if existing.is_active != is_active:
            changes.add("is_active")
        return changes

    def _apply_special_fields(self, model: Promotion, dto: PromotionDTO, fields: set[str]) -> None:
        if "is_active" in fields:
            model.is_active = dto.season_year is not None and dto.season_year >= 2024
