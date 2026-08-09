"""RankingUpsert — idempotent ranking replacement.

Rankings use a REPLACE strategy (not merge): old rankings for a given
(promotion, category) are deleted, then new rankings are inserted.

ATOMICITY: the delete + insert happens within the same database transaction.
If the process crashes between DELETE and INSERT, the transaction rolls back
and rankings are preserved from the previous sync. No data loss.

Protected by DB unique constraint: uq_ranking_fighter_category on
(promotion_id, category, fighter_id) prevents duplicate entries.
"""

import logging
from typing import TYPE_CHECKING

from src.domain.models.ranking import Ranking
from src.providers.dto import RankingDTO
from src.sync.upsert import UpsertResult

if TYPE_CHECKING:
    from src.sync.upserts.id_resolver import IdResolver

logger = logging.getLogger(__name__)


class RankingUpsert:
    """Ranking REPLACE strategy — atomic per (promotion, category)."""

    entity_type = "ranking"
    provider = "espn"

    def __init__(self, resolver: "IdResolver") -> None:
        self._resolver: IdResolver = resolver

    async def upsert_batch(self, dtos: list[RankingDTO]) -> UpsertResult:
        """Atomic replace per (promotion, category) group.

        Within one transaction:
        1. DELETE all rankings for (promotion_id, category)
        2. INSERT new rankings

        If step 2 fails, the DELETE is rolled back — rankings preserved.
        """
        from sqlalchemy import delete

        if not dtos:
            return UpsertResult.empty()

        # Group by (promotion, category) for atomic deletion
        groups: dict[tuple[str, str], list[RankingDTO]] = {}
        for dto in dtos:
            key = (dto.promotion_external_id, dto.category)
            groups.setdefault(key, []).append(dto)

        result = UpsertResult()

        for (promo_eid, category), group_dtos in groups.items():
            try:
                promo_uuid = await self._resolver.resolve(
                    self.provider, promo_eid, "promotion"
                )
                if promo_uuid is None:
                    logger.warning(f"Promotion {promo_eid} not found — skipping rankings")
                    result.errors += len(group_dtos)
                    continue

                # DELETE old rankings (within same transaction — atomic)
                await self._resolver._db.execute(
                    delete(Ranking).where(
                        Ranking.promotion_id == promo_uuid,
                        Ranking.category_name == category,
                    )
                )

                # INSERT new rankings
                for dto in group_dtos:
                    try:
                        fighter_uuid = await self._resolver.resolve(
                            self.provider, dto.fighter_external_id, "fighter"
                        )
                        if fighter_uuid is None:
                            continue

                        wclass_uuid = None
                        if dto.weight_class_external_id:
                            wclass_uuid = await self._resolver.resolve(
                                self.provider, dto.weight_class_external_id, "weight_class"
                            )

                        ranking = Ranking(
                            provider=self.provider,
                            promotion_id=promo_uuid,
                            fighter_id=fighter_uuid,
                            weight_class_id=wclass_uuid,
                            category_name=category,
                            rank=dto.rank,
                            trend=dto.trend,
                            is_champion=dto.is_champion,
                        )
                        self._resolver._db.add(ranking)
                        result.inserted += 1

                    except Exception as e:
                        logger.error(f"Ranking insert failed: {e}")
                        result.errors += 1
                        result.error_details.append(str(e))

            except Exception as e:
                logger.error(f"Ranking group {category} failed: {e}")
                result.errors += len(group_dtos)

        return result
