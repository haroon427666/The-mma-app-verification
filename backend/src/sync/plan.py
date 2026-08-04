"""
Sync plan — defines WHAT to sync and in WHAT order.

The engine only knows how to execute plans. It has zero knowledge of
entities, dependencies, or ordering. Plans define all of that.

This separation means:
- NightlyPlan runs 9 jobs in dependency order
- RankingsPlan runs 1 job
- FighterOnlyPlan runs 1 job + its dependencies
- LiveEventsPlan runs events + competitions + broadcasts

All reuse the exact same SyncEngine.
"""

from dataclasses import dataclass, field

from src.sync.types import EntityType


@dataclass
class SyncPlan:
    """A plan defines which jobs to run and in what order.

    The engine executes jobs in `order` sequence. Each entry maps
    to exactly one SyncJob subclass by entity_type.

    Plans can be composed: a FullSyncPlan contains a RankingsPlan, etc.
    """

    name: str = "unknown"                   # "full_sync", "rankings_only", etc.
    description: str = ""                   # Human-readable description
    order: list[EntityType] = field(default_factory=list)
    """Execution order. The engine runs jobs in this sequence.
    Dependencies are satisfied by position: index 0 has no deps,
    index 1 depends on index 0, etc.
    """

    def __post_init__(self) -> None:
        if not self.order:
            raise ValueError(f"SyncPlan '{self.name}' has no jobs in order")

    @property
    def job_count(self) -> int:
        return len(self.order)

    def depends_on(self, entity: EntityType) -> list[EntityType]:
        """Return entities that must complete before the given entity."""
        idx = self.order.index(entity) if entity in self.order else -1
        return self.order[:idx] if idx > 0 else []


# ── Pre-built Plans ───────────────────────────────────────────────────────────


class FullSyncPlan(SyncPlan):
    """Complete sync: all 9 entity types in dependency order.

    Order ensures foreign keys exist: promotions → venues → weight_classes
    → fighters → events → competitions → broadcasts → statistics → rankings.
    """

    def __init__(self) -> None:
        super().__init__(
            name="full_sync",
            description="Complete sync of all 9 entity types in dependency order",
            order=[
                EntityType.PROMOTION,
                EntityType.VENUE,
                EntityType.WEIGHT_CLASS,
                EntityType.FIGHTER,
                EntityType.EVENT,
                EntityType.COMPETITION,
                EntityType.BROADCAST,
                EntityType.STATISTIC,
                EntityType.RANKING,
            ],
        )


class RankingsPlan(SyncPlan):
    """Rankings-only sync (lightweight, runs every 12h)."""

    def __init__(self) -> None:
        super().__init__(
            name="rankings_sync",
            description="Rankings update only — assumes fighters and promotions exist",
            order=[EntityType.RANKING],
        )


class EventsPlan(SyncPlan):
    """Events-focused sync for live/upcoming updates."""

    def __init__(self) -> None:
        super().__init__(
            name="events_sync",
            description="Events + competitions + broadcasts (live/upcoming)",
            order=[
                EntityType.EVENT,
                EntityType.COMPETITION,
                EntityType.BROADCAST,
            ],
        )


class FighterPlan(SyncPlan):
    """Fighter-only sync (useful for targeted updates)."""

    def __init__(self) -> None:
        super().__init__(
            name="fighter_sync",
            description="Fighter profiles + statistics",
            order=[
                EntityType.FIGHTER,
                EntityType.STATISTIC,
            ],
        )


class FoundationPlan(SyncPlan):
    """Foundation entities that rarely change."""

    def __init__(self) -> None:
        super().__init__(
            name="foundation_sync",
            description="Promotions, venues, weight classes (rarely change)",
            order=[
                EntityType.PROMOTION,
                EntityType.VENUE,
                EntityType.WEIGHT_CLASS,
            ],
        )
