"""StatisticsUpsert — idempotent statistic upsert.

Statistics are tied to a specific competitor row: (fighter_id, competition_id).
If the competitor cannot be resolved, the statistic is SKIPPED — it will be
retried on the next sync run after the fighter/competition is synced.

NO GUESSING: we never attach stats to a "most recent" competitor.
Wrong attribution is worse than a delayed stat.
"""

import logging

from src.domain.models.competitor import Competitor
from src.domain.models.statistic import Statistic
from src.providers.dto import StatisticDTO
from src.sync.upsert import UpsertResult

logger = logging.getLogger(__name__)


class StatisticsUpsert:
    """Statistics upsert — matched by (competitor_id, label).

    Does NOT extend BaseUpsert because statistics lack provider external IDs.
    Instead, matched by composite key: (competitor_id, label).
    """

    entity_type = "statistic"
    provider = "espn"

    def __init__(self, resolver: "IdResolver") -> None:
        from src.sync.upserts.id_resolver import IdResolver
        self._resolver: IdResolver = resolver

    async def upsert_batch(self, dtos: list[StatisticDTO]) -> UpsertResult:
        """Upsert statistics: resolve competitor_id, then insert/update.

        If competitor cannot be resolved: SKIP with warning.
        The stat will be picked up on the next sync run after the fighter
        and competition have been synced.
        """
        from sqlalchemy import select

        if not dtos:
            return UpsertResult.empty()

        result = UpsertResult()

        for dto in dtos:
            try:
                # Resolve fighter UUID
                fighter_uuid = await self._resolver.resolve(
                    self.provider, dto.fighter_external_id, "fighter"
                )
                if fighter_uuid is None:
                    logger.warning(
                        f"Statistic skipped: fighter {dto.fighter_external_id} "
                        f"not yet synced — will retry next run"
                    )
                    result.skipped += 1
                    continue

                # Resolve competitor: (competition_id, fighter_id)
                competitor_id = None
                if dto.competition_external_id:
                    comp_uuid = await self._resolver.resolve(
                        self.provider, dto.competition_external_id, "competition"
                    )
                    if comp_uuid:
                        row = await self._resolver._db.execute(
                            select(Competitor.id).where(
                                Competitor.competition_id == comp_uuid,
                                Competitor.fighter_id == fighter_uuid,
                            )
                        )
                        competitor_id = row.scalar_one_or_none()

                if competitor_id is None:
                    logger.warning(
                        f"Statistic skipped: competitor not found for "
                        f"fighter={dto.fighter_external_id} "
                        f"competition={dto.competition_external_id} "
                        f"— will retry next run"
                    )
                    result.skipped += 1
                    continue

                # Upsert the statistic by (competitor_id, label)
                existing = await self._resolver._db.execute(
                    select(Statistic).where(
                        Statistic.competitor_id == competitor_id,
                        Statistic.label == dto.label,
                    )
                )
                existing_row = existing.scalar_one_or_none()

                if existing_row:
                    if (existing_row.value != dto.value or
                        existing_row.display_value != dto.display_value):
                        existing_row.value = dto.value
                        existing_row.display_value = dto.display_value
                        self._resolver._db.add(existing_row)
                        result.updated += 1
                    else:
                        result.skipped += 1
                else:
                    stat = Statistic(
                        competitor_id=competitor_id,
                        category=dto.category,
                        label=dto.label,
                        value=dto.value,
                        display_value=dto.display_value,
                    )
                    self._resolver._db.add(stat)
                    result.inserted += 1

            except Exception as e:
                logger.error(f"Statistic upsert failed: {e}")
                result.errors += 1
                result.error_details.append(str(e))

        return result
