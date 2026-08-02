"""
Sync engine — public API.

Provider-agnostic sync orchestration. Nothing here depends on ESPN.
Everything is injected: provider, plan, state store, events, retry policy.
"""

from src.sync.batch import SyncBatch
from src.sync.clock import Clock, FrozenClock, SystemClock
from src.sync.context import CancellationToken, CancelledError, ProgressTracker, SyncContext
from src.sync.dead_letter import DeadLetterQueue, DeadLetterRecord
from src.sync.dependency import DependencyGraph
from src.sync.engine import MemorySyncStateStore, SyncEngine
from src.sync.events import SyncEventBus, SyncEventCtx
from src.sync.failure import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    FailureCategory,
    FailureClassifier,
)
from src.sync.job import JobResult, SyncJob
from src.sync.lock import ExecutionLock, InMemoryLock, lock_key
from src.sync.metrics import DatabaseMetrics, EntityMetrics, HttpMetrics, ProviderMetrics, SyncMetrics
from src.sync.observability import (
    Alert,
    AlertManager,
    AlertThresholds,
    HealthChecker,
    MetricsExporter,
    ProviderHealth,
    SchedulerHealth,
    StructuredLogger,
    SystemHealth,
)
from src.sync.pipeline import SyncPipeline
from src.sync.plan import (
    EventsPlan,
    FighterPlan,
    FoundationPlan,
    FullSyncPlan,
    RankingsPlan,
    SyncPlan,
)
from src.sync.reliability import ReliabilityConfig, default_reliability
from src.sync.result import SyncResult
from src.sync.retry import (
    DEFAULT_RETRY,
    AGGRESSIVE_RETRY,
    LONG_RUNNING_RETRY,
    ExponentialBackoff,
    FixedBackoff,
    NoBackoff,
    RetryPolicy,
    TimeoutPolicy,
)
from src.sync.run import SyncRun
from src.sync.scheduler import PLAN_REGISTRY, RunRecord, SyncJobDefinition, SyncScheduler
from src.sync.state import SyncState
from src.sync.state_store import MemorySyncStateStore as MemoryStateStore, SyncStateStore
from src.sync.strategy import SyncDecision, SyncStrategy
from src.sync.types import (
    ESPN_V1,
    ESPN_CAPABILITIES,
    EntityType,
    JobStatus,
    ProviderCapabilities,
    SyncMode,
    SyncSchemaVersion,
    SyncStatus,
)
from src.sync.upsert import UpsertResult

__all__ = [
    # Core
    "SyncEngine",
    "SyncJob",
    "SyncContext",
    "SyncPipeline",
    # Dependency
    "DependencyGraph",
    # Plans
    "SyncPlan",
    "FullSyncPlan",
    "RankingsPlan",
    "EventsPlan",
    "FighterPlan",
    "FoundationPlan",
    # State
    "SyncState",
    "SyncStateStore",
    "MemoryStateStore",
    "MemorySyncStateStore",
    # Run
    "SyncRun",
    "SyncBatch",
    # Results
    "JobResult",
    "SyncResult",
    "UpsertResult",
    # Strategy
    "SyncStrategy",
    "SyncDecision",
    # Types
    "EntityType",
    "JobStatus",
    "SyncStatus",
    "SyncMode",
    "SyncSchemaVersion",
    "ESPN_V1",
    "ProviderCapabilities",
    "ESPN_CAPABILITIES",
    # Scheduler
    "SyncScheduler",
    "SyncJobDefinition",
    "RunRecord",
    "PLAN_REGISTRY",
    # Lock
    "ExecutionLock",
    "InMemoryLock",
    "lock_key",
    # Failure handling
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "FailureCategory",
    "FailureClassifier",
    "DeadLetterQueue",
    "DeadLetterRecord",
    "ReliabilityConfig",
    "default_reliability",
    # Observability
    "StructuredLogger",
    "MetricsExporter",
    "HealthChecker",
    "SystemHealth",
    "ProviderHealth",
    "SchedulerHealth",
    "AlertManager",
    "Alert",
    "AlertThresholds",
    # Infrastructure
    "Clock",
    "SystemClock",
    "FrozenClock",
    "CancellationToken",
    "CancelledError",
    "ProgressTracker",
    # Metrics
    "SyncMetrics",
    "EntityMetrics",
    "ProviderMetrics",
    "DatabaseMetrics",
    "HttpMetrics",
    # Events
    "SyncEventBus",
    "SyncEventCtx",
    # Retry
    "RetryPolicy",
    "ExponentialBackoff",
    "FixedBackoff",
    "NoBackoff",
    "TimeoutPolicy",
    "DEFAULT_RETRY",
    "AGGRESSIVE_RETRY",
    "LONG_RUNNING_RETRY",
]
