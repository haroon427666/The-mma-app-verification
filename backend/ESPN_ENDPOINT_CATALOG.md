# ESPN MMA Endpoint Catalog

**Definitive reference for every ESPN endpoint consumed by the sync engine.**
Last verified: 2026-08-01 (live API calls); reconciled against the frozen ESPN
research (2026-08-09) — pagination, league count, records/statistics wiring,
historical discovery, and rate envelope below reflect the research evidence.
Status indicators: ✅ verified, ⚠️ partial, ❌ not available.

Base: `https://sports.core.api.espn.com/v2/sports/mma`

---

## 1. Leagues (Promotions)

### 1.1 League Detail
```
GET /leagues/{slug}?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **$ref in response** | `season.$ref`, `events.$ref`, `seasons.$ref`, `calendar.$ref` |
| **Parser** | `espn/parsers/promotion.py::parse_promotion()` |
| **DTO** | `PromotionDTO` |
| **Sync Job** | `ESPN_PromotionSyncJob._fetch()` |
| **DB Table** | `promotions` |
| **Caveats** | Uses slug ("ufc"), NOT numeric ID ("3321"). `abbreviation` and `shortName` are identical for UFC. `logos[]` is an array — take `logos[0].href`. `gender` is a simple string ("MALE"). |

### 1.2 Leagues List
```
GET /leagues
```
| Aspect | Detail |
|---|---|
| **Params** | None (returns all 49 leagues — research: 48 enumerated + CES) |
| **Pagination** | Page-based (`page` 1-indexed); returns `count`, `pageIndex`, `pageCount` |
| **$ref in response** | Each league is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_promotion()` |
| **Sync Job** | `ESPN_PromotionSyncJob._fetch()` |
| **DB Table** | `promotions` |
| **Caveats** | Items in the response are `$ref` URLs — must be resolved individually. The list returns ~49 leagues including defunct orgs. ONE Championship's slug is **`ofc`** (research-verified). Filter by `gender` if needed. |

---

## 2. Athletes (Fighters)

### 2.1 Fighter Detail
```
GET /athletes/{id}?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **$ref in response** | `statistics.$ref`, `records.$ref`, `eventLog.$ref`, `leagues.$ref`, `defaultLeague.$ref` |
| **Parser** | `espn/parsers/fighter.py::parse_fighter()` |
| **DTO** | `FighterDTO` |
| **Sync Job** | `ESPN_FighterSyncJob._fetch()` (discovery-driven: global listing + league rosters, resolved by ID) |
| **DB Table** | `fighters` (+ `fighter_records` for the breakdown) |
| **Caveats** | `weight` (lbs), `height` (in), `reach` (in) → must convert to metric. `reach` may be `0.0` (treat as NULL). `weightClass` is INLINE `{id, text, shortName, slug}` — NOT a `$ref`. `stance` is INLINE `{id, text}` — NOT a `$ref`. `images[]` is usually empty — fallback to CDN URL pattern. NO `nickname` field. `records` and `statistics` are separate $refs — fetch independently. `active` is present on most athlete resources but NOT guaranteed — `is_active` is presence-guarded (a missing field never flips the stored flag). |

### 2.2 Fighter List (League-Scoped)
```
GET /leagues/{league}/athletes?limit={N}&page={P}&lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `limit` (default 25, max ~1000), `page` (1-indexed), `lang=en`, `region=us` |
| **Pagination** | **Page-based** — ESPN ignores `offset` on v2 list endpoints; drive the walk with `page` and trust echoed `pageIndex`/`pageCount` (probe-verified on athletes/leagues/events/rankings). |
| **$ref in response** | Each item in `items[]` is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_fighter()` per fighter |
| **Sync Job** | `ESPN_FighterSyncJob._fetch()` (discovery-driven) |
| **DB Table** | `fighters` |
| **Caveats** | UFC roster ~1,840 (drifts; research census 38,014 candidate IDs). Discovery enumerates the **global flat listing** (`/athletes`) **plus** league rosters, deduplicated by ESPN ID — the flat listing alone misses hidden profiles (Rousey 2563796, DJ 2512089, Gracie 2335697, Ngannou 3933168...). |

### 2.3 Fighter Records
```
GET /athletes/{id}/records?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | Yes (but typically 1 page for overall) |
| **$ref in response** | Each record category is a `$ref` |
| **Parser** | `espn/parsers/records.py::parse_fighter_records()` (full breakdown) |
| **DTO** | `FighterDTO` (record_* fields incl. ko/sub/title breakdown) |
| **Sync Job** | `ESPN_FighterSyncJob` — records fetched per fighter with bounded concurrency and persisted to `fighter_records` via `FighterUpsert` |
| **DB Table** | `fighters` (record_* columns) + `fighter_records` (breakdown) |
| **Caveats** | Stats include: wins, losses, draws, noContests, submissions (= sub wins), submissionLosses, tkos (= KO/TKO wins), tkoLosses, titleWins, titleLosses, titleDraws. `summary` provides "21-5-0". **Unavailable/empty records never reset stored values** (research GAP fixed: fighters used to persist 0-0-0-0). |

