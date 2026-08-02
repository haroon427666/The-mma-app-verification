"""ESPN sync jobs bridging provider → pipeline → upsert → database."""

from src.providers.espn.jobs.promotion import ESPN_PromotionSyncJob
from src.providers.espn.jobs.venue import ESPN_VenueSyncJob
from src.providers.espn.jobs.weight_class import ESPN_WeightClassSyncJob
from src.providers.espn.jobs.fighter import ESPN_FighterSyncJob
from src.providers.espn.jobs.event import ESPN_EventSyncJob
from src.providers.espn.jobs.competition import ESPN_CompetitionSyncJob
from src.providers.espn.jobs.broadcast import ESPN_BroadcastSyncJob
from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob
from src.providers.espn.jobs.statistics import ESPN_StatisticSyncJob

__all__ = [
    "ESPN_PromotionSyncJob",
    "ESPN_VenueSyncJob",
    "ESPN_WeightClassSyncJob",
    "ESPN_FighterSyncJob",
    "ESPN_EventSyncJob",
    "ESPN_CompetitionSyncJob",
    "ESPN_BroadcastSyncJob",
    "ESPN_RankingSyncJob",
    "ESPN_StatisticSyncJob",
]
