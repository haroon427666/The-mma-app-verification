"""FighterUpsert — idempotent fighter upsert."""

from src.domain.models.fighter import Fighter
from src.providers.dto import FighterDTO
from src.sync.upserts.base import BaseUpsert


class FighterUpsert(BaseUpsert):
    entity_type = "fighter"
    provider = "espn"

    FIELD_MAP = {
        "first_name": "first_name",
        "last_name": "last_name",
        "short_name": "short_name",
        "record_wins": "record_wins",
        "record_losses": "record_losses",
        "record_draws": "record_draws",
        "record_no_contests": "record_no_contests",
        "height_cm": "height_cm",
        "weight_kg": "weight_kg",
        "reach_cm": "reach_cm",
        "stance": "stance",
        "nationality": "nationality",
        "headshot_url": "headshot_url",
    }

    @property
    def _model_class(self) -> type:
        return Fighter

    def _extract_external_id(self, dto: FighterDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: FighterDTO) -> Fighter:
        return Fighter(
            first_name=dto.first_name,
            last_name=dto.last_name,
            short_name=dto.short_name,
            record_wins=dto.record_wins,
            record_losses=dto.record_losses,
            record_draws=dto.record_draws,
            record_no_contests=dto.record_no_contests,
            height_cm=dto.height_cm,
            weight_kg=dto.weight_kg,
            reach_cm=dto.reach_cm,
            stance=dto.stance,
            nationality=dto.nationality,
            birth_date=dto.birth_date,
            headshot_url=dto.headshot_url,
            weight_class_id=None,  # resolved by sync engine
        )

    # birth_date not in FIELD_MAP because it's Optional and datetime comparisons
    # need special null-handling (None != None is False, which is correct here)
    def _special_fields(self, existing: Fighter, dto: FighterDTO) -> set[str]:
        changes: set[str] = set()
        if existing.birth_date != dto.birth_date:
            changes.add("birth_date")
        return changes

    def _apply_special_fields(self, model: Fighter, dto: FighterDTO, fields: set[str]) -> None:
        if "birth_date" in fields:
            model.birth_date = dto.birth_date