### 2.4 Fighter Statistics
```
GET /athletes/{id}/statistics?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **$ref in response** | None (full inline) |
| **Parser** | `espn/parsers/statistics.py::parse_statistics()` |
| **DTO** | `StatisticDTO` |
| **Sync Job** | `ESPN_StatisticSyncJob._fetch()` — career stats fetched per fighter (bounded: `ESPN_STATS_MAX_FIGHTERS`, default 200) |
| **DB Table** | `statistics` (career rows: `competitor_id` NULL, keyed by fighter_id; migration 006) |
| **Caveats** | `splits.categories[{name, stats[{name, value, displayValue}]}]`. Categories: "GENERAL", "STRIKING", "GRAPPLING". Career stats are **content-dependent** — athletes without stats produce no rows (never fabricated). |

---

## 3. Events

### 3.1 Event Detail
```
GET /leagues/{league}/events/{eventId}?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **$ref in response** | `season.$ref`, `league.$ref`, `venues[].$ref` |
| **Parser** | `espn/parsers/event.py::parse_event()` |
| **DTO** | `EventDTO` |
| **Sync Job** | `ESPN_EventSyncJob._fetch()` (resolves $refs from list) |
| **DB Table** | `events` |
| **Caveats** | **CRITICAL: `competitions[]` is EMBEDDED in the event response** (not separate $refs). This saves N API calls. `status.type.name` maps to: STATUS_SCHEDULED, STATUS_FINAL, STATUS_CANCELLED. `shortName` is "UFC Fight Night" (without the main event names). |

### 3.2 Event List (League-Scoped)
```
GET /leagues/{league}/events?limit={N}&page={P}&dates={YYYY}&lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `limit`, `page` (1-indexed), `dates` (YYYY format), `lang=en`, `region=us` |
| **Pagination** | Page-based (offset ignored by ESPN). Returns `count`, `pageIndex`, `pageCount`. |
| **$ref in response** | Each item in `items[]` is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_event()` |
| **Sync Job** | `ESPN_EventSyncJob._fetch()` |
| **DB Table** | `events` |
| **Caveats** | **⚠️ UPCOMING-ONLY** — research proved this listing returns count=1 (the next event) for every league and **must never be used for history**. Historical events come from `ESPN_HistoricalEventSyncJob` via the winningFight chain + athlete eventlogs. |

---

## 4. Competitions (Fights)

### 4.1 Competitions (Embedded in Event)
```
(No dedicated endpoint — competitions[] is embedded in GET /leagues/{league}/events/{id})
```
| Aspect | Detail |
|---|---|
| **Parser** | `espn/parsers/event.py::extract_competitions_from_event()` + `espn/parsers/competition.py::parse_competition()` |
| **DTO** | `CompetitionDTO` (with nested `CompetitorDTO[]`) |
| **Sync Job** | `ESPN_CompetitionSyncJob._fetch()` → `ESPN_EventSyncJob` fetches events, then competitions extracted inline |
| **DB Table** | `competitions`, `competitors` |
| **Caveats** | Each competition has: `matchNumber`, `cardSegment.{name:"main"/"prelims1"/"prelims2", description}`, `type.{id, text, abbreviation}` (weight class INLINE), `competitors[{athlete.$ref, order, winner}]`, `status.$ref`, `broadcasts.$ref`. `format.regulation.periods` = 3 or 5 rounds. |

