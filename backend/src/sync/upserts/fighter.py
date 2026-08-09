"""FighterUpsert — idempotent fighter upsert + expanded record persistence.

Records (KO/sub/title breakdown) live in the `fighter_records` table (one row
per fighter, unique on fighter_id). The expanded breakdown is ONLY written when
the DTO carries it (records actually fetched from /athletes/{id}/records) —
unavailable records never reset stored values (research GAP: fighters used to
persist 0-0-0-0).

is_active is presence-guarded: the ESPN payload only carries `active` for some
athletes; a None DTO value means "unknown" and never overwrites the stored flag.
"""

from sqlalchemy import select

from src.domain.models.fighter import Fighter, FighterRecord
from src.providers.dto import FighterDTO
from src.sync.upsert import UpsertResult
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
        "weight_class_name": "weight_class_name",
    }

    @property
    def _model_class(self) -> type[Fighter]:
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
            weight_class_name=dto.weight_class_name,
            weight_class_id=None,  # resolved in _enrich_model
        )

    async def _enrich_model(self, model: Fighter, dto: FighterDTO) -> None:
        """Resolve the fighter's weight class, creating it from inline data."""
        if dto.weight_class_external_id:
            wclass_uuid = await self._ensure_weight_class(
                dto.weight_class_external_id,
                dto.weight_class_name or dto.weight_class_external_id,
            )
            if wclass_uuid:
                model.weight_class_id = wclass_uuid

    # birth_date not in FIELD_MAP because it's Optional and datetime comparisons
    # need special null-handling (None != None is False, which is correct here)
    def _special_fields(self, existing: Fighter, dto: FighterDTO) -> set[str]:
        changes: set[str] = set()
        if existing.birth_date != dto.birth_date:
            changes.add("birth_date")
        # is_active: presence-guarded — only a real bool from ESPN may change it
        if dto.is_active is not None and existing.is_active != dto.is_active:
            changes.add("is_active")
        return changes

    def _apply_special_fields(self, model: Fighter, dto: FighterDTO, fields: set[str]) -> None:
        if "birth_date" in fields:
            model.birth_date = dto.birth_date
        if "is_active" in fields and dto.is_active is not None:
            model.is_active = dto.is_active

    # ── Expanded record breakdown (fighter_records table) ──────────────────

    async def upsert_batch(self, dtos: list[FighterDTO]) -> UpsertResult:
        """Fighter upsert + nested FighterRecord persistence.

        After the fighter rows are upserted, resolve each fighter UUID and
        write the expanded record breakdown when the DTO carries it. Records
        are idempotent via the unique constraint on fighter_id.
        """
        result = await super().upsert_batch(dtos)

        for dto in dtos:
            if not self._has_record_data(dto):
                continue
            try:
                fighter_uuid = await self._resolver.resolve(
                    self.provider, dto.external_id, self.entity_type
                )
                if fighter_uuid is None:
                    continue
                result += await self._upsert_record(fighter_uuid, dto)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(
                    f"Record upsert failed for {dto.external_id}: {e}"
                )
                result.errors += 1

        return result

    @staticmethod
    def _has_record_data(dto: FighterDTO) -> bool:
        """True when the DTO carries an actually-fetched record breakdown.

        All breakdown fields default None (records not fetched/unavailable);
        any non-None value means /athletes/{id}/records returned a real payload
        for this fighter. Stored records are never reset by a None DTO.
        """
        return (
            dto.record_summary is not None
            or dto.ko_tko_wins is not None
            or dto.submission_wins is not None
            or dto.title_wins is not None
            or dto.total_fights is not None
            or dto.finish_rate is not None
        )

    async def _upsert_record(self, fighter_uuid: str, dto: FighterDTO) -> UpsertResult:
        """Idempotent FighterRecord upsert keyed by fighter_id (unique)."""
        result = UpsertResult()

        existing = await self._resolver._db.execute(
            select(FighterRecord).where(FighterRecord.fighter_id == fighter_uuid)
        )
        row = existing.scalar_one_or_none()

        def apply(rec: FighterRecord) -> bool:
            changed = False
            mapping = {
                "wins": dto.record_wins,
                "losses": dto.record_losses,
                "draws": dto.record_draws,
                "no_contests": dto.record_no_contests,
                "ko_tko_wins": dto.ko_tko_wins,
                "ko_tko_losses": dto.ko_tko_losses,
                "submission_wins": dto.submission_wins,
                "submission_losses": dto.submission_losses,
                "title_wins": dto.title_wins,
                "title_losses": dto.title_losses,
                "title_draws": dto.title_draws,
                "total_fights": dto.total_fights,
                "win_percentage": dto.win_percentage,
                "finish_rate": dto.finish_rate,
                "record_summary": dto.record_summary,
            }
            for attr, value in mapping.items():
                if value is None:
                    continue  # never clobber with unknown
                if getattr(rec, attr) != value:
                    setattr(rec, attr, value)
                    changed = True
            return changed

        if row:
            if apply(row):
                self._resolver._db.add(row)
                result.updated += 1
            else:
                result.skipped += 1
        else:
            rec = FighterRecord(fighter_id=fighter_uuid)
            rec.wins = dto.record_wins
            rec.losses = dto.record_losses
            rec.draws = dto.record_draws
            rec.no_contests = dto.record_no_contests
            rec.ko_tko_wins = dto.ko_tko_wins or 0
            rec.ko_tko_losses = dto.ko_tko_losses or 0
            rec.submission_wins = dto.submission_wins or 0
            rec.submission_losses = dto.submission_losses or 0
            rec.title_wins = dto.title_wins or 0
            rec.title_losses = dto.title_losses or 0
            rec.title_draws = dto.title_draws or 0
            rec.total_fights = dto.total_fights or 0
            rec.win_percentage = dto.win_percentage or 0.0
            rec.finish_rate = dto.finish_rate or 0.0
            rec.record_summary = dto.record_summary
            self._resolver._db.add(rec)
            result.inserted += 1

        return result
