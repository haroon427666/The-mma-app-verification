"""
Enterprise Scheduler Jobs — pre-built job definitions for every data source.

Each source (UFC, ESPN, UFCStats, TheSportsDB, Wikipedia, Tapology, Sherdog)
has a complete schedule with dependencies, retry policies, and monitoring.

All jobs use the JobScheduler from platform.scheduler and BaseConnector
from platform.connectors.
"""

from platform.scheduler import JobDefinition, JobPriority, TriggerType

# ═══════════════════════════════════════════════════════════════════════════
# ESPN — Primary structured data source
# ═══════════════════════════════════════════════════════════════════════════

ESPN_FULL_SYNC = JobDefinition(
    id="espn_full_sync",
    connector="espn",
    entity_type="all",
    trigger_type=TriggerType.CRON,
    cron="0 2 * * *",
    priority=JobPriority.HIGH,
    max_retries=2,
    retry_backoff_base=60.0,
    timeout_seconds=600,
    concurrency_limit=1,
    tags={"source": "espn", "type": "full"},
)

ESPN_FIGHTERS = JobDefinition(
    id="espn_fighters",
    connector="espn",
    entity_type="fighter",
    trigger_type=TriggerType.CRON,
    cron="0 */12 * * *",
    priority=JobPriority.NORMAL,
    max_retries=3,
    depends_on=["espn_weight_classes"],
    tags={"source": "espn", "entity": "fighter"},
)

ESPN_WEIGHT_CLASSES = JobDefinition(
    id="espn_weight_classes",
    connector="espn",
    entity_type="weight_class",
    trigger_type=TriggerType.CRON,
    cron="0 0 * * 0",
    priority=JobPriority.LOW,
    tags={"source": "espn", "entity": "weight_class"},
)

ESPN_EVENTS = JobDefinition(
    id="espn_events",
    connector="espn",
    entity_type="event",
    trigger_type=TriggerType.INTERVAL,
    interval_seconds=1800,
    priority=JobPriority.HIGH,
    depends_on=["espn_fighters", "espn_weight_classes"],
    tags={"source": "espn", "entity": "event"},
)

ESPN_LIVE_EVENTS = JobDefinition(
    id="espn_live_events",
    connector="espn",
    entity_type="event_live",
    trigger_type=TriggerType.INTERVAL,
    interval_seconds=30,
    priority=JobPriority.LIVE,
    timeout_seconds=15,
    tags={"source": "espn", "entity": "live"},
)

ESPN_RANKINGS = JobDefinition(
    id="espn_rankings",
    connector="espn",
    entity_type="ranking",
    trigger_type=TriggerType.CRON,
    cron="0 */6 * * *",
    priority=JobPriority.NORMAL,
    depends_on=["espn_fighters"],
    tags={"source": "espn", "entity": "ranking"},
)

ESPN_RESULTS = JobDefinition(
    id="espn_results",
    connector="espn",
    entity_type="competition",
    trigger_type=TriggerType.INTERVAL,
    interval_seconds=120,
    priority=JobPriority.CRITICAL,
    depends_on=["espn_events"],
    tags={"source": "espn", "entity": "results"},
)

# ═══════════════════════════════════════════════════════════════════════════
# TheSportsDB — Media enrichment
# ═══════════════════════════════════════════════════════════════════════════

TSDB_MEDIA_SYNC = JobDefinition(
    id="tsdb_media_sync",
    connector="thesportsdb",
    entity_type="media",
    trigger_type=TriggerType.CRON,
    cron="0 5 * * 0",
    priority=JobPriority.LOW,
    max_retries=2,
    timeout_seconds=300,
    tags={"source": "thesportsdb", "type": "weekly"},
)