### 4.2 Competition Status (for results)
```
GET /leagues/{league}/events/{eventId}/competitions/{competitionId}/status?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **Parser** | `espn/parsers/competition.py::parse_competition_status()` |
| **DTO** | `CompetitionDTO` (enriches result fields) |
| **Sync Job** | `ESPN_CompetitionSyncJob._fetch()` — fires AFTER competition is parsed |
| **DB Table** | `competitions` (result_method, result_detail, result_round, result_time) |
| **Caveats** | Only fetch for FINAL events. Response: `{clock, displayClock, period, type.{name}, result.{name, displayName, description}}`. `result.name`: "submission", "ko", "tko", "decision". `result.description`: "D'Arce Choke", "Punches", etc. |

### 4.3 Competition Broadcasts
```
GET /leagues/{league}/events/{eventId}/competitions/{competitionId}/broadcasts?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | Yes (`items[]` in response) |
| **Parser** | `espn/parsers/broadcast.py::parse_broadcast_list()` |
| **DTO** | `BroadcastDTO` |
| **Sync Job** | `ESPN_BroadcastSyncJob._fetch()` |
| **DB Table** | `broadcasts` |
| **Caveats** | Deduplicate at event level (same network+region combination across competitions). Response: `items[{market.{type}, media.{name, callLetters}, type.{shortName}, lang, region}]`. |

### 4.4 Competitor Statistics
```
GET /leagues/{league}/events/{eventId}/competitions/{competitionId}/competitors/{competitorId}/statistics?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **Parser** | `espn/parsers/statistics.py::parse_statistics()` |
| **DTO** | `StatisticDTO` |
| **Sync Job** | `ESPN_StatisticSyncJob` (per-competition) |
| **DB Table** | `statistics` |
| **Caveats** | Per-fight stats (different from career stats at /athletes/{id}/statistics). Only available after fight is complete. |

---

## 5. Rankings

### 5.1 Rankings Categories List
```
GET /leagues/{league}/rankings?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | Yes (24 categories, 1 page) |
| **$ref in response** | Each item is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_ranking_category()` |
| **Sync Job** | `ESPN_RankingSyncJob._fetch()` |
| **DB Table** | `rankings` |
| **Caveats** | 24 ranking categories confirmed. Includes: P4P (men), P4P (women), 8 men's divisions, 3 women's divisions (each with champion + contender lists). |

### 5.2 Ranking Category Detail
```
GET /leagues/{league}/rankings/{category}?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **Parser** | `espn/parsers/ranking.py::parse_ranking_category()` + `extract_winning_fight_refs()` |
| **DTO** | `RankingDTO` |
| **Sync Job** | `ESPN_RankingSyncJob._fetch()` (per category) |
| **DB Table** | `rankings` (atomic replace per category) |
| **Caveats** | `ranks[{current, trend, athlete.$ref, hasAccolade, defenses, winningFight.$ref}]`. Uses `current` (not `rank`). `hasAccolade` = champion indicator. **`winningFight` is the historical-event discovery hook** — every rank entry carries a competition ref (legacy 400/600-series event ids); consumed by `ESPN_HistoricalEventSyncJob`. |

---

## 6. Venues

### 6.1 Venue Detail
```
GET /leagues/{league}/venues/{venueId}?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | No |
| **Parser** | `espn/parsers/venue.py::parse_venue()` |
| **DTO** | `VenueDTO` |
| **Sync Job** | `ESPN_VenueSyncJob` (resolves from event $refs) |
| **DB Table** | `venues` |
| **Caveats** | Venue data is also EMBEDDED in competition data: `venue.{id, fullName, address.{city, country}, indoor, grass}`. The resolved $ref adds: `capacity`, `geometry.{latitude, longitude}`. Either path works — $ref resolution gives richer data. |

---

## 7. $ref Resolution (Cross-Cutting)

### 7.1 RefResolver
```
(Not an endpoint — infrastructure component)
```
| Aspect | Detail |
|---|---|
| **File** | `espn/reference.py::RefResolver` |
| **Purpose** | Caches $ref resolutions within one sync run to avoid redundant HTTP calls |
| **Cache scope** | Per sync run (cleared between runs) |
| **Used by** | Every parser that encounters `{"$ref": "https://..."}` |
| **Caveats** | **BUG FOUND (FIXED):** `extract_id_from_ref()` must strip query params (`?lang=en&region=us`) before extracting ID from URL. `RefResolver.resolve_all()` resolves in parallel via `asyncio.gather()`. |

---

## 8. Records (Separate from Fighter Detail)

### 8.1 Fighter Records Detail
```
GET /athletes/{id}/records?lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `lang=en`, `region=us` |
| **Auth** | None |
| **Pagination** | Yes (one category per $ref item) |
| **$ref in response** | Each record category is a `$ref` |
| **Parser** | `espn/parsers/records.py::parse_fighter_records()` |
| **DTO** | `FighterDTO.record_*` fields (incl. breakdown) |
| **Sync Job** | `ESPN_FighterSyncJob` — wired (was a doc-only claim; now actually invoked) |
| **DB Table** | `fighters` + `fighter_records` |
| **Caveats** | The `items[0]` for "overall" contains: `summary: "21-5-0"`, `stats[{name:"wins", value:21}, ...]` plus `submissions`, `submissionLosses`, `tkos`, `tkoLosses`, `titleWins`, `titleLosses`, `titleDraws`. Full breakdown now persisted. |

