# Gap Analysis — V10 (current) vs Reference (`from-github (1)`)

Method: full file-tree diff (820 vs 775 files, exclusions), MD5 content diff of all
shared paths (185 differing), git lineage check, and live re-verification of every
audit blocker claim against actual V10 code.

## 1. Lineage (verified)

- **V10** = git repo, single commit `9e666a1 Initial upload`, **283 modified
  files uncommitted** (the previous OpenCode session's work: cache/ETag/003/tests).
- **Reference** = extracted zip, NOT a git repo; file tree ≈ V10's HEAD baseline
  (pre-OpenCode), NOT identical to HEAD in content (4/4 sampled files differ).

**Conclusion:** reference is an *earlier snapshot of the same monorepo*, not a
different architecture. V10 ⊇ reference at file level.

## 2. File-level differences

### Missing in V10 (1 file — restore candidate)
| Path | Note |
|---|---|
| `backend/tests/integration/test_cache.py` | Reference has it; V10 does NOT. V10 instead has `tests/unit/test_cache.py` + `tests/unit/test_api_cache.py` (new). **Restore only after content comparison** — the unit tests may supersede it. |

### Present only in V10 (OpenCode additions — keep)
- `backend/alembic/versions/003_phase8_performance.py` (13 indexes)
- `backend/src/api/cache.py`, `etag.py`, `middleware/redis.py`,
  `sync/cache_invalidation.py`, `src/__init__.py`
- `backend/src/domain/models/*` (11 re-export shims)
- `backend/tests/unit/test_api_cache.py`, `test_cache.py`, `test_etag.py`,
  `test_health.py`, `test_observability.py`, `test_sync_cache_invalidation.py`
- `deliverables-2026-08-02/`, `deliverables-2026-08-03/`, `session-ses_0387.md`

### No renames/moves/deletes detected at tree level
Mobile trees are **byte-identical** between V10 and reference (no route files in
either — both are the broken v1-era baseline).

## 3. Content differences (185 shared files)

All within `backend/src`, `backend/tests`, `backend/docs`, `backend/PROJECT_STATUS.md`,
`backend/pyproject.toml`, `recommendation/` — i.e., the previous session's edit set.
Direction: V10 is AHEAD (fixes + features). No content regressions found vs reference
beyond what the OpenCode audit already documented (sync.py still broken, etc.).

## 4. Blocker re-verification (audit claims vs ACTUAL V10 code)

| # | Claim (audits) | Verified in V10 | Status |
|---|---|---|---|
| 1 | `sync.py` wrong API (`SyncPlan(entity_types=...)` etc.) | sync.py:151,154,189,212 — real `SyncPlan()` is no-arg (plan.py:63); `SyncEngine(jobs=…)` (engine.py:55); `SyncContext` is dataclass w/ `db: AsyncSession` (context.py:102); `pipeline.execute(ctx, state, …)` (pipeline.py:63) | 🔴 **BROKEN** |
| 2 | Auth tables have no migration | 001 creates 14 tables (no users); 002 adds 4 support tables; 003 = indexes only. Zero `users`/`user_sessions`/… anywhere in migrations | 🔴 **BROKEN** |
| 3 | `first_event_date` String(20) vs DATE | core.py:32 `String(20)` vs 001:31 `sa.Date()` | 🔴 **DRIFT** |
| 4 | `time_utc` String(10) vs TIME | event.py:33 `String(10)` vs 001:141 `sa.Time()` | 🔴 **DRIFT** |
| 5 | 002 re-adds `synced_at` to rankings (001 already has it, 001:219) | 002:147–150 loop includes `"rankings"` → generated SQL has `ALTER TABLE rankings ADD COLUMN synced_at` — **fresh DB = DuplicateColumnError** | 🔴 **CONFLICT** |
| 6 | Rankings `source_provider` missing → 500 | 002 loop DOES add it to rankings now (audit stale on the fix), but blocked by #5 | 🟡 **BLOCKED BY #5** |
| 7 | Scheduler commented out | main.py:38–41 `# manager = SyncManager(context)` / "deferred to production runtime" | 🔴 **BROKEN** |
| 8 | PromotionUpsert sets `is_active` | promotion.py:27–34 does NOT pass is_active | ✅ **FIXED** (audit stale) |
| 9 | Tests 212/30/17 | **300 passed, 0 failed** (fresh run) | ✅ **FIXED** |
| 10 | `src.domain` missing | 11 shims present; imports resolve (compile OK) | ✅ **FIXED** |
| 11 | Health endpoints broken | `/health`, `/health/database`, `/health/ready` OK (200) | ✅ **FIXED** |
| 12 | Cache/ETag real | cache.py/etag.py present; 304 + Cache-Control verified previously | ✅ **REAL** |
| 13 | Mobile unroutable, 444 tsc errors, expo-asset missing, assets missing | mobile = v1 baseline; no route files; 6 JSX-in-.ts files; no assets dir | 🔴 **BROKEN** |
| 14 | AI modules present + Predict tab | prediction/, recommendation/, intelligence/, platform/ exist; MainNavigator wires Predict | 🔴 **PRESENT** |
| 15 | Champions endpoint missing | No `/champions` route in other.py (only rankings list/mens/womens/p4p/{division}) | 🟡 **MISSING** |
| 16 | `src/domain` shims vs `tests/integration/test_cache.py` | V10 has unit tests; ref has integration test | 🟡 **SEE §2** |

## 5. What is NOT broken (verified)

compileall clean · app import clean · 300 tests green · ruff clean (previous run) ·
ETag/cache-aside/003 migration exist · domain shims resolve · health endpoints OK ·
reference `test_cache.py` is the only missing file.

## 6. Result for the plan

The "migration" is NOT a restore-from-reference exercise (V10 already ⊇ reference).
It is a **fix-the-data-path exercise** on V10 itself, plus policy removals (AI) and
mobile baseline repair:
1. Schema: resolve 001↔002 conflict + fix type drifts (first_event_date, time_utc) + auth tables migration.
2. Sync: rewrite sync.py to the real engine API; wire scheduler in lifespan.
3. Endpoints: add champions (data already synced).
4. Mobile: restore bootability (routes, assets, deps, .tsx renames, shell components).
5. Policy: delete AI/betting modules + tabs + recommendations router.
6. Tests: add migration-coverage + champions tests; keep 300 green.
7. Docs: honest status.
