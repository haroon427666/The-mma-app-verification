# ESPN API Endpoint Verification Report

**Date:** 2026-08-01
**Method:** Live API calls against `sports.core.api.espn.com`
**Status:** ALL endpoints confirmed with actual response shapes

---

## 1. Verified Endpoint Catalog

### 1.1 Leagues (Promotions)

| Endpoint | Status | Response Shape |
|---|---|---|
| `GET /v2/sports/mma/leagues?limit=N` | ✅ 200 | Paginated. `items[]` = `$ref` URLs. `count: 48`, `pageIndex`, `pageCount` |
| `GET /v2/sports/mma/leagues/{slug}` | ✅ 200 | Full inline detail: `id`, `name`, `displayName`, `abbreviation`, `slug`, `season.{year}`, `logos[{href}]`, `gender` |

**Example response (UFC):**
```json
{"id":"3321","name":"Ultimate Fighting Championship","displayName":"UFC","abbreviation":"UFC","slug":"ufc","season":{"year":2026},"logos":[{"href":"https://a.espncdn.com/i/teamlogos/leagues/500/ufc.png"}],"gender":"MALE"}
```

### 1.2 Athletes (Fighters)

| Endpoint | Status | Response Shape |
|---|---|---|
| `GET /v2/sports/mma/leagues/{league}/athletes?limit=N` | ✅ 200 | Paginated. `items[]` = `$ref` URLs pointing to `/v2/sports/mma/athletes/{id}` |
| `GET /v2/sports/mma/athletes/{id}` | ✅ 200 | Full inline: `firstName`, `lastName`, `fullName`, `displayName`, `weight`(lbs), `height`(in), `reach`(in), `weightClass`(inline), `stance`(inline), `statistics.$ref`, `records.$ref`, `status.name`, `active`, `slug`, `images[]` |
| `GET /v2/sports/mma/athletes/{id}/records` | ✅ 200 | Paginated. `items[]` with `summary: "28-1-0"`, `stats[{name:"wins",value:28}]` |
| `GET /v2/sports/mma/athletes/{id}/statistics` | ✅ 200 | `splits.categories[{name, stats[{name, value, displayValue}]}]` |
| `GET /v2/sports/mma/athletes/{id}/eventlog` | ✅ 200 | Fighter's fight history (documented, not tested here) |

**CRITICAL:** `weight` is in **pounds**, `height` is in **inches**, `reach` is in **inches**. Must convert to metric.
**CRITICAL:** NO `nickname` field on the athlete resource.
**CRITICAL:** `weightClass` is INLINE `{id, text, shortName, slug}` — NOT a `$ref`.
**CRITICAL:** `stance` is INLINE `{id, text}` — NOT a `$ref`.

### 1.3 Events

| Endpoint | Status | Response Shape |
|---|---|---|
| `GET /v2/sports/mma/leagues/{league}/events?dates=YYYY&limit=N` | ✅ 200 | Paginated. `items[]` = `$ref` URLs |
| `GET /v2/sports/mma/leagues/{league}/events/{id}` | ✅ 200 | Full inline: `id`, `name`, `shortName`, `date`, `status.type.name`, `league.$ref`, `venues[{.$ref}]`, **`competitions[]` EMBEDDED (not $refs!)** |

**CRITICAL:** Competitions are **embedded** in the event response, not separate `$ref`s. Each competition in the array has full inline data including: `id`, `description`, `type.{text}`, `competitors[{athlete.$ref, winner, order}]`, `cardSegment.{id,description,name}`, `venue`(embedded), `status.$ref`, `broadcasts.$ref`.

### 1.4 Competitions (Fights)

| Endpoint | Status | Response Shape |
|---|---|---|
| (Embedded in event) | ✅ 200 | `id`, `matchNumber`, `cardSegment.{name:"main"|"prelims1"|"prelims2", description:"Main Card"|"Prelims"|"Early Prelims"}`, `type.{text:"Lightweight"}`, `competitors[{order, winner, athlete.$ref}]`, `description:"3 Rnd (5-5-5)"` |
| `GET .../competitions/{comp_id}/status` | ✅ 200 | `type.name:"STATUS_FINAL"`, `result.{name:"submission", displayName:"Submission", description:"D'Arce Choke"}`, `clock`, `period` |
| `GET .../competitions/{comp_id}/broadcasts` | ✅ 200 | `items[{market.{type:"National"}, media.{name:"PPV", callLetters:"PPV"}, type.{shortName:"PPV"}, lang, region}]` |
| `GET .../competitions/{comp_id}/competitors/{id}/statistics` | ✅ 200 | Per-fight stats (documented, not tested here) |