---

## 9. Weight Classes (Inline Only)

### 9.1 Weight Class Data
```
(NO dedicated weight class endpoint exists on the Core API)
```
| Aspect | Detail |
|---|---|
| **Source** | Extracted INLINE from `athlete.weightClass` and `competition.type` |
| **Parser** | `espn/parsers/weight_class.py::parse_weight_class()` |
| **DTO** | `WeightClassDTO` |
| **Sync Job** | `ESPN_WeightClassSyncJob` (collects from other syncs) |
| **DB Table** | `weight_classes` |
| **Caveats** | `GET /weightclasses/{id}` → **404 (not a valid Core API endpoint)**. Must extract from inline data. ESPN weight class IDs: 970 (Bantamweight), 969 (Welterweight), 982 (Heavyweight), 986 (Lightweight), 972 (Middleweight), 990 (Light Heavyweight), 999 (Featherweight), 1006 (Women's Strawweight), 1003 (Women's Bantamweight), 1000 (Women's Flyweight), etc. |

---

## 10. Site API (Frontend Endpoints)

The Site API (`site.api.espn.com/apis/site/v2/sports/mma`) serves the ESPN website. These endpoints aggregate data from multiple Core API resources.

| Endpoint | Status | Notes |
|---|---|---|
| `/scoreboard` | ⚠️ 404 on direct query | Path structure differs from Core API. May require different base or params. |
| `/news` | ⚠️ Not tested | |
| `/summary?event={id}` | ⚠️ Not tested | Aggregated event view |
| `/event?event={id}` | ⚠️ Not tested | Aggregated event view |

**Recommendation:** Site API endpoints are NOT needed for the sync pipeline. The Core API provides all structured data. Site API may be useful for the frontend (aggregated scoreboard, news) but adds complexity to the provider layer.

---

## 11. Endpoint → Parser → Job → Table Matrix

| # | Endpoint | Parser | Sync Job | DB Table | Verified |
|---|---|---|---|---|---|
| 1 | `GET /leagues/{slug}` | `promotion.py::parse_promotion` | `ESPN_PromotionSyncJob` | `promotions` | ✅ |
| 2 | `GET /leagues` | RefResolver + `parse_promotion` | `ESPN_PromotionSyncJob` | `promotions` | ✅ |
| 3 | `GET /athletes/{id}` | `fighter.py::parse_fighter` | `ESPN_FighterSyncJob` | `fighters` | ✅ |
| 4 | `GET /leagues/{l}/athletes` | RefResolver + `parse_fighter` | `ESPN_FighterSyncJob` | `fighters` | ✅ |
| 4b | `GET /athletes` (global listing) | ID enumeration | `ESPN_FighterSyncJob` (discovery) | `fighters` | ✅ |
| 5 | `GET /athletes/{id}/records` | `records.py::parse_fighter_records` | `ESPN_FighterSyncJob` | `fighters` + `fighter_records` | ✅ |
| 6 | `GET /athletes/{id}/statistics` | `statistics.py::parse_statistics` | `ESPN_StatisticSyncJob` | `statistics` (career) | ✅ |
| 6b | `GET /athletes/{id}/eventlog` | `eventlog.py::parse_eventlog_refs` | `ESPN_HistoricalEventSyncJob` (config-gated) | `events` | ✅ |
| 7 | `GET /leagues/{l}/events/{id}` | `event.py::parse_event` | `ESPN_EventSyncJob` / `ESPN_HistoricalEventSyncJob` | `events` | ✅ |
| 8 | `GET /leagues/{l}/events` | RefResolver + `parse_event` | `ESPN_EventSyncJob` | `events` (upcoming-only) | ✅ |
| 9 | *(embedded in event)* | `competition.py::parse_competition` | `ESPN_CompetitionSyncJob` | `competitions`, `competitors` | ✅ |
| 10 | `GET .../competitions/{id}/status` | `competition.py::parse_competition_status` | `ESPN_CompetitionSyncJob` | `competitions` (result_*) | ✅ |
| 11 | `GET .../competitions/{id}/broadcasts` | `broadcast.py::parse_broadcast_list` | `ESPN_BroadcastSyncJob` | `broadcasts` | ✅ |
| 12 | `GET /leagues/{l}/rankings` | RefResolver | `ESPN_RankingSyncJob` | `rankings` | ✅ |
| 13 | `GET /leagues/{l}/rankings/{cat}` | `ranking.py::parse_ranking_category` + winningFight refs | `ESPN_RankingSyncJob` / `ESPN_HistoricalEventSyncJob` | `rankings` + historical events | ✅ |
| 14 | `GET /leagues/{l}/venues/{id}` | `venue.py::parse_venue` | `ESPN_VenueSyncJob` | `venues` | ✅ |
| 15 | *(inline from athlete/competition)* | `weight_class.py::parse_weight_class` | `ESPN_WeightClassSyncJob` | `weight_classes` | ✅ |
| 16 | `GET .../competitors/{id}/statistics` | `statistics.py::parse_statistics` | `ESPN_StatisticSyncJob` | `statistics` (per-fight) | ✅ |

---

## 12. Known Caveats Summary

| # | Caveat | Impact | Mitigation |
|---|---|---|---|
| 1 | `$ref` URLs include `?lang=en&region=us` query params | ID extraction was broken | Fixed: `extract_id_from_ref()` splits on `?` first |
| 2 | `reach: 0.0` treated as falsy → returned None | 25% of fighters lost reach data | Fixed: `if inches is not None` instead of `if inches` |
| 3 | `weightClass` and `stance` are INLINE objects, not `$ref`s | Parser expecting $ref would fail | Confirmed: both parsed as `data.get("weightClass",{}).get("id")` |
| 4 | `images[]` is usually empty on fighter detail | 70% of fighters lack headshots from ESPN | Fallback: construct CDN URL pattern. Octagon API covers the gap. |
| 5 | `competitions[]` EMBEDDED in event — NOT separate $refs | Old code expected separate competitions fetch | Fixed: `extract_competitions_from_event()` reads inline array |
| 6 | `cardSegment.name` uses codes: "main", "prelims1", "prelims2" | Needs mapping to human-readable | `CARD_SEGMENT_MAP` in config.py |
| 7 | Rankings use `current` (not `rank`) and `hasAccolade` (not `isChampion`) | Schema mismatch with expectations | Adapted: `entry.get("current")`, `entry.get("hasAccolade")` |
| 8 | `GET /weightclasses/{id}` returns 404 | No dedicated weight class endpoint | Weight classes extracted INLINE from athlete/competition data |
| 9 | Pagination is **page-based** (`page` 1-indexed; ESPN ignores `offset`; limit capped ~1000) | Must drive the walk with `page` | `client.paginate()` advances by page and trusts echoed `pageIndex`/`pageCount` |
| 10 | All league-scoped endpoints use `{slug}` not numeric `{id}` | URL construction requires slug | `ENDPOINTS` config uses `{league_slug}` format strings |
| 11 | `/leagues/{slug}/events` is **upcoming-only** (count=1) | No historical events from listings | `ESPN_HistoricalEventSyncJob`: rankings → winningFight → events/{id} (+ eventlogs) |
| 12 | ONE Championship slug is `ofc`, not `one-championship` | Wrong slug → 404 | `ESPN_LEAGUE_SLUGS` corrected |
| 13 | Flat athlete listing alone misses hidden profiles | ~95% of the 38,014 census unreachable | Discovery = global listing + league rosters + ranking/event refs, deduped by ID |

---

## 13. Rate Limit & Request Efficiency

Research (PERFORMANCE_FINAL_REPORT) measured a substantially better envelope
under controlled conditions; the original 50–55 req/min was NOT a proven ESPN
hard limit. Production is configured INSIDE the measured safe envelope:

| Metric | Configured Value |
|---|---|
| Sustained rate | **3.0 req/s** (research: 2–5) |
| Burst capacity | 6 (token bucket) |
| Bounded concurrency | 6 workers (research: 4–8) |
| Retry | 3× backoff 2.0 on (429, 500, 502, 503, 504) + DNS/network; **no retry on 400/404** |
| Response cache | URL-canonicalized TTL cache (300s) + in-flight dedup |
| Keep-alive | httpx pool (10 keepalive / 20 max connections) |
| Circuit breaker | 5 consecutive failures → 60s cooldown |

---

**End of catalog. 18 rows mapped to parsers, jobs, and tables (incl. global listing, eventlog, and historical discovery).**