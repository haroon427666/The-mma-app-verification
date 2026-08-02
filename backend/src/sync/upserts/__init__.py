"""Upsert services — one per entity, all idempotent.

Each upsert handles:
- External ID resolution (provider:external_id → internal UUID)
- Insert or update (changed fields only)
- Nullable field safety
- Batch writes with UpsertResult counts

Usage:
    resolver = IdResolver(db_session)
    upsert = FighterUpsert(resolver)
    result = await upsert.upsert_batch(fighter_dtos)
    # result.inserted, result.updated, result.skipped, result.errors
"""

from src.sync.upserts.base import BaseUpsert
from src.sync.upserts.id_resolver import IdResolver
from src.sync.upserts.promotion import PromotionUpsert
from src.sync.upserts.venue import VenueUpsert
from src.sync.upserts.weight_class import WeightClassUpsert
from src.sync.upserts.fighter import FighterUpsert
from src.sync.upserts.event import EventUpsert
from src.sync.upserts.competition import CompetitionUpsert
from src.sync.upserts.broadcast import BroadcastUpsert
from src.sync.upserts.ranking import RankingUpsert
from src.sync.upserts.statistics import StatisticsUpsert

__all__ = [
    "BaseUpsert",
    "IdResolver",
    "PromotionUpsert",
    "VenueUpsert",
    "WeightClassUpsert",
    "FighterUpsert",
    "EventUpsert",
    "CompetitionUpsert",
    "BroadcastUpsert",
    "RankingUpsert",
    "StatisticsUpsert",
]
