# ESPN MMA Endpoint Catalog

**Definitive reference for every ESPN endpoint consumed by the sync engine.**
Last verified: 2026-08-01 (live API calls). Status indicators: ✅ verified, ⚠️ partial, ❌ not available.

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
| **Params** | None (returns all 48 leagues) |
| **Pagination** | Implicit — returns `count`, `pageIndex`, `pageCount` |
| **$ref in response** | Each league is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_promotion()` |
| **Sync Job** | `ESPN_PromotionSyncJob._fetch()` |
| **DB Table** | `promotions` |
| **Caveats** | Items in the response are `$ref` URLs — must be resolved individually. The list returns ~48 leagues including defunct orgs. Filter by `gender` if needed. |

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
| **Sync Job** | `ESPN_FighterSyncJob._fetch()` (resolves $refs from list) |
| **DB Table** | `fighters` |
| **Caveats** | `weight` (lbs), `height` (in), `reach` (in) → must convert to metric. `reach` may be `0.0` (treat as NULL). `weightClass` is INLINE `{id, text, shortName, slug}` — NOT a `$ref`. `stance` is INLINE `{id, text}` — NOT a `$ref`. `images[]` is usually empty — fallback to CDN URL pattern. NO `nickname` field. `records` and `statistics` are separate $refs — fetch independently. |

### 2.2 Fighter List (League-Scoped)
```
GET /leagues/{league}/athletes?limit={N}&offset={M}&lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `limit` (default 100), `offset`, `lang=en`, `region=us` |
| **Pagination** | Offset-based: `pageIndex * limit`. Returns `count`, `pageIndex`, `pageCount`. |
| **$ref in response** | Each item in `items[]` is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_fighter()` per fighter |
| **Sync Job** | `ESPN_FighterSyncJob._fetch()` |
| **DB Table** | `fighters` |
| **Caveats** | 1,809 total UFC fighters (19 pages at limit=100). Each `$ref` must be individually resolved — `RefResolver` caches within a run. |

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
| **Parser** | `espn/parsers/fighter.py::parse_fighter_records()` |
| **DTO** | `FighterDTO` (record_wins/losses/draws/no_contests) |
| **Sync Job** | `ESPN_FighterSyncJob` (resolved post-fetch) |
| **DB Table** | `fighters` (record_* columns) |
| **Caveats** | Stats include: wins, losses, draws, noContests, submissionWins, submissionLosses, tkoWins, tkoLosses, titleWins, titleLosses, titleDraws. Currently only extracting W/L/D/NC. `summary` field provides "21-5-0" format string. |

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
| **Sync Job** | `ESPN_StatisticSyncJob._fetch()` or per-fighter during `ESPN_FighterSyncJob` |
| **DB Table** | `statistics` |
| **Caveats** | `splits.categories[{name, stats[{name, value, displayValue}]}]`. Categories: "GENERAL", "STRIKING", "GRAPPLING". Stats include: knockdowns, sig strikes landed/attempted, takedowns landed/attempted, submission attempts, reversals, control time. |

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
GET /leagues/{league}/events?limit={N}&offset={M}&dates={YYYY}&lang=en&region=us
```
| Aspect | Detail |
|---|---|
| **Params** | `limit`, `offset`, `dates` (YYYY format), `lang=en`, `region=us` |
| **Pagination** | Offset-based. Returns `count`, `pageIndex`, `pageCount`. |
| **$ref in response** | Each item in `items[]` is a `$ref` URL |
| **Parser** | Resolved via `RefResolver`, then `parse_event()` |
| **Sync Job** | `ESPN_EventSyncJob._fetch()` |
| **DB Table** | `events` |
| **Caveats** | Each `$ref` must be resolved. Use `dates` param to filter by year. The resolved event contains embedded competitions — fetch competitions from it, not separately. |

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
| **Parser** | `espn/parsers/ranking.py::parse_ranking_category()` |
| **DTO** | `RankingDTO` |
| **Sync Job** | `ESPN_RankingSyncJob._fetch()` (per category) |
| **DB Table** | `rankings` (atomic replace per category) |
| **Caveats** | `ranks[{current, trend, athlete.$ref, hasAccolade, defenses}]`. Uses `current` (not `rank`). `hasAccolade` = champion indicator. `trend`: "-", "+2", etc. Rankings are ATOMIC REPLACE — DELETE all for category, then INSERT. |

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
| **Parser** | `espn/parsers/fighter.py::parse_fighter_records()` |
| **DTO** | `FighterDTO.record_*` fields |
| **Sync Job** | Resolved during `ESPN_FighterSyncJob` |
| **DB Table** | `fighters` |
| **Caveats** | The `items[0]` for "overall" contains: `summary: "21-5-0"`, `stats[{name:"wins", value:21}, {name:"losses", value:5}, ...]`. Also includes: `submissionWins`, `tkoWins`, `titleWins` (not currently extracted — available for future). |

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
| 5 | `GET /athletes/{id}/records` | `fighter.py::parse_fighter_records` | `ESPN_FighterSyncJob` | `fighters` (record_*) | ✅ |
| 6 | `GET /athletes/{id}/statistics` | `statistics.py::parse_statistics` | `ESPN_StatisticSyncJob` | `statistics` | ✅ |
| 7 | `GET /leagues/{l}/events/{id}` | `event.py::parse_event` | `ESPN_EventSyncJob` | `events` | ✅ |
| 8 | `GET /leagues/{l}/events` | RefResolver + `parse_event` | `ESPN_EventSyncJob` | `events` | ✅ |
| 9 | *(embedded in event)* | `competition.py::parse_competition` | `ESPN_CompetitionSyncJob` | `competitions`, `competitors` | ✅ |
| 10 | `GET .../competitions/{id}/status` | `competition.py::parse_competition_status` | `ESPN_CompetitionSyncJob` | `competitions` (result_*) | ✅ |
| 11 | `GET .../competitions/{id}/broadcasts` | `broadcast.py::parse_broadcast_list` | `ESPN_BroadcastSyncJob` | `broadcasts` | ✅ |
| 12 | `GET /leagues/{l}/rankings` | RefResolver | `ESPN_RankingSyncJob` | `rankings` | ✅ |
| 13 | `GET /leagues/{l}/rankings/{cat}` | `ranking.py::parse_ranking_category` | `ESPN_RankingSyncJob` | `rankings` | ✅ |
| 14 | `GET /leagues/{l}/venues/{id}` | `venue.py::parse_venue` | `ESPN_VenueSyncJob` | `venues` | ✅ |
| 15 | *(inline from athlete/competition)* | `weight_class.py::parse_weight_class` | `ESPN_WeightClassSyncJob` | `weight_classes` | ✅ |
| 16 | `GET .../competitors/{id}/statistics` | `statistics.py::parse_statistics` | `ESPN_StatisticSyncJob` | `statistics` | ✅ |

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
| 9 | Pagination is offset-based (`offset = pageIndex * limit`) | Must track offset per job | SyncState stores `last_offset` for resume |
| 10 | All league-scoped endpoints use `{slug}` not numeric `{id}` | URL construction requires slug | `ENDPOINTS` config uses `{league_slug}` format strings |

---

## 13. Rate Limit Observations

| Metric | Observed Value |
|---|---|
| Sustained rate | ~10 requests/second |
| Burst capacity | ~15 requests/second |
| 429 responses | None observed during Phase 4 testing |
| Recommended throttle | 8 req/s (leaves headroom) |
| Circuit breaker threshold | 5 consecutive failures → 60s cooldown |

---

**End of catalog. All 16 endpoints mapped to parsers, jobs, and tables.**