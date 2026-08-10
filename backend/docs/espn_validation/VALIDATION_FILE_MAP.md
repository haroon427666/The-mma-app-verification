# VALIDATION FILE MAP — ESPN integration (commit `cda302c`)

> Legend: **[A]** added in commit · **[M]** modified in commit · **[E]** evidence/acceptance file (this package, not in commit)
> Status: `VERIFIED` (independently confirmed at package time) · `REPORTED` (per validation report §14/§21 — not re-run per lightweight policy)
> 69 files in commit `cda302c` (24 added, 45 modified) per `git show --name-status cda302c`.

## 1. ESPN integration docs (in commit)

| File | In commit | Role | Status |
|---|---|---|---|
| `backend/ESPN_INTEGRATION_PLAN.md` | A | Architecture & research mapping | VERIFIED (exists in commit) |
| `backend/ESPN_INTEGRATION_REPORT.md` | A | Implementation record (451 passed/1 skipped at impl close) | VERIFIED |
| `backend/ESPN_PRODUCTION_VALIDATION_REPORT.md` | A | **Primary acceptance evidence** (455/2, READY_FOR_COMMIT) | VERIFIED |
| `backend/ESPN_ENDPOINT_CATALOG.md` | M | Endpoint catalog | VERIFIED |
| `backend/PROJECT_STATUS.md` | M | Project status | VERIFIED |
| `SESSION_STATE.md` | M | Session state | VERIFIED |

## 2. Database migration

| File | In commit | Role | Status |
|---|---|---|---|
| `backend/alembic/versions/006_statistics_career.py` | A | Career statistics: `competitor_id` nullable + partial unique index `uq_statistics_career_fighter_cat_label` | VERIFIED — applied (live DB `alembic_version=006`, index present) |

## 3. Scripts & verification

| File | In commit | Role | Status |
|---|---|---|---|
| `backend/scripts/espn_live_benchmark.py` | A | Rate-envelope benchmark (3.22/2.68/3.02/3.00 rps) | VERIFIED — results in report §13 |
| `backend/verify_espn.py` | (pre-existing, not in commit) | Phase 5.5 live verification suite (80/80 field coverage) | REPORTED — used during implementation |

## 4. API layer

| File | In commit |
|---|---|
| `backend/src/api/sync.py` | M |
| `backend/src/api/utils.py` | A |
| `backend/src/api/v1/__init__.py` | M |
| `backend/src/api/v1/compare.py` | A |
| `backend/src/api/v1/events.py` | M |
| `backend/src/api/v1/fighters.py` | M |
| `backend/src/api/v1/fights.py` | M |
| `backend/src/api/v1/notifications.py` | M |
| `backend/src/api/v1/other.py` | M |
| `backend/src/api/v1/users.py` | M |
| `backend/src/api/v1/watchlist.py` | M |

## 5. Domain / DB / schemas / services

| File | In commit |
|---|---|
| `backend/src/db/models/core.py` | M |
| `backend/src/db/repositories/fighter.py` | M |
| `backend/src/domain/models/fighter.py` | M |
| `backend/src/schemas/fighter.py` | M |
| `backend/src/schemas/misc.py` | M |
| `backend/src/services/fighter_service.py` | M |

## 6. ESPN provider

| File | In commit | Role |
|---|---|---|
| `backend/src/providers/dto/__init__.py` | M | DTOs (FighterRecord, etc.) |
| `backend/src/providers/espn/client.py` | M | Rate limiter (token bucket), breaker, cache, dedup, retries |
| `backend/src/providers/espn/config.py` | M | Endpoints, slugs, limits, env config |
| `backend/src/providers/espn/provider.py` | M | Discovery, resolution, eventlog hooks |
| `backend/src/providers/espn/jobs/__init__.py` | M | Job registry |
| `backend/src/providers/espn/jobs/broadcast.py` | M | Broadcast job |
| `backend/src/providers/espn/jobs/fighter.py` | M | Fighter + records job (checkpoint) |
| `backend/src/providers/espn/jobs/historical_event.py` | A | Historical events job (winningFight chain) |
| `backend/src/providers/espn/jobs/ranking.py` | M | Rankings job |
| `backend/src/providers/espn/jobs/statistics.py` | M | Career statistics job |
| `backend/src/providers/espn/parsers/competition.py` | M | Competition parser |
| `backend/src/providers/espn/parsers/eventlog.py` | A | Eventlog parser (pagination) |
| `backend/src/providers/espn/parsers/fighter.py` | M | Fighter parser (is_active guard) |
| `backend/src/providers/espn/parsers/promotion.py` | M | Promotion parser |
| `backend/src/providers/espn/parsers/ranking.py` | M | Ranking parser (winningFight refs) |
| `backend/src/providers/registry.py` | M | Provider registry |

