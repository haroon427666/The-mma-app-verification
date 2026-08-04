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
from src.sync.engine import SyncEngine
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
from src.sync.metrics import (
    DatabaseMetrics,
    EntityMetrics,
    HttpMetrics,
    ProviderMetrics,
    SyncMetrics,
)
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
    AGGRESSIVE_RETRY,
    DEFAULT_RETRY,
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
from src.sync.state_store import MemorySyncStateStore, SyncStateStore
from src.sync.state_store import MemorySyncStateStore as MemoryStateStore
from src.sync.strategy import SyncDecision, SyncStrategy
from src.sync.types import (
    ESPN_CAPABILITIES,
    ESPN_V1,
    EntityType,
    JobStatus,
    ProviderCapabilities,
    SyncMode,
    SyncSchemaVersion,
    SyncStatus,
)
from src.sync.upsert import UpsertResult

__all__ = [
    "AGGRESSIVE_RETRY",
    "DEFAULT_RETRY",
    "ESPN_CAPABILITIES",
    "ESPN_V1",
    "LONG_RUNNING_RETRY",
    "PLAN_REGISTRY",
    "Alert",
    "AlertManager",
    "AlertThresholds",
    "CancellationToken",
    "CancelledError",
    # Failure handling
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    # Infrastructure
    "Clock",
    "DatabaseMetrics",
    "DeadLetterQueue",
    "DeadLetterRecord",
    # Dependency
    "DependencyGraph",
    "EntityMetrics",
    # Types
    "EntityType",
    "EventsPlan",
    # Lock
    "ExecutionLock",
    "ExponentialBackoff",
    "FailureCategory",
    "FailureClassifier",
    "FighterPlan",
    "FixedBackoff",
    "FoundationPlan",
    "FrozenClock",
    "FullSyncPlan",
    "HealthChecker",
    "HttpMetrics",
    "InMemoryLock",
    # Results
    "JobResult",
    "JobStatus",
    "MemoryStateStore",
    "MemorySyncStateStore",
    "MetricsExporter",
    "NoBackoff",
    "ProgressTracker",
    "ProviderCapabilities",
    "ProviderHealth",
    "ProviderMetrics",
    "RankingsPlan",
    "ReliabilityConfig",
    # Retry
    "RetryPolicy",
    "RunRecord",
    "SchedulerHealth",
    # Observability
    "StructuredLogger",
    "SyncBatch",
    "SyncContext",
    "SyncDecision",
    # Core
    "SyncEngine",
    # Events
    "SyncEventBus",
    "SyncEventCtx",
    "SyncJob",
    "SyncJobDefinition",
    # Metrics
    "SyncMetrics",
    "SyncMode",
    "SyncPipeline",
    # Plans
    "SyncPlan",
    "SyncResult",
    # Run
    "SyncRun",
    # Scheduler
    "SyncScheduler",
    "SyncSchemaVersion",
    # State
    "SyncState",
    "SyncStateStore",
    "SyncStatus",
    # Strategy
    "SyncStrategy",
    "SystemClock",
    "SystemHealth",
    "TimeoutPolicy",
    "UpsertResult",
    "default_reliability",
    "lock_key",
]
