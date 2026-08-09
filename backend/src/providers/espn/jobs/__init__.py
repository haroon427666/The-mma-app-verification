"""ESPN sync jobs bridging provider → pipeline → upsert → database."""

from src.providers.espn.jobs.broadcast import ESPN_BroadcastSyncJob
from src.providers.espn.jobs.competition import ESPN_CompetitionSyncJob
from src.providers.espn.jobs.event import ESPN_EventSyncJob
from src.providers.espn.jobs.fighter import ESPN_FighterSyncJob
from src.providers.espn.jobs.historical_event import ESPN_HistoricalEventSyncJob
from src.providers.espn.jobs.promotion import ESPN_PromotionSyncJob
from src.providers.espn.jobs.ranking import ESPN_RankingSyncJob
from src.providers.espn.jobs.statistics import ESPN_StatisticSyncJob
from src.providers.espn.jobs.venue import ESPN_VenueSyncJob
from src.providers.espn.jobs.weight_class import ESPN_WeightClassSyncJob

__all__ = [
    "ESPN_BroadcastSyncJob",
    "ESPN_CompetitionSyncJob",
    "ESPN_EventSyncJob",
    "ESPN_FighterSyncJob",
    "ESPN_HistoricalEventSyncJob",
    "ESPN_PromotionSyncJob",
    "ESPN_RankingSyncJob",
    "ESPN_StatisticSyncJob",
    "ESPN_VenueSyncJob",
    "ESPN_WeightClassSyncJob",
]