## 7. Sync engine

| File | In commit | Role |
|---|---|---|
| `backend/src/sync/dependency.py` | M | Sync dependency wiring |
| `backend/src/sync/engine.py` | M | Sync engine (per-job commits, batches) |
| `backend/src/sync/plan.py` | M | Plan building |
| `backend/src/sync/types.py` | M | Sync types |
| `backend/src/sync/upsert.py` | M | Upsert orchestration |
| `backend/src/sync/upserts/base.py` | M | Base upsert (idempotency) |
| `backend/src/sync/upserts/broadcast.py` | M | Broadcast upsert |
| `backend/src/sync/upserts/competition.py` | M | Competition upsert |
| `backend/src/sync/upserts/event.py` | M | Event upsert |
| `backend/src/sync/upserts/fighter.py` | M | Fighter + records upsert (None-skip) |
| `backend/src/sync/upserts/id_resolver.py` | M | ESPN ID = provider identity |
| `backend/src/sync/upserts/ranking.py` | M | Ranking upsert |
| `backend/src/sync/upserts/statistics.py` | M | Career statistics upsert |
| `backend/src/scheduler/locks.py` | M | Scheduler locks |
| `backend/sync.py` | M | CLI entry point |

## 8. Tests

| File | In commit | Coverage |
|---|---|---|
| `backend/tests/unit/test_espn_discovery.py` | A | Discovery |
| `backend/tests/unit/test_espn_pagination.py` | A | Pagination |
| `backend/tests/unit/test_upserts.py` | A | Upserts |
| `backend/tests/integration/test_espn_live_probes.py` | A | Live probes (env-gated) |
| `backend/tests/integration/test_espn_records_and_stats.py` | A | Records + stats + migration 006 |
| `backend/tests/integration/test_sync_live.py` | A | Dual-run live sync (env-gated) |
| `backend/tests/integration/test_sync_engine_records.py` | A | Records via engine |
| `backend/tests/contract/test_pagination_shape.py` | A | Pagination contract |
| `backend/tests/api/test_compare.py` | A | Compare API |
| `backend/tests/api/test_favorites.py` | A | Favorites API |
| `backend/tests/api/test_next_fight.py` | A | Next-fight API |
| `backend/tests/api/test_preferences.py` | A | Preferences API |
| `backend/tests/api/test_scheduler_status.py` | A | Scheduler status API |
| `backend/tests/api/test_uuid_guards.py` | A | UUID guards |
| `backend/tests/api/test_weight_classes.py` | A | Weight classes API |
| `backend/tests/api/test_event_extras.py` | M | Event extras API |
| `backend/tests/api/test_rankings_extras.py` | M | Rankings extras API |
| `backend/tests/integration/test_parsers.py` | M | Parsers |
| `backend/tests/scheduler/test_all.py` | M | Scheduler |

**Suite totals (reported):** 455 passed / 2 skipped at validation close; 457 `test_` defs in the current tree (consistent).

## 9. Acceptance evidence package (this directory — NOT in commit, created 2026-08-10)

| File | Role |
|---|---|
| `README.md` | Package overview + boundary rules |
| `ACCEPTANCE_EVIDENCE.md` | Full acceptance record |
| `VALIDATION_RESULTS.json` | Machine-readable results |
| `VALIDATION_FILE_MAP.md` | This file |
| `VALIDATION_TIMELINE.md` | Chronological reconstruction |
| `CHECKSUM_MANIFEST.json` | SHA-256 integrity manifest (no self-hash) |
| `VERIFICATION.md` | Independent re-verification guide |

## 10. Frozen research workspace (external, read-only)

Entry point: `C:\Users\-\Desktop\zip for xhatgpt\espn endpoint checks\research\espn_endpoint_discovery\`
Key files: `START_HERE.md`, `FINAL_RESEARCH_STATUS.md`, `RESEARCH_MANIFEST.json`, `FINAL_NUMBERS.md`,
`MASTER_REPORT.md`, `KNOWN_LIMITATIONS.md`, `DO_NOT_REDO.md`, `FROZEN.md`, `PRODUCTION_SURFACE_MATRIX.json`,
`RECONCILIATION.json`, `PERFORMANCE_BENCH_FINAL.json`, `live_probes_final.json`, `FINAL_ENDPOINT_CATALOG.json`,
`ENDPOINT_COMPLETENESS.json`, `DISCOVERY_SOURCES_FINAL.json`, `ERRORS_FINAL.json`.
**Frozen state:** untouched — this package only reads.
