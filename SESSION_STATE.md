# SESSION_STATE.md — Session Journal

> Per-session state per the milestone protocol. Read this + `PROJECT_STATE.md` +
> `EXECUTION_PLAN.md` completely before touching anything. Zero-memory-friendly.
> **Current session started:** 2026-08-05 — milestone implementation (T01–T05).
> **T01–T18 COMPLETED** — sync + degradation + real favorites/preferences/notifications + pagination contract + UUID guards + weight-classes + next-fight + compare routes + mobile env/base-URL hardening + mobile TS model audit (snake_case contract) + full gates. Milestone DONE; docs updated; commit pending user request.

---

## 1. Session Objective

Implement the approved milestone **"Make the Data Flow + Contract Integrity"** in order:
T01–T05 (sync write path + live-Postgres acceptance test = milestone gate) → T06–T07
(graceful degradation) → T08–T10 (real favorites/preferences) → T11–T15 (contract) →
T16–T17 (mobile) → T18 (close). Each task verified before the next.

## 2. Work Completed

1. **T01–T04 Completed** (details preserved in PLAN_HISTORY.md freeze entry): BaseUpsert
   `_prepare_new` NOT NULL provider/external_id; pagination guards; `_enrich_model` FK
   resolution; engine per-job commits + sync_runs/sync_jobs.
2. **Live DB provisioned:** role `mma`/`mma` + db `mma` on `postgresql-x64-18` (superuser
   `postgres:REDACTED` user-supplied); alembic 001→005 → 27 tables.
3. **4 live-run bugs fixed:** promotion external_id → slug `"ufc"`; ranking job iterates
   promotions; broadcast job fetches events first; `BroadcastUpsert` sets NOT NULL `provider`.
4. **Pagination investigation (conclusive, probe-proven):** ESPN v2 core API list endpoints
   (athletes/leagues/events/rankings) **ignore `offset`**, honor **`limit`+`page`**
   (1-indexed; `pageIndex` echoes requested page; athletes pool = 1829, limit max 1000,
   default 25).
5. **T05 fix implemented:** `paginate()` switched to `page`-based iteration (advance by 1,
   stop at `pageIndex >= pageCount`; all T02 guards kept; `ESPN_MAX_PAGES` env override);
   `fetch_fighters`/`fetch_events` map `offset → offset//limit+1`; pagination tests rewritten
   to the proven contract (7 tests).
6. **5th live-run bug fixed:** `RankingUpsert` missing NOT NULL `provider` → session-poisoning
   flush error; fixed `provider=self.provider`. Also fixed mypy regression in
   `BroadcastUpsert._event_uuid_map` typing.
7. **T05 acceptance PASSED:** `MMA_LIVE_SYNC=1` `ESPN_MAX_PAGES=25` — 9/9 jobs COMPLETED,
   0 errors: promotions 48, fighters **1829** (full pool), events 1, competitions 33,
   broadcasts 1, rankings 118 inserted (110 rows), sync_runs 1.
8. **T06 Completed:** `scheduler_status()` wraps `manager.get_status()` → HTTPException 503
   ("Redis unreachable or scheduler not healthy"); `tests/api/test_scheduler_status.py` (3 tests).
9. **T07 Completed:** `RedisLock` degrades when Redis unreachable — `acquire()` → True,
   `release()`/`extend()`/`is_locked()` → False on `RedisError`/`OSError` (never raise);
   `FailingRedis` helper + 2 tests in `tests/scheduler/test_all.py`.
10. **T08 Completed:** favorites real DB-backed — GET reads `favorite_fighters`/
    `favorite_events` (ordered); POST idempotent; DELETE removes; non-UUID → 404; promotion →
    explicit 501; `tests/api/test_favorites.py` (5 tests).
11. **T09 Completed:** preferences DB-backed via `UserPreference` — GET returns defaults when
    no row; PATCH upserts with `exclude_unset` merge; response built before commit (avoided
    `MissingGreenlet`); `tests/api/test_preferences.py` (4 tests).
12. **T10 Completed:** duplicate `notif_router` (users.py) deleted — stubs held no distinct
    endpoints; real `notifications.py` (8 routes) now reachable. **Fixed two shadowing bugs:**
    stub was registered first so GET `/v1/notifications` returned `[]` and PATCH `/read-all`
    was a silent no-op. Mobile consumption (`/{id}/read`, `/read-all`, `?limit=50`) verified
    against real routes.
