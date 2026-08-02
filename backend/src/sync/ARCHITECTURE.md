# Phase 3.1 — Sync Architecture (Revised)

**Status:** Pending Approval
**Author:** Zaro AI
**Date:** 2026-08-01
**Revision:** 2 — incorporates 10 review adjustments + SyncPipeline layer

---

## Layer Architecture

```
                    ┌──────────────────────────┐
                    │      APScheduler          │
                    │  (cron / manual trigger)  │
                    └────────────┬─────────────┘
                                 │ launches
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         SyncEngine                                     │
│                                                                        │
│  Receives: SyncPlan + BaseDataProvider                                 │
│  Knows: NOTHING about entities, dependencies, or ordering              │
│                                                                        │
│  For each EntityType in plan.order:                                   │
│    ├── Load SyncState (checkpoint, cursor, last sync)                 │
│    ├── Look up SyncJob from registry                                  │
│    └── Delegate to SyncPipeline                                       │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ delegates per-job
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                         SyncPipeline                                   │
│                                                                        │
│  Owns: retries, batching, pagination, cancellation, metrics,           │
│        checkpointing, event hooks, progress tracking                   │
│                                                                        │
│  execute(job, ctx, state, events):                                    │
│    1. Decide full vs incremental (from state.can_incremental)          │
│    2. retry( job._fetch(ctx, state) )          ← RetryPolicy injected │
│    3. job._transform(ctx, dtos)                                        │
│    4. For each batch:                                                  │
│         token.check()                                                   │
│         job._upsert(ctx, batch)                                        │
│         state.update_progress(page, offset, count)  ← checkpoint       │
│         events.fire_batch_complete()                                   │
│    5. Collect metrics, fire after_job event                            │
└────────────────────────────────┬───────────────────────────────────────┘
                                 │ calls _fetch / _upsert
                                 ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          SyncJob (abstract)                            │
│                                                                        │
│  Metadata (class attributes):                                          │
│    entity_type: EntityType       ← enum, never string                  │
│    depends_on: list[EntityType]   ← for plan validation                │
│    critical: bool               ← abort run on failure?                │
│    batch_size: int              ← items per DB write batch             │
│    supports_incremental: bool   ← can do delta sync?                   │
│                                                                        │
│  Methods (subclasses implement):                                       │
│    _fetch(ctx, state) → list[DTO]                                      │
│    _transform(ctx, dtos) → list[DTO]  (optional, default pass-through) │
│    _upsert(ctx, dtos) → dict[str, int]                                 │
│                                                                        │
│  Jobs are tiny — typically 30-80 lines.                                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Component Catalog (13 components)

| # | Component | File | Purpose |
|---|---|---|---|
| 1 | **EntityType** | `types.py` | Enum — no magic strings anywhere |
| 2 | **SyncSchemaVersion** | `types.py` | Provider schema versioning for conditional transforms |
| 3 | **Clock** | `clock.py` | Injectable time source (SystemClock / FrozenClock) |
| 4 | **SyncState** | `state.py` | Per-entity checkpoint: cursor, page, etag, updated_since, last sync |
| 5 | **SyncContext** | `context.py` | Immutable dependency bag: provider, db, clock, metrics, token, progress |
| 6 | **SyncMetrics** | `metrics.py` | Strongly-typed: ProviderMetrics, DatabaseMetrics, HttpMetrics, EntityMetrics |
| 7 | **SyncEventBus** | `events.py` | BeforeSync, AfterSync, BeforeJob, AfterJob, OnFailure, OnRetry, OnBatchComplete |
| 8 | **RetryPolicy** | `retry.py` | Injectable: ExponentialBackoff, FixedBackoff, NoBackoff, TimeoutPolicy |
| 9 | **SyncPlan** | `plan.py` | Defines WHAT and ORDER: FullSyncPlan, RankingsPlan, EventsPlan, FoundationPlan |
| 10 | **SyncJob** | `job.py` | Abstract base with metadata: entity_type, depends_on, critical, batch_size |
| 11 | **SyncPipeline** | `pipeline.py` | Owns retries, batching, checkpointing, cancellation, events — injected between engine and job |
| 12 | **SyncEngine** | `engine.py` | Plan-based orchestrator — zero entity knowledge |
| 13 | **SyncResult** | `result.py` | Immutable aggregate: overall_status + per-job JobResults |

---

## File Tree

```
src/sync/
├── __init__.py          (2.1 KB) —  Public API (38 exports)
├── types.py             (2.3 KB) —  EntityType, JobStatus, SyncStatus, SyncSchemaVersion
├── clock.py             (2.1 KB) —  Clock, SystemClock, FrozenClock
├── context.py           (3.9 KB) —  SyncContext, CancellationToken, ProgressTracker
├── state.py             (6.5 KB) —  SyncState (cursor, page, etag, updated_since, checkpoint)
├── metrics.py           (6.8 KB) —  SyncMetrics, ProviderMetrics, DatabaseMetrics, HttpMetrics
├── events.py            (6.7 KB) —  SyncEventBus (7 hook types)
├── retry.py             (5.4 KB) —  RetryPolicy, ExponentialBackoff, TimeoutPolicy
├── plan.py              (4.2 KB) —  SyncPlan, FullSyncPlan, RankingsPlan, EventsPlan, FighterPlan, FoundationPlan
├── job.py               (4.6 KB) —  SyncJob (abstract, with metadata), JobResult
├── pipeline.py          (7.7 KB) —  SyncPipeline (retries, batching, checkpointing, events)
├── engine.py            (9.3 KB) —  SyncEngine (plan-based), SyncStateStore, MemorySyncStateStore
├── result.py            (3.1 KB) —  SyncResult (immutable aggregate)
└── ARCHITECTURE.md      (this file)
```

---

## How all 10 review points were addressed

| # | Issue | Solution |
|---|---|---|
| 1 | Missing SyncState | `state.py` — SyncState with cursor, page, etag, updated_since, checkpoint, status |
| 2 | SyncJob too generic | `job.py` — metadata: entity_type (EntityType), depends_on, critical, batch_size, supports_incremental |
| 3 | Dependency graph in engine | `plan.py` — SyncPlan defines order. Engine has zero entity knowledge. |
| 4 | Missing SyncPlan | 5 pre-built plans: FullSyncPlan, RankingsPlan, EventsPlan, FighterPlan, FoundationPlan |
| 5 | Mutable dict metrics | `metrics.py` — ProviderMetrics, DatabaseMetrics, HttpMetrics, EntityMetrics. All strongly typed fields. |
| 6 | Missing events | `events.py` — SyncEventBus with 7 hooks: BeforeSync, AfterSync, BeforeJob, AfterJob, OnFailure, OnRetry, OnBatchComplete |
| 7 | No RetryPolicy | `retry.py` — RetryPolicy + ExponentialBackoff + TimeoutPolicy. Injected. 3 presets. |
| 8 | No Clock | `clock.py` — Clock interface + SystemClock + FrozenClock. Injected. |
| 9 | Magic strings | `types.py` — EntityType enum used everywhere. Never a bare string. |
| 10 | No versioning | `types.py` — SyncSchemaVersion in context. ESPN_V1 constant. |
| 11 | Extra: Pipeline layer | `pipeline.py` — inserted between Engine and Job. Owns retries, batching, checkpointing. |

---

## Design Decisions

| Decision | Rationale |
|---|---|
| Engine knows nothing about entities | Engine executes plans. Plans define entities. Adding a new entity = new job + update plan. Engine unchanged. |
| Pipeline owns infrastructure concerns | Jobs are pure: fetch, transform, upsert. Pipeline handles retries, batching, cancellation. |
| State is per-entity, per-provider | A RankingsPlan for ESPN doesn't touch Tapology state. Each provider tracks independently. |
| Plans are composable | A NightlyPlan can wrap FoundationPlan + FighterPlan + EventsPlan. |
| Metrics are strongly typed | Prometheus/Grafana mapping is 1:1 with field names. No dict-to-metric translation. |
| FrozenClock for tests | Every timing-sensitive test freezes time. No sleep(), no flaky timing assertions. |

---

*End of Phase 3.1 (Revised) — pending approval.*
