# ESPN Production Integration — Architecture & Implementation Plan

> Frozen research: `C:\Users\-\Desktop\zip for xhatgpt\espn endpoint checks\research\espn_endpoint_discovery\` (2026-08-09)
> Production: this repo, `backend/` — provider-first architecture, preserved as-is.
> Status: **PLAN** (implementation phases below). Research workspace is FROZEN — never modified.

---

## 1. Baseline Facts (frozen research — do not silently change)

| Fact | Value | Evidence |
|---|---|---|
| Flat athlete listing | ~38,006 IDs | FINAL_NUMBERS.md |
| Defensible union census | 38,014 IDs (38,006 verified, 8 hard-400 legacy) | FINAL_NUMBERS.md |
| Census classification | 2,763 confirmed MMA · 33,352 MMA-likely · 1,845 uncertain · 45 combat-other · 8 invalid · 1 stub | FINAL_NUMBERS.md |
| Promotions/leagues | 49 (48 enumerated + CES verified separately) | MASTER_REPORT.md |
| "other" league | ~27,286 IDs, compositionally unresolved | FINAL_NUMBERS.md |
| UFC roster | ~1,840 (drifts from historical 1,831) | MASTER_REPORT.md |
| Endpoint families | 96 total: 75 confirmed, 15 failed, 4 content-dependent, 1 current-only, 1 observed/unverified | FINAL_NUMBERS.md |
| P0 production surfaces | 10 (see §3) | MASTER_REPORT.md |
| Historical events | `/leagues/{slug}/events` is **upcoming-only** (count=1). History via **rankings → winningFight → events/{id}** + athlete eventlogs + season types | ENDPOINT_GUIDE.md |
| winningFight hooks | 47 cached; every rank entry carries a winningFight $ref (→ competition ref, legacy 400/600-series event ids) | FINAL_ENDPOINT_CATALOG.json |
| Eventlog | `athletes/{id}/eventlog` CONFIRMED P0, CONTENT_DEPENDENT (~36k refs) | ENDPOINT_GUIDE.md |
| Pagination | **page-based**, 1-indexed; offset ignored; limit capped ~1000; default ~25 | probe-proven |
| ONE Championship slug | **`ofc`** (not `one-championship`) | FROZEN.md |
| Dead surfaces | core v3 MMA athlete (404), site v1 (403), sport dictionaries (404), teams (vestigial) | MASTER_REPORT.md |
| Rate envelope | 4–8 workers · 2–5 req/sec sustained · keep-alive · bounded concurrency · backoff · retry 429/500/502/503/504 + DNS; **no retry on 400/404** | PERFORMANCE_FINAL_REPORT.md |
| Hidden profiles | DJ 2512089, Rousey 2563796, Gracie 2335697, Shamrock 2335653, Ngannou 3933168 — reachable via refs, not flat listing | HIDDEN_SURFACES_REPORT.md |

---

## 2. Production Status (code is truth — reconciled verbatim)

### Existing architecture (preserved)
`ESPN/TSDB/Octagon → providers → sync engine (plans → pipeline → jobs → upserts) → DB → services → API → mobile`

- **Client** (`providers/espn/client.py`): httpx.AsyncClient, keep-alive (10/20 conns), token-bucket rate limiter (10 rps / burst 15), circuit breaker (5 fails / 60s), retry 3× backoff 2.0 on (429,500,502,503,504) + network errors, honors Retry-After, **page-based `paginate()`** with dedup + progress guards + `ESPN_MAX_PAGES` cap. **No response cache, no request dedup, no in-flight dedup.**
- **Provider** (`providers/espn/provider.py`): `fetch_fighters/events` default `league_slug="ufc"`; `fetch_fighter_records()` + `parse_fighter_records()` exist but **no job calls them**; `fetch_fighter_statistics()` exists but stats job `_fetch` returns `[]`; `athlete_eventlog` endpoint defined in config but **no consumer**; `competitor_statistics` defined but unused; `one-championship` slug wrong.
- **Sync engine** (`sync/engine.py` → `pipeline.py` → `job.py`): 9 jobs keyed by `EntityType`; plans (`FullSyncPlan` 9 entities, RankingsPlan, EventsPlan, FighterPlan, FoundationPlan); per-job commits + `sync_runs`/`sync_jobs`; `SyncState` checkpoint/resume (page/offset/cursor/checkpoint dict); Memory state store in CLI.
- **Upserts** (`sync/upserts/`): `BaseUpsert` (FIELD_MAP, race-safe, bulk resolve, `_enrich_model` FK resolution, lazy weight-class creation); `FighterUpsert` (records fields mapped, **is_active NOT in FIELD_MAP**); `CompetitionUpsert` (nested competitors); `RankingUpsert` (atomic replace); `StatisticsUpsert` (competitor-scoped only — **career stats skipped**); `BroadcastUpsert` (composite key).
- **DB models**: `fighters` (has is_active, record_* columns), `fighter_records` (rich breakdown, FK unique fighter_id — **table exists, never written by sync**), `statistics` (competitor_id + fighter_id NOT NULL), `events`, `competitions`, `competitors`, `rankings`, `promotions`, `venues`, `weight_classes`.
- **Repository**: `FighterRepository.upsert_record()` exists (PG `on_conflict`) — unused by sync path.

### Gap list (from reconciliation)
| # | Gap | Evidence |
|---|---|---|
| C1 | No historical events ingested (league events are upcoming-only) | live run: 1 event/33 comps |
| C2 | Fighter records never fetched → 0-0-0-0 persists | `parse_fighter()` hardcodes zeros |
| C3 | Eventlog defined, unconsumed | config.py |
| C4 | Statistics job returns `[]`; career stats skipped by upsert | jobs/statistics.py, upserts/statistics.py |
| C5 | Discovery UFC-centric; 95% of census unreachable | `fetch_fighters` default ufc |
| C6 | `is_active` not persisted by `FighterUpsert` (not in FIELD_MAP) | upserts/fighter.py |
| C7 | Rate config 10 rps / burst 15 exceeds measured safe envelope | config.py |
| C8 | Stale docs: `one-championship`, offset pagination claims, 48-league, stats-synced claims | config.py, ESPN_ENDPOINT_CATALOG.md |

---

## 3. P0 Surface Mapping (research → production)

### 1. Global athlete listing — `core.v2/athletes`
- Production: **MISSING** (no global listing endpoint in ENDPOINTS).
- Change: add `global_athletes` endpoint + `fetch_athlete_ids()` enumerator (list only, no profile resolution).

### 2. League rosters — `core.v2/leagues/{league}/athletes`
- Production: present (`ENDPOINTS["athletes"]`) but only ever used with `ufc`.
- Change: iterate all configured league slugs; union + dedup by ID.

### 3. Athlete profile — `core.v2/athletes/{id}`
- Production: present (`fetch_fighter`, `parse_fighter`) ✓ — used by fighter job.
- Change: feed it from the discovery ID union; bounded concurrency.

### 4. Athlete eventlog — `core.v2/athletes/{id}/eventlog`
- Production: endpoint defined, **unused**.
- Change: `fetch_fighter_eventlog()` + parser → event IDs; config-gated ingestion.

### 5. Events detail — `core.v2/leagues/{league}/events/{id}`
- Production: `fetch_event()` present, used for embedded competitions ✓.
- Change: drive from winningFight refs for historical events.

### 6. Competitions — embedded in event
- Production: `fetch_competitions()` present ✓ (embedded, status for FINAL).
- Change: reuse for historical events.

### 7. Competitors — embedded
- Production: `CompetitionUpsert` handles nested competitors ✓.
- Change: none.

### 8. Status — `competitions/{id}/status`
- Production: `parse_competition_status` + fetch for FINAL ✓.
- Change: none.

### 9. Rankings — `leagues/{league}/rankings`
- Production: present ✓.
- Change: parser must also **capture `winningFight` refs** (currently dropped).

### 10. Search
- Production: present (API). Change: none.

## P1 Classification
| Surface | Class | Rationale |
|---|---|---|
| `athletes/{id}/ranks` | DEFER | Content-dependent, ranked athletes only |
| `athletes/{id}/statistics` | IMPLEMENT (career) | P0-adjacent; mobile profile needs it |
| `competitors/{id}/statistics` | IMPLEMENT (bounded, content-dependent) | Per-fight stats where ESPN provides |
| season/types traversal | DEFER | Breadth expansion after core chain |
| `linescores` | DEFER | Non-essential for MMA product |
| `odds` | NOT APPLICABLE | Product excludes betting/odds |
| teams surface | NOT APPLICABLE | Vestigial for MMA |
| v3 MMA / site v1 / sport dictionaries | UNSUPPORTED | Verified dead (404/403) |
| the other 96-10 endpoint families | DEFER | No product value without MMA app requirement |

---

## 4. Target Discovery Architecture

```
global flat listing (/athletes)
        + 49 league rosters (/leagues/{slug}/athletes)
        + rankings athlete refs
        + historical refs (winningFight, eventlog, event/competition refs)
        ── dedup by ESPN athlete ID ──► candidate ID set
        ── bounded-concurrency resolution (4–8 workers, 2–5 rps) ──► profiles
        ── records per fighter ──► FighterRecord table
