"""All ORM models — single import surface."""

from src.db.models.auth import (
    Device,
    EventFavorite,
    FighterFavorite,
    Notification,
    User,
    UserPreference,
    UserSession,
    WatchlistEvent,
)
from src.db.models.core import Broadcast, Promotion, Ranking, Statistic, Venue, WeightClass
from src.db.models.event import Competition, Competitor, Event
from src.db.models.fighter import Fighter, FighterRecord
from src.db.models.support import (
    DeadLetter,
    ExternalId,
    FighterProviderRecordStatus,
    ProviderConflict,
    ProviderPayload,
    SyncCheckpoint,
    SyncJob,
    SyncRun,
)

__all__ = [
    "Broadcast",
    "Competition",
    "Competitor",
    "DeadLetter",
    "Device",
    "Event",
    "EventFavorite",
    "ExternalId",
    "Fighter",
    "FighterFavorite",
    "FighterProviderRecordStatus",
    "FighterRecord",
    "Notification",
    "Promotion",
    "ProviderConflict",
    "ProviderPayload",
    "Ranking",
    "Statistic",
    "SyncCheckpoint",
    "SyncJob",
    "SyncRun",
    "User",
    "UserPreference",
    "UserSession",
    "Venue",
    "WatchlistEvent",
    "WeightClass",
]
