"""CompetitionUpsert — idempotent competition + nested competitor upsert.

Competitions are tricky: they contain nested CompetitorDTOs.
This upsert handles both Competition and Competitor rows in one batch.

Race-safe: uses BaseUpsert's IntegrityError retry for the competition row.
Competitor rows are protected by DB unique constraint (competition_id, fighter_id).
"""

import logging
from uuid import UUID

from src.domain.models.competition import Competition
from src.domain.models.competitor import Competitor
from src.providers.dto import CompetitionDTO
from src.sync.upsert import UpsertResult
from src.sync.upserts.base import BaseUpsert

logger = logging.getLogger(__name__)


class CompetitionUpsert(BaseUpsert):
    """Competition upsert with nested competitor handling.

    Overrides upsert_batch() to handle CompetitorDTOs after the competition
    row is inserted/updated. This is the ONLY subclass that overrides batch logic
    — and it's necessary because competitions have a 1:N child relationship.
    """

    entity_type = "competition"
    provider = "espn"

    FIELD_MAP = {
        "order_num": "order_num",
        "card_segment": "card_segment",
        "status": "status",
        "is_main_event": "is_main_event",
        "is_title_fight": "is_title_fight",
        "result_method": "result_method",
        "result_detail": "result_detail",
        "result_round": "result_round",
        "result_time": "result_time",
    }

    @property
    def _model_class(self) -> type[Competition]:
        return Competition

    def _extract_external_id(self, dto: CompetitionDTO) -> str:
        return dto.external_id

    def _to_model(self, dto: CompetitionDTO) -> Competition:
        return Competition(
            event_id=None,         # resolved by sync engine
            weight_class_id=None,  # resolved by sync engine
            order_num=dto.order_num,
            card_segment=dto.card_segment,
            status=dto.status,
            is_main_event=dto.is_main_event,
            is_title_fight=dto.is_title_fight,
            result_method=dto.result_method,
            result_detail=dto.result_detail,
            result_round=dto.result_round,
            result_time=dto.result_time,
        )

    # ── Nested competitor handling ─────────────────────────────────────────

    async def upsert_batch(self, dtos: list[CompetitionDTO]) -> UpsertResult:
        """Extended upsert: competition + nested competitors.

        After competition upsert, resolve competition UUIDs and upsert
        each competitor row. Competitors are idempotent via DB unique constraint.
        """
        result = await super().upsert_batch(dtos)

        for dto in dtos:
            if not dto.competitors:
                continue
            try:
                comp_uuid = await self._resolver.resolve(
                    self.provider, dto.external_id, self.entity_type
                )
                if comp_uuid is None:
                    continue
                result += await self._upsert_competitors(comp_uuid, dto)
            except Exception as e:
                logger.error(f"Competitor upsert failed for {dto.external_id}: {e}")
                result.errors += 1

        return result

    async def _upsert_competitors(
        self, competition_uuid: UUID, dto: CompetitionDTO
    ) -> UpsertResult:
        """Idempotent competitor upsert via DB unique constraint on (comp_id, fighter_id)."""
        from sqlalchemy import select

        result = UpsertResult()

        for comp_dto in dto.competitors:
            fighter_uuid = await self._resolver.resolve(
                self.provider, comp_dto.fighter_external_id, "fighter"
            )
            if fighter_uuid is None:
                logger.warning(
                    f"Competitor skipped: fighter {comp_dto.fighter_external_id} "
                    f"not yet synced"
                )
                result.skipped += 1
                continue

            existing = await self._resolver._db.execute(
                select(Competitor).where(
                    Competitor.competition_id == competition_uuid,
                    Competitor.fighter_id == fighter_uuid,
                )
            )
            existing_row = existing.scalar_one_or_none()

            if existing_row:
                changed = False
                if existing_row.corner != comp_dto.corner:
                    existing_row.corner = comp_dto.corner
                    changed = True
                if existing_row.outcome != comp_dto.outcome:
                    existing_row.outcome = comp_dto.outcome
                    changed = True
                if changed:
                    self._resolver._db.add(existing_row)
                    result.updated += 1
                else:
                    result.skipped += 1
            else:
                competitor = Competitor(
                    competition_id=competition_uuid,
                    fighter_id=fighter_uuid,
                    corner=comp_dto.corner,
                    outcome=comp_dto.outcome,
                )
                self._resolver._db.add(competitor)
                result.inserted += 1

        return result