13. **T11 Completed:** pagination contract decided (keep backend `{items,total,page,limit,pages}`
    per PROJECT_STATE §12.3) — mobile `PaginatedResponse` fixed, `extractItems` helper added,
    7 consumer sites updated (fighters/events repos, usePastEvents, home queries + inline
    HomeScreen feed, FightersScreen inline list — these rendered `[]` or the raw envelope
    before); new contract test pins the envelope shape (7 tests).
14. **T12 Completed:** shared `require_uuid()` (404) guards on all 18 UUID-typed `{id}` routes
    (watchlist ×4, fighters ×5, events ×4, fights, notifications ×2, venues ×2); fake-id test
    fixtures updated to real UUIDs; `tests/api/test_uuid_guards.py` (15 tests).
15. **T13 Completed:** investigation found `weight_classes` **empty in live DB** (0 rows, all
    1829 fighters `weight_class_id` NULL) — the sync job fetches `[]` (inline data), nothing
    wrote rows, data silently dropped. Fix: parsers capture inline `weightClass.text`
    (fighter/competition), DTOs gain `weight_class_name`, shared
    `BaseUpsert._ensure_weight_class()` lazily creates the row on first use (resolver +
    name-cache, deduped across jobs) and links the FK; `wc_router` in `other.py` (list + detail,
    `require_uuid` guard); schemas in `misc.py`. Tests: 5 route tests + 3 lazy-creation unit
    tests. **Live sync re-run: 1831 fighters inserted, 0 errors → 14 weight classes created,
    1828 fighters linked (no backfill needed).** Live route check: 14 divisions, per-division
    counts correct, detail resolves. Full gates: pytest **404 passed, 1 skipped**, ruff + mypy
    clean.
16. **T14 Completed:** `GET /v1/fighters/{id}/next-fight` (FTR-107, `NextFight | null` per
    flutter-audit) — `FighterRepository.get_next_fight` (single joined query; earliest bout on
    a non-FINAL/non-CANCELLED event, date asc nulls-last, card order; past-dated SCHEDULED
    events excluded); `NextFightResponse` schema; route with `require_uuid` + 404 for unknown
    fighter + 15-min TTL; service passthrough. Live smoke found `CompetitionUpsert` dropping
    `weight_class_name` (FK resolved since T13, display name NULL) → mapped + FIELD_MAP. 7
    tests (`tests/api/test_next_fight.py`). Live re-sync + smoke: fighters on the SCHEDULED
    UFC FN card return opponent/corner/weight-class, no-competition fighter → `null`. Gates:
    pytest **411 passed, 1 skipped**, ruff + mypy clean.
17. **T15 Completed (decision: add endpoint, keep deeplink):** investigation showed mobile has
    no compare screen (`fighters/compare` resolves nowhere; store holds only ids) — the
    missing contract piece is the route. `GET /v1/compare?a=&b=` (`api/v1/compare.py`):
    summaries (`FighterListItem`) + head-to-head (most recent first, per-side outcomes,
    method/round/title) + common opponents (chronological per-side outcomes, one-sided
    excluded) per data-spec "compare payload incl. common opponents"; `require_uuid` 404s,
    unknown fighter 404, `a == b` 422, 1-h TTL. `FighterRepository.get_compare`: 5 indexed
    queries, no N+1. 8 tests. Live smoke: Canuto vs Foro → real h2h bout on the Gamrot card;
    no shared opponents in live DB → empty. Gates: pytest **419 passed, 1 skipped**, ruff +
    mypy clean, mobile tsc 0.
18. **T16 Completed:** no real prod deploy target exists → `EXPO_PUBLIC_API_URL` made
    **mandatory in non-dev builds** (fail-fast error; dev fallback `localhost:8000/api`
    kept). New single source `mobile/config/env.ts` (`API_BASE_URL` + derived `WS_BASE_URL`);
    `services/api.ts`, `BootstrapConfig.ts` (`api.mma-app.com` fake removed),
    `LiveFightSocket.ts` (`wss://api.mma-platform.com/ws` fake removed) all consume it;
    `mobile/.env.example` created. Verified: tsc 0; prod web export w/o env inlines the
    "required" throw (fail-fast proven); w/ env the real URL inlines and no API fakes remain
    in the bundle. Gates: backend pytest 419 + 1 skip (unchanged), ruff/mypy clean, mobile
    tsc 0, expo export OK.