TSDB_PROMOTIONS = JobDefinition(
    id="tsdb_promotions",
    connector="thesportsdb",
    entity_type="promotion",
    trigger_type=TriggerType.CRON,
    cron="0 6 * * 0",
    priority=JobPriority.LOW,
    tags={"source": "thesportsdb", "entity": "promotion"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Wikipedia — Reference data
# ═══════════════════════════════════════════════════════════════════════════

WIKIPEDIA_FIGHTERS = JobDefinition(
    id="wikipedia_fighters",
    connector="wikipedia",
    entity_type="fighter_bio",
    trigger_type=TriggerType.CRON,
    cron="0 8 * * 1",
    priority=JobPriority.LOW,
    timeout_seconds=600,
    tags={"source": "wikipedia", "entity": "fighter"},
)

WIKIPEDIA_EVENTS = JobDefinition(
    id="wikipedia_events",
    connector="wikipedia",
    entity_type="event_info",
    trigger_type=TriggerType.CRON,
    cron="0 10 * * 1",
    priority=JobPriority.LOW,
    tags={"source": "wikipedia", "entity": "event"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Sherdog — Fight records + history
# ═══════════════════════════════════════════════════════════════════════════

SHERDOG_FIGHTERS = JobDefinition(
    id="sherdog_fighters",
    connector="sherdog",
    entity_type="fighter_record",
    trigger_type=TriggerType.CRON,
    cron="0 12 * * 2",
    priority=JobPriority.LOW,
    max_retries=3,
    timeout_seconds=900,
    tags={"source": "sherdog", "entity": "fighter"},
)

SHERDOG_EVENTS = JobDefinition(
    id="sherdog_events",
    connector="sherdog",
    entity_type="event",
    trigger_type=TriggerType.CRON,
    cron="0 14 * * 2",
    priority=JobPriority.LOW,
    tags={"source": "sherdog", "entity": "event"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Tapology — Rankings + community data
# ═══════════════════════════════════════════════════════════════════════════

TAPOLOGY_RANKINGS = JobDefinition(
    id="tapology_rankings",
    connector="tapology",
    entity_type="ranking",
    trigger_type=TriggerType.CRON,
    cron="0 16 * * 3",
    priority=JobPriority.LOW,
    tags={"source": "tapology", "entity": "ranking"},
)

TAPOLOGY_FIGHTERS = JobDefinition(
    id="tapology_fighters",
    connector="tapology",
    entity_type="fighter",
    trigger_type=TriggerType.CRON,
    cron="0 18 * * 3",
    priority=JobPriority.LOW,
    tags={"source": "tapology", "entity": "fighter"},
)

# ═══════════════════════════════════════════════════════════════════════════
# UFCStats — Detailed fight statistics
# ═══════════════════════════════════════════════════════════════════════════

UFCSTATS_SYNC = JobDefinition(
    id="ufcstats_sync",
    connector="ufcstats",
    entity_type="statistics",
    trigger_type=TriggerType.CRON,
    cron="0 20 * * 3",
    priority=JobPriority.LOW,
    max_retries=2,
    timeout_seconds=900,
    tags={"source": "ufcstats", "entity": "statistics"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Official UFC API
# ═══════════════════════════════════════════════════════════════════════════

OFFICIAL_UFC_SYNC = JobDefinition(
    id="official_ufc_sync",
    connector="official_ufc",
    entity_type="all",
    trigger_type=TriggerType.CRON,
    cron="0 3 * * *",
    priority=JobPriority.HIGH,
    max_retries=2,
    timeout_seconds=600,
    tags={"source": "official_ufc", "type": "daily"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Maintenance jobs
# ═══════════════════════════════════════════════════════════════════════════

DATA_LAKE_CLEANUP = JobDefinition(
    id="datalake_cleanup",
    connector="datalake",
    entity_type="cleanup",
    trigger_type=TriggerType.CRON,
    cron="0 4 * * 0",
    priority=JobPriority.BACKGROUND,
    timeout_seconds=300,
    tags={"type": "maintenance"},
)

QUALITY_RESCORE = JobDefinition(
    id="quality_rescore",
    connector="quality",
    entity_type="rescoring",
    trigger_type=TriggerType.CRON,
    cron="0 1 * * *",
    priority=JobPriority.BACKGROUND,
    timeout_seconds=600,
    tags={"type": "maintenance"},
)

# ═══════════════════════════════════════════════════════════════════════════
# Registry — all jobs
# ═══════════════════════════════════════════════════════════════════════════

ALL_JOBS: dict[str, JobDefinition] = {
    # ESPN (primary)
    "espn_full_sync": ESPN_FULL_SYNC,
    "espn_fighters": ESPN_FIGHTERS,
    "espn_weight_classes": ESPN_WEIGHT_CLASSES,
    "espn_events": ESPN_EVENTS,
    "espn_live_events": ESPN_LIVE_EVENTS,
    "espn_rankings": ESPN_RANKINGS,
    "espn_results": ESPN_RESULTS,
    # TheSportsDB
    "tsdb_media_sync": TSDB_MEDIA_SYNC,
    "tsdb_promotions": TSDB_PROMOTIONS,
    # Wikipedia
    "wikipedia_fighters": WIKIPEDIA_FIGHTERS,
    "wikipedia_events": WIKIPEDIA_EVENTS,
    # Sherdog
    "sherdog_fighters": SHERDOG_FIGHTERS,
    "sherdog_events": SHERDOG_EVENTS,
    # Tapology
    "tapology_rankings": TAPOLOGY_RANKINGS,
    "tapology_fighters": TAPOLOGY_FIGHTERS,
    # UFCStats
    "ufcstats_sync": UFCSTATS_SYNC,
    # Official UFC
    "official_ufc_sync": OFFICIAL_UFC_SYNC,
    # Maintenance
    "datalake_cleanup": DATA_LAKE_CLEANUP,
    "quality_rescore": QUALITY_RESCORE,
}

# ═══════════════════════════════════════════════════════════════════════════
# Dependency Graph
# ═══════════════════════════════════════════════════════════════════════════

DEPENDENCY_GRAPH: dict[str, list[str]] = {
    "espn_weight_classes": [],         # No deps — runs first
    "espn_fighters": ["espn_weight_classes"],
    "espn_events": ["espn_fighters", "espn_weight_classes"],
    "espn_rankings": ["espn_fighters"],
    "espn_results": ["espn_events"],
    "espn_live_events": ["espn_events"],
    "espn_full_sync": [],              # Independent
    "tsdb_media_sync": [],
    "tsdb_promotions": [],
    "wikipedia_fighters": [],
    "wikipedia_events": [],
    "sherdog_fighters": [],
    "sherdog_events": [],
    "tapology_rankings": [],
    "tapology_fighters": [],
    "ufcstats_sync": [],
    "official_ufc_sync": [],
    "datalake_cleanup": [],
    "quality_rescore": [],
}

# ═══════════════════════════════════════════════════════════════════════════
# Dashboard Configuration — monitoring rules per job
# ═══════════════════════════════════════════════════════════════════════════

JOB_MONITORING: dict[str, dict] = {
    "espn_live_events": {"alert_on_failure": True, "max_latency_ms": 5000},
    "espn_results": {"alert_on_failure": True, "max_latency_ms": 10000},
    "espn_full_sync": {"alert_on_failure": True, "max_latency_ms": 600000},
    "espn_fighters": {"alert_on_failure": True, "max_latency_ms": 300000},
    "espn_events": {"alert_on_failure": True, "max_latency_ms": 120000},
    "espn_rankings": {"alert_on_failure": False, "max_latency_ms": 60000},
}