**CRITICAL:** `cardSegment.name` maps: `"main"` → Main Card, `"prelims1"` → Prelims, `"prelims2"` → Early Prelims.
**CRITICAL:** `type.{text}` is the weight class name — INLINE, not a `$ref`.

### 1.5 Rankings

| Endpoint | Status | Response Shape |
|---|---|---|
| `GET /v2/sports/mma/leagues/{league}/rankings` | ✅ 200 | Paginated. `items[]` = `$ref` URLs to ranking categories |
| `GET .../rankings/{category}` | ✅ 200 | `id`, `name`, `type:"pound-for-pound"`, `gender`, `ranks[{current, trend, athlete.$ref, hasAccolade, defenses}]` |

**CRITICAL:** Rank entries use `current` (not `rank`) and `hasAccolade` (not `isChampion`). `trend` is "-", "+2", etc.
**CRITICAL:** NO `weightClass` reference at the ranking level. The category name identifies the division.

### 1.6 Venues

Venues are **embedded** in competition data within events. The event's `venues[]` array contains `$ref`s to resolve separately.
The venue URL pattern is: `/v2/sports/mma/leagues/{league}/venues/{id}`

### 1.7 Broadcasts

Per-competition $ref: `GET .../competitions/{comp_id}/broadcasts` returns:
```json
{"items":[{"market":{"type":"National"},"media":{"name":"PPV"},"type":{"shortName":"PPV"},"lang":"en","region":"us"}]}
```

---

## 2. Critical Corrections Required

| # | What We Coded | What's Actually True | Files to Fix |
|---|---|---|---|
| 1 | Non-league-scoped URLs like `/{resource}` | All list endpoints are league-scoped: `/leagues/{league}/{resource}` | config.py, provider.py |
| 2 | `parse_*_list()` parses embedded items | Items in list responses are ALWAYS `$ref` URLs | All parsers |
| 3 | Fighter `weight` in kg, `height` in cm | Imperial units (lbs, inches). Must convert. | fighter.py |
| 4 | `weightClass` is a `$ref` | INLINE object `{id, text, shortName, slug}` | fighter.py, competition.py |
| 5 | Fighter has `nickname` field | No nickname field exists | fighter.py, DTO |
| 6 | Fighter `record` is direct field | Record is under separate `records` $ref endpoint | fighter.py |
| 7 | Competitions fetched via separate endpoint | Competitions EMBEDDED in event response | event.py, competition.py, provider.py |
| 8 | Rankings use `rank`, `is_champion` | Uses `current`, `hasAccolade` | ranking.py |
| 9 | Rankings use `entries[]` | Uses `ranks[]` | ranking.py |
| 10 | Separate weight class endpoint | Weight classes extracted from athlete/competition inline data | provider.py, weight_class.py |
| 11 | `cardSegment` has single name | Has `name`(code) + `description`(display) | competition.py |
| 12 | Venue is separate endpoint | Venue EMBEDDED in competition data | venue.py, event.py |

---

## 3. Summary of URL Patterns (VERIFIED)

```
BASE = https://sports.core.api.espn.com/v2/sports/mma

# List endpoints (return $refs → must resolve each item)
GET /leagues                                    → 48 orgs as $refs
GET /leagues/{league}/athletes                  → fighters as $refs
GET /leagues/{league}/events?dates=YYYY         → events as $refs
GET /leagues/{league}/rankings                  → categories as $refs

# Detail endpoints (return full inline data)
GET /leagues/{slug}?lang=en&region=us            → full league detail
GET /athletes/{id}?lang=en&region=us             → full fighter detail
GET /athletes/{id}/records                       → W/L/D record
GET /athletes/{id}/statistics                    → career stats
GET /leagues/{league}/events/{id}                → event + EMBEDDED competitions
GET .../competitions/{id}/status                 → fight result
GET .../competitions/{id}/broadcasts              → where to watch
GET /leagues/{league}/rankings/{category}        → ranked fighters list
```