19. **T17 Completed (mobile TS model audit, flutter-audit D1):** every mobile type/model
    layer re-derived from the actual backend schemas, feature by feature:
    - **Fighters:** `types.ts` rewritten snake_case (`FighterProfile`, `FighterListItem`,
      `FighterStatsResponse`, `FighterRecord`, `FightHistoryEntry`, `SimilarFighter`,
      `NextFight`; `FighterFightEntry` alias fixed); refactored `repository/index.ts` +
      `hooks/index.ts` (`useInfiniteQuery<Fighter[]>`); legacy `api/queries.ts` rewritten
      against `fighterEndpoints` + contract types (kept as exported entry via
      `features/index.ts`); components/screens/charts re-keyed (`full_name`,
      `record.record_summary`, `finish_rate`, `sig_strikes_landed_per_min`, `headshot_url`);
      deleted dead `screens/FightersScreen.tsx` + `types/index.ts`.
    - **Home:** `recommendedFighters` → `RecommendationItem[]`; HomeScreen re-keyed
      (`venue_name`, `fight_count`, null-safe date); unused imports dropped.
    - **Events:** types rewritten (`EventListItem`, `Broadcast`, `FightCardEntry`,
      `EventDetail`, `FighterCorner`, `FightDetail`, `EventStatistics`); repo/hooks re-typed
      (`useEvent` = `EventWithExtras` + LIVE/IN_PROGRESS polling); `utils/eventStatus`
      status-based (`LIVE`/`IN_PROGRESS`/`SCHEDULED`/`COMPLETED`/`FINAL`); `fightSorter`
      segment-key normalization + `is_main_event`; components/screens/detail re-keyed
      (`venue_name`, `banner_url`, `broadcasts[].network`, `fighter_a_name`, `winner ===
      fighter_a_id`); stories mock updated.
    - **Rankings:** types rewritten (`RankingEntry`, `RankingCategory`, `RankingsResponse`,
      `FighterBrief`, `ChampionEntry`, `RankingMovementEntry`, `GOATEntry`, `ProspectEntry`,
      `StreakEntry`, `TitleDefenseEntry`); `useP4P`/`useDivisionRankings` → `RankingCategory`
      (p4p returns a single category); RankingCard/MovementArrow/ChampionCard re-keyed;
      phantom `sortByELO` (`fighter.eloRating` doesn't exist) removed.
    - **Search:** `SearchModule.tsx` runtime bugs fixed — rows read `item.name`/
      `item.relevance`/`item.image_url` (were `title`/`score` → undefined); repo unwraps
      `data.suggestions`/`data.trending`/`data.popular`/`data.history`.
    - **Watchlist:** `WatchlistEvent` → `{id,title,subtitle,date}` (was `name`/`venue`/
      `fightCount` → undefined); favorites repo maps snake_case `FighterProfile`
      (`full_name`, `record.record_summary`, `weight_class`).
    - **Profile:** `UserProfile`/`UserPrefs`/`UserSession` re-derived from
      `ProfileResponse`/`PreferencesResponse`/`SessionResponse` (display_name, avatar_url,
      device/browser/ip_address, country, notify_* prefs; was camelCase + nonexistent
      `os`/`location`).
    - **Notifications:** `NotificationItem` → `{id,category,title,message,read,createdAt,
      deepLink,actionable}` (was `type` → `undefined.replace()` crash); badge count
      `(data?.data ?? data ?? []).length` (was `data.total ?? data.count`).
    - Auth service verified already aligned. Verification: `npx tsc --noEmit` **0 errors**.
20. **T18 Completed (milestone close):** full gates green — pytest **419 passed, 1 skipped**
    (env-gated live test), ruff **clean**, mypy **Success (186 files)**, mobile tsc **0
    errors**, `npx expo export --platform web` **bundled OK** (1396 modules). Docs updated:
    EXECUTION_PLAN (T17/T18 statuses + archive), SESSION_STATE, PROJECT_STATE. **Milestone
    "Make the Data Flow + Contract Integrity" COMPLETE (T01–T18).** Commit pending — only on
    user request (HEAD `d3ecc68`).

## 3. Files Modified (by task)

| Task | File | Change |
|---|---|---|
| T01 | `backend/src/sync/upserts/base.py` | `_prepare_new` fills NOT NULL provider/external_id; race-retry cache fix |
| T01 | `backend/tests/unit/test_upserts.py` | 11 tests |
| T02 | `backend/src/providers/espn/client.py` | paginate() → `page`-based (limit+page; stop at pageCount); `_pagination_cap()` + `ESPN_MAX_PAGES` |
| T02 | `backend/tests/unit/test_espn_pagination.py` | 7 tests (proven ESPN contract) |
| T03 | `backend/src/sync/upserts/base.py` | `_enrich_model` FK resolution + per-row error isolation |
| T04 | `backend/src/sync/engine.py` | `_record_run_start`/`_record_job`/`_record_run_end`, per-job commits |
| T04 | `backend/tests/integration/test_sync_engine_records.py` | 3 tests (new) |
| T05 | `backend/src/providers/espn/provider.py` | fetch_fighters/fetch_events: `offset → offset//limit+1` mapping |
| T05 | `backend/src/providers/espn/parsers/promotion.py` | external_id = slug |
| T05 | `backend/src/providers/espn/jobs/ranking.py` | iterates promotions for `fetch_rankings(promo)` |
| T05 | `backend/src/providers/espn/jobs/broadcast.py` | fetches events then per-event `fetch_broadcasts(event)` |
| T05 | `backend/src/sync/upserts/broadcast.py` | sets `provider`; instance-level `_event_uuid_map` (str typing) |
| T05 | `backend/src/sync/upserts/ranking.py` | sets `provider=self.provider` (NOT NULL fix) |
| T05 | `backend/tests/integration/test_sync_live.py` | env-gated live acceptance test; `ESPN_MAX_PAGES=25` default |
| T05 | `backend/tests/integration/test_parsers.py` | promotion external_id assertion → `"ufc"` |
| T06 | `backend/src/api/sync.py` | `scheduler_status()` try/except → 503 with explicit message |
| T06 | `backend/tests/api/test_scheduler_status.py` | 3 tests (new) |
| T07 | `backend/src/scheduler/locks.py` | `RedisLock` degrades on `RedisError`/`OSError` (acquire True, others False) |
| T07 | `backend/tests/scheduler/test_all.py` | +2 tests (`FailingRedis`) |
| T08 | `backend/src/api/v1/users.py` | fav_router real DB-backed (GET/POST/DELETE, UUID guard, promo 501) |
| T08 | `backend/tests/api/test_favorites.py` | 5 tests (new) |
| T09 | `backend/src/api/v1/users.py` | pref_router DB-backed via `UserPreference` (GET defaults / PATCH upsert) |
| T09 | `backend/tests/api/test_preferences.py` | 4 tests (new) |
| T10 | `backend/src/api/v1/users.py` | deleted `notif_router` + 3 notification stubs |
| T10 | `backend/src/api/v1/__init__.py` | removed `notif_router` registration |
| T11 | `backend/tests/contract/test_pagination_shape.py` | 7 tests pinning `{items,total,page,limit,pages}` envelope |
| T11 | `mobile/types/index.ts` | `PaginatedResponse` → `{items,total,page,limit,pages}` |
| T11 | `mobile/services/pagination.ts` | new: `extractItems<T>` / `isPage` helpers |
| T11 | `mobile/features/fighters/repository/index.ts` | `list` uses `extractItems` |
| T11 | `mobile/features/events/repository/index.ts` | `list` + `getPast` use `extractItems` |
| T11 | `mobile/features/events/hooks/usePastEvents.ts` | uses `extractItems` |
| T11 | `mobile/features/home/api/queries.ts` | home feed + live + recommended hooks use `extractItems` |
| T11 | `mobile/features/home/screens/HomeScreen.tsx` | inline feed uses `extractItems` |
| T11 | `mobile/features/fighters/screens/FightersScreen.tsx` | inline list uses `extractItems` |
| T12 | `backend/src/api/utils.py` | new: shared `require_uuid()` (404 on non-UUID) |
| T12 | `backend/src/api/v1/{watchlist,fighters,events,fights,notifications,other,users}.py` | `require_uuid` guards on all 18 UUID `{id}` routes |
| T12 | `backend/tests/api/test_uuid_guards.py` | 15 tests (new) |
| T12 | `backend/tests/api/{test_event_extras,test_rankings_extras}.py` | fake ids → valid UUIDs |
| T13 | `backend/src/providers/dto/__init__.py` | `weight_class_name` on FighterDTO + CompetitionDTO |
| T13 | `backend/src/providers/espn/parsers/{fighter,competition}.py` | capture inline `weightClass.text` label |
| T13 | `backend/src/sync/upserts/base.py` | new `_ensure_weight_class()` (lazy row creation, resolver + name cache) |
| T13 | `backend/src/sync/upserts/{fighter,competition}.py` | enrich via `_ensure_weight_class`; Fighter FIELD_MAP + weight_class_name |
| T13 | `backend/src/schemas/misc.py` | `WeightClassListItem` / `WeightClassDetailResponse` |
| T13 | `backend/src/api/v1/other.py` | `wc_router`: list (paginated, ordered by name, fighter_count) + detail (`require_uuid`) |
| T13 | `backend/src/api/v1/__init__.py` | register `wc_router` |
| T13 | `backend/tests/api/test_weight_classes.py` | 5 tests (new; letter-containing UUID ids — sqlite NUMERIC-affinity trap) |
| T13 | `backend/tests/unit/test_upserts.py` | +3 lazy-creation tests |
| T14 | `backend/src/db/repositories/fighter.py` | `get_next_fight` (joined query, semantics documented) |
| T14 | `backend/src/services/fighter_service.py` | `get_next_fight` passthrough |
| T14 | `backend/src/schemas/fighter.py` | `NextFightResponse` |
| T14 | `backend/src/api/v1/fighters.py` | `GET /{fighter_id}/next-fight` (require_uuid, 404, 15-min TTL) |
| T14 | `backend/src/sync/upserts/competition.py` | persist `weight_class_name` (+ FIELD_MAP) |
| T14 | `backend/tests/api/test_next_fight.py` | 7 tests (new) |
| T15 | `backend/src/api/v1/compare.py` | `GET /v1/compare?a=&b=` (new router, registered) |
| T15 | `backend/src/db/repositories/fighter.py` | `get_compare` (h2h + common opponents) |
| T15 | `backend/src/services/fighter_service.py` | `compare_fighters` passthrough |
| T15 | `backend/src/schemas/fighter.py` | `CompareResponse`/`CompareBoutEntry`/`CommonOpponentEntry` |
| T15 | `backend/tests/api/test_compare.py` | 8 tests (new) |
| T16 | `mobile/config/env.ts` | `API_BASE_URL`/`WS_BASE_URL` resolver (new; prod-required env) |
| T16 | `mobile/services/api.ts` | consume `API_BASE_URL`; fake prod URL removed |
| T16 | `mobile/app/bootstrap/BootstrapConfig.ts` | consume `API_BASE_URL`; fake removed |
| T16 | `mobile/features/events/socket/LiveFightSocket.ts` | derive WS base; fake removed |
| T16 | `mobile/.env.example` | new (EXPO_PUBLIC_API_URL, EXPO_PUBLIC_ENV) |
| T17 | `mobile/features/fighters/types.ts` | rewritten snake_case + `FighterFightEntry` alias; deleted `types/index.ts` |
| T17 | `mobile/features/fighters/repository/index.ts` | typed repo layer (extractItems) |
| T17 | `mobile/features/fighters/hooks/index.ts` | `useInfiniteQuery<Fighter[]>` |
| T17 | `mobile/features/fighters/api/queries.ts` | legacy layer rewritten to contract types/endpoints |
| T17 | `mobile/features/fighters/components/index.tsx` | FighterHeader/Record/Stats/FightHistoryRow/SimilarityCard/StyleBadge/RankMovement/FavoriteButton re-keyed |
| T17 | `mobile/features/fighters/screens/index.tsx` | FighterRow/CompCol/compare headline snake_case; deleted `screens/FightersScreen.tsx` |
| T17 | `mobile/features/fighters/charts/index.tsx` | radar dims snake_case |
| T17 | `mobile/features/home/types/index.ts` | dropped unused model imports |
| T17 | `mobile/features/home/api/queries.ts` | `recommendedFighters` → `RecommendationItem[]` |
| T17 | `mobile/features/home/screens/HomeScreen.tsx` | venue_name/fight_count/date guard |
| T17 | `mobile/features/events/types.ts` | rewritten snake_case (`EventListItem`…`EventStatistics`) |
| T17 | `mobile/features/events/repository/index.ts` | re-typed; getLive/getUpcoming raw-list unwrap |
| T17 | `mobile/features/events/hooks/{useEvent,useEvents,usePastEvents}.ts` | re-typed; `EventWithExtras` + LIVE/IN_PROGRESS polling |
| T17 | `mobile/features/events/utils/{eventStatus,fightSorter}.ts` | status-based + segment normalization + `is_main_event` |
| T17 | `mobile/features/events/components/{EventCard,LiveBanner,FightRow}.tsx` | snake_case |
| T17 | `mobile/features/events/screens/{EventDetailScreen,FightCardScreen,LiveEventScreen,ResultsScreen,EventsScreen}.tsx` | snake_case |
| T17 | `mobile/features/events/detail/index.tsx` | banner_url/venue_name/broadcasts network |
| T17 | `mobile/features/events/stories/EventCard.stories.tsx` | mock updated |
| T17 | `mobile/features/rankings/types.ts` | rewritten snake_case (+`FighterBrief`) |
| T17 | `mobile/features/rankings/repository/index.ts` | re-typed; p4p → `RankingCategory` |
| T17 | `mobile/features/rankings/hooks/index.ts` | `useP4P`/`useDivisionRankings` → `RankingCategory`; movement/streaks typed |
| T17 | `mobile/features/rankings/components/index.tsx` | RankingCard/MovementArrow/ChampionCard re-keyed |
| T17 | `mobile/features/rankings/screens/index.tsx` | P4P `data.rankings`, champion banner, GOAT/Prospects/Movement/TitleDefenses snake_case |
| T17 | `mobile/features/rankings/theme/index.tsx` | phantom `sortByELO` removed |
| T17 | `mobile/features/search/SearchModule.tsx` | result rows `name/relevance/image_url`; repo unwraps suggestions/trending/popular/history |
| T17 | `mobile/features/search/screens/SearchScreen.tsx` | `SearchResult extends models.SearchResult` |
| T17 | `mobile/features/watchlist/screens/WatchlistScreen.tsx` | `WatchlistEvent {id,title,subtitle,date}`; favorites map snake_case profile |
| T17 | `mobile/features/profile/ProfileModule.tsx` | UserProfile/UserPrefs/UserSession re-derived from backend schemas |
| T17 | `mobile/features/notifications/screens/NotificationsScreen.tsx` | `category` (was `type`); badge count from `data[]` length |

Temp probes (throwaway, `C:\Users\-\AppData\Local\Temp\opencode\`): pgcheck/pgprobe/pgbrute/
pgsetup/pgadmin_check/probe_ranked*.py/probe_where.py/probe_raw.py/probe_matrix.py/
probe_other.py/probe_coverage.py/wc_probe.py/sqlite_probe.py/wc_live_check.py/
nf_probe.py/nf_live_check.py/compare_live_check.py/compare_h2h_check.py.

## 4. Verification Performed (results)

| Gate | Result |
|---|---|
| alembic upgrade head on live PG | 001→005 applied cleanly, 27 tables |
| ESPN pagination probe matrix | offset ignored everywhere; `page`+`limit` = real contract; athletes pool 1829 |
| Live sync acceptance (T05) | **PASSED** ~4 min: 9/9 jobs, promotions 48, fighters 1829, rankings 110, sync_runs 1 |
| pytest (final) | **419 passed, 1 skipped** (env-gated live test) |
| ruff check src tests | clean |
| mypy src | clean (186 files) |
| mobile tsc --noEmit | 0 errors |
| Live sync re-run (T13) | 9/9 jobs COMPLETED, 1831 fighters, 0 errors → **14 weight classes**, 1828 fighters linked |
| Live `/v1/weight-classes` | list 14 rows w/ per-division counts, detail resolves |
| Live `/v1/fighters/{id}/next-fight` | SCHEDULED card fighters → full bout payload; no-competition fighter → `null` |
| Live `/v1/compare` | Canuto vs Foro → real h2h bout (Gamrot card, per-corner outcomes); no shared opponents → empty |
| mobile tsc + expo export (T16) | tsc 0; prod export w/o env → fail-fast throw inlined; w/ env → real URL, 0 fakes |
| mobile tsc (T17, after all features) | **0 errors** (fighters/home/events/rankings/search/watchlist/profile/notifications) |
| Full gates (T18, milestone close) | pytest **419 passed, 1 skipped**; ruff clean; mypy Success (186 files); tsc 0; expo export web OK (1396 modules) |

## 5. Decisions Made

1. **ESPN pagination contract = `limit`+`page`** (evidence over assumption — probe matrix in
   PLAN_HISTORY.md); `offset` retained in provider signatures only as
   `offset//limit+1` page mapping (job interfaces unchanged).
2. **Acceptance bound:** `ESPN_MAX_PAGES=25` (default in live test) covers the full 19-page
   1829-athlete pool → ranked fighters included.
3. Promotion canonical external_id = league slug (`"ufc"`).
4. Live DB = fresh `mma` db (owner `mma`); superuser password `REDACTED` never committed.
5. Live test env-gated (`MMA_LIVE_SYNC=1`) so CI/normal pytest stays offline.
6. 20/104 ranked fighters not on ESPN's league roster list → ranking rows skipped by FK
   guard (accepted data-coverage nuance, documented).
7. T10 deleted the users.py notif stubs rather than merging — the real router is strictly
   richer; deletion also fixed the route-shadowing (stub registered first) bugs.
8. `MissingGreenlet` lesson: with `expire_on_commit`, build API responses from ORM objects
   BEFORE `session.commit()` (or use `populate_existing`).

## 6. Current Progress

- T01–T18: **Completed** — milestone "Make the Data Flow + Contract Integrity" **DONE**
  (gates: 419 passed + 1 skip, ruff/mypy clean, mobile tsc 0, expo export OK).
- Implementation overall: **100%** of milestone tasks.

## 7. Remaining Work

1. None — milestone complete. Optional follow-ups on user request: commit the working tree
   (HEAD `d3ecc68`), present the final milestone report, run the live sync acceptance (T05,
   `MMA_LIVE_SYNC=1`, ~4 min) again.

## 8. Resume Point

If this session is interrupted:

1. Read `PROJECT_STATE.md`, `SESSION_STATE.md`, `EXECUTION_PLAN.md` (repo root).
2. Milestone T01–T18 is **complete** (all gates green, docs updated). Next work is whatever
   the user requests (e.g., commit, report, or the T18 live acceptance re-run). Environment:
   venv python `C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe`; gates
   from `backend/` workdir; live test `$env:MMA_LIVE_SYNC="1"` (adds ~4 min); DB
   `postgresql+asyncpg://mma:mma@localhost:5432/mma`.
3. git HEAD `d3ecc68`; working tree contains uncommitted T01–T18 changes (do not commit
   unless the user asks).

---

## 9. Session Wrap-up — 2026-08-06 (milestone close)

**State of the repository at session end** (snapshot for the next instance):

- **Milestone T01–T18 "Make the Data Flow + Contract Integrity": COMPLETE.** All gates green:
  pytest **419 passed, 1 skipped** (env-gated live test), ruff clean, mypy Success (186 files),
  mobile `npx tsc --noEmit` 0 errors, `npx expo export --platform web` bundled OK.
- **Uncommitted work:** the entire T01–T18 working tree (~83 files changed: backend sync/
  degradation/contract work + mobile env/model-alignment work) sits on top of HEAD `d3ecc68`.
  **Nothing has been committed this milestone — commit only if the user asks.**
- **Live environment still available:** PostgreSQL service `postgresql-x64-18` (db `mma`,
  `mma:mma`), live sync acceptance runnable via `$env:MMA_LIVE_SYNC="1"` (~4 min);
  venv python `C:\Users\-\AppData\Local\Temp\opencode\mma-venv\Scripts\python.exe`.
- **Key architectural facts recorded for continuation:** backend schemas are the single source
  of truth for mobile types (PROJECT_STATE §12.11); `/v1/rankings/p4p` returns one
  `RankingCategory` (12.13); notifications keep camelCase keys (12.14); watchlist events shape
  is `{id,title,subtitle,date}` (12.15); fighters keeps two compiled layers (12.12).
- **Known issues that remain open (non-blocking):** GET `/v1/notifications` ignores the
  `read` filter (badge count approximate); recommendations backend returns rules-based hardcoded
  `score`s; ESPN data coverage nuance (only 1 current UFC event; 20/104 ranked fighters not on
  the league roster list → skipped by FK guard by design).
- **Suggested next steps (not started, user's call):** commit the milestone; present the final
  milestone report; re-run the live sync acceptance; begin a Backlog item (EXECUTION_PLAN §Backlog:
  B1 officials sync, B2 per-fight zone stats, B3 seasons date-range filter, B4 records breakdown,
  B5 stats leaders, B6 espn_id exposure, B7 multi-league, E1 Redis job store, E2 TheSportsDB
  enrichment, E3 Postgres e2e in CI).
- **Housekeeping:** `session-ses_0327.md` at repo root is a stray untracked file — never commit.