```

- **Resumable**: checkpoint the enumerated ID set + last processed ID in `SyncState.checkpoint` (e.g. `{"athlete_ids": [...], "processed": 37_500}`).
- **Idempotent**: `FighterUpsert` by `(provider, external_id)`; `IdResolver` handles mapping.
- **Cache**: client response cache (URL-canonicalized, TTL) + RefResolver per-run cache (existing).
- **Never guess IDs**: only IDs observed in real responses are used.
- **Distinguish outcomes**: success / permanent failure (400/404 — recorded, no retry) / transient failure (retry, checkpoint preserved) / pending (not yet attempted).

## 5. Historical Event Architecture

```
rankings → ranks[].winningFight $ref (competition ref)
        → extract event_id + competition_id
        → fetch /events/{event_id} (embedded competitions)
        → competitions → competitors → athletes
  + athlete eventlogs (event $refs) — config-gated breadth
```
- New job `ESPN_HistoricalEventSyncJob` (EntityType.HISTORICAL_EVENT, bounded by `ESPN_MAX_HISTORICAL_EVENTS`, default on in plan, gated by env for live).
- Reuses `EventUpsert` + `CompetitionUpsert` (competitors nested). Idempotent — no duplicates.
- Historical events never overwrite upcoming data: upsert merges only present fields; status updates only when the provider says so.

## 6. Fighter Records

- Wire `/athletes/{id}/records` into `ESPN_FighterSyncJob`: after profile fetch, resolve records per fighter (bounded concurrency), attach to `FighterDTO`.
- Persist via new `FighterRecordUpsert` (uses existing `fighter_records` table + `FighterRepository.upsert_record` semantics).
- **Do not reset existing records** when ESPN returns empty/partial: only write when a valid `overall` item parsed; keep DB row otherwise.

## 7. Statistics

- Career: `/athletes/{id}/statistics` → `StatisticDTO` with `competition_external_id=""`; **upsert must persist career stats** — `statistics.competitor_id` becomes nullable (migration 006), career rows keyed by `fighter_id` only.
- Per-fight: `competitors/{id}/statistics` fetched during historical/competition sync where ESPN provides it (content-dependent, bounded).
- Never fabricate: absent stats → no rows.

## 8. Cache / Request Efficiency (client)

- URL canonicalization (sorted params) → cache key.
- In-flight dedup: concurrent identical requests share one HTTP call.
- Response cache: TTL (default 300s), size-bounded.
- Keep-alive already present (10/20). Bounded concurrency: semaphore 4–8.
- Metrics: requests, cache hits/misses, deduped, retries, 429s, 5xx, DNS errors, 400/404, latency, throughput — via existing `SyncMetrics` + client counters.

## 9. Rate Configuration

- `rate_limit_per_second`: 10.0 → **3.0** (inside 2–5 envelope).
- `burst_size`: 15 → **6**.
- `max_concurrency`: new, default **6**.
- `retry`: keep 3× backoff 2.0 on (429, 500, 502, 503, 504) + network; **never retry 400/404** (already correct — 4xx non-429 not retried).

## 10. Docs Reconciliation

- `one-championship` → `ofc` in `ESPN_LEAGUE_SLUGS`.
- `ESPN_ENDPOINT_CATALOG.md`: offset → page pagination; 48 → 49 leagues; correct records/statistics claims (was "resolved during sync" / "stats synced" — now actually true after Phases 3/6).
- Config comments: rate envelope, discovery modes.

---

## 11. Implementation Order (per Part 15)

| Phase | Work | Files |
|---|---|---|
| 1 | Athlete discovery + cache | config.py, client.py, provider.py, reference.py |
| 2 | Active/inactive persistence | dto/__init__.py, parsers/fighter.py, upserts/fighter.py |
| 3 | Fighter records | provider.py, dto, jobs/fighter.py, new FighterRecordUpsert, jobs registry |
| 4 | Historical events | parsers/ranking.py (winningFight), new historical job, plan.py, types.py, sync.py |
| 5 | Eventlog | provider.py, new parser, config gate |
| 6 | Statistics | migration 006, upserts/statistics.py, jobs/statistics.py, provider.py |
| 7 | Perf/cache/retry | client.py (dedup+cache+concurrency), config.py |
| 8 | Tests | tests/unit, tests/integration |
| 9 | Docs | ESPN_ENDPOINT_CATALOG.md, config comments |
| 10 | Full validation + report | pytest/ruff/mypy, ESPN_INTEGRATION_REPORT.md |

Safety: no provider/engine/upsert deletions; no new framework; mobile untouched; research workspace untouched; no git commits.
