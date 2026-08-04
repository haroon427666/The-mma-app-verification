# ESPN MMA Public API — Complete Reference

> **Generated:** 2026-07-30 via live API calls (no auth required)  
> **Base URL:** `http://sports.core.api.espn.com/v2/sports/mma/`  
> **Legend:** ✅ Verified live · 🔵 Theoretical (same pattern) · 🟡 Partially verified  
> **Note:** All endpoints are HTTP GET, no API key required, support `?lang=en&region=us`

---

## Table of Contents

1. [Complete Endpoint Map](#1-complete-endpoint-map)
2. [Complete Data Field Inventory](#2-complete-data-field-inventory)
3. [Synced vs Available Gap Analysis](#3-synced-vs-available-gap-analysis)
4. [Additional Data Opportunities](#4-additional-data-opportunities)
5. [Recommended New Backend Endpoints](#5-recommended-new-backend-endpoints)

---

## 1. Complete Endpoint Map

### 1.1 Top-Level Discovery

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/v2/sports/mma/leagues?limit=100` | ✅ | 48 MMA leagues as `$ref` list |
| `/v2/sports/mma/leagues/{slug}` | ✅ | League detail with nested `$ref` links |
| `/v2/sports/mma/athletes/{id}` | ✅ | Full athlete profile |

---

### 1.2 League Endpoints

**Pattern:** `/v2/sports/mma/leagues/{league_slug}/...`

**All 48 verified league slugs:**
```
ufc, bellator, pfl, rizin, strikeforce, pride, wec, dream, pancrase,
lfa, rfa, cage-warriors, ksw, m1, k1, shooto-japan, shooto-brazil,
one-fc (use slug from list), mfc, ifl, ifc, proelite, xfc, vfc, roc,
sfl, ofc, lfc, mvp, tfc, tpf, fng, budo, bosnia, boxe, blackout,
absolute, affliction, bang-fighting, banni-fight, banzay, barracao,
battlezone, benevides, big-fight, brazilian-freestyle, shoxc, shark-fights, other
```

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/leagues/{slug}` | ✅ | id, guid, uid, name, displayName, abbreviation, shortName, slug, gender, logos[], links[], season($ref), seasons($ref), events($ref), calendar($ref) |
| `/leagues/{slug}/seasons` | ✅ | Paginated list of season `$ref` links (UFC has 34 seasons, 1993–2026) |
| `/leagues/{slug}/seasons/{year}` | ✅ | year, startDate, endDate, displayName, type($ref), types($ref) |
| `/leagues/{slug}/seasons/{year}/types` | ✅ | List of season type refs (UFC: only type 2 = Regular Season) |
| `/leagues/{slug}/seasons/{year}/types/{id}` | ✅ | id, type, name, abbreviation, year, startDate, endDate, hasGroups, hasStandings, hasLegs, slug |
| `/leagues/{slug}/events` | ✅ | Paginated list of event `$ref` links (current/upcoming only by default) |
| `/leagues/{slug}/calendar` | ✅ | 4 calendar sub-types: ondays, whitelist, blacklist, offdays |
| `/leagues/{slug}/calendar/ondays` | ✅ | Event dates with sections and season ref |
| `/leagues/{slug}/rankings` | ✅ | Paginated list of ranking category `$ref` links |
| `/leagues/{slug}/rankings/{category}` | ✅ | Full ranking list with athlete refs, rank, trend, defenses, champion flag |
| `/leagues/{slug}/venues/{id}` | ✅ | Venue detail |
| `/leagues/{slug}/media/{id}` | ✅ | Broadcast media detail (network name, logos) |

**UFC-specific ranking categories (24 total):**
```
pound-for-pound, womens-pound-for-pound,
heavyweight-champions, light-heavyweight-champions, middleweight-champions,
welterweight-champions, lightweight-champions, featherweight-champions,
bantamweight-champions, flyweight-champions, womens-bantamweight-champions,
womens-strawweight-champions, womens-flyweight-champions,
heavyweight, light-heavyweight, middleweight, welterweight, lightweight,
featherweight, bantamweight, flyweight,
womens-bantamweight, womens-strawweight, womens-flyweight
```

---

### 1.3 Event Endpoints

**Pattern:** `/v2/sports/mma/leagues/{slug}/events/{event_id}/...`

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/leagues/{slug}/events/{id}` | ✅ | Full event detail (see field inventory §2.2) |
| `/leagues/{slug}/events/{id}/competitions` | 🔵 | List of competition refs for this event |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}` | ✅ | Full competition detail (see §2.3) |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/status` | ✅ | Live/final status, clock, period, result, method |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/broadcasts` | ✅ | Broadcast networks with logos |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/officials` | ✅ | Referee + judges with names and positions |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/plays` | ✅ | Play-by-play events (32 plays per fight, paginated) |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/competitors` | 🔵 | List of competitor refs |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/competitors/{athlete_id}` | ✅ | Competitor in context: winner, order, athlete($ref), statistics($ref), record($ref) |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/competitors/{athlete_id}/statistics` | ✅ | Per-fight stats (40+ fields, see §2.6) |

---

### 1.4 Athlete Endpoints

**Pattern:** `/v2/sports/mma/athletes/{athlete_id}/...`

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/athletes/{id}` | ✅ | Full profile (see §2.1) |
| `/athletes/{id}/records` | ✅ | Paginated list of record types (overall, etc.) |
| `/athletes/{id}/records/0` | ✅ | Overall W/L/D/NC + breakdown by method (KO, TKO, Sub, etc.) |
| `/athletes/{id}/statistics` | 🔵 | List of statistic split refs |
| `/athletes/{id}/statistics/0` | ✅ | Career aggregate stats (6 core metrics) |
| `/athletes/{id}/eventlog` | ✅ | Fight history: event($ref), competition($ref), competitor($ref), played |
| `/athletes/{id}/leagues` | ✅ | All leagues this athlete has competed in |

---

### 1.5 Venue Endpoints

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/leagues/{slug}/venues/{id}` | ✅ | id, guid, fullName, address{city, country}, grass, indoor |
| `/leagues/{slug}/venues` | 🔵 | Likely paginated list of venue refs |

---

### 1.6 Media / Broadcast Endpoints

| Endpoint | Status | Returns |
|----------|--------|---------|
| `/leagues/{slug}/media/{id}` | ✅ | id, callLetters, name, shortName, slug, logos[] |
| `/leagues/{slug}/events/{id}/competitions/{comp_id}/broadcasts` | ✅ | type{id,shortName,longName,slug}, channel, slug, priority, market{id,type}, media($ref with inline), lang, region |

---

### 1.7 Pagination & Query Parameters

All list endpoints support:
- `?limit=N` — items per page (default 25, max ~100)
- `?page=N` — page number
- `?lang=en&region=us` — localization
- `?dates=YYYYMMDD` — filter events by date (on event list endpoints)

---

## 2. Complete Data Field Inventory

### 2.1 Athlete / Fighter

```
IDENTITY
  id                    string   ESPN athlete ID (e.g. "2591306")
  uid                   string   Scoped UID "s:3301~a:{id}"
  guid                  string   Global UUID
  firstName             string
  lastName              string
  fullName              string
  displayName           string
  shortName             string   "F. Lastname"
  nickname              string   e.g. "The Renegade"
  slug                  string   URL-safe name

PHYSICAL
  weight                float    In pounds
  displayWeight         string   "136 lbs"
  height                float    In inches
  displayHeight         string   "5' 10\""
  reach                 float    In inches
  displayReach          string   "71\""
  age                   int
  dateOfBirth           string   ISO 8601

FIGHTING STYLE
  weightClass           object   {id, text, shortName, slug}
  stance                object   {id, text}  e.g. "Orthodox" / "Southpaw"
  styles                array    [{id, text}]  e.g. "Mixed Martial Artist", "Wrestler"
  association           object   {id, name, location}  — GYM/TEAM

NATIONALITY
  gender                string   "MALE" / "FEMALE"
  citizenship           string   Country name
  citizenshipCountry    object   {alternateId, abbreviation, color, alternateColor}
  flag                  object   {href, alt, rel}  — flag image URL

MEDIA
  headshot              object   {href, alt}  — ESPN CDN headshot URL
  images                array    [{href, rel}]  — stance images (leftStance, rightStance)
  links                 array    ESPN.com profile links

STATUS
  active                bool
  linked                bool
  status                object   {id, name, type, abbreviation}

REFS (follow for more data)
  statistics            $ref     → /athletes/{id}/statistics
  records               $ref     → /athletes/{id}/records
  eventLog              $ref     → /athletes/{id}/eventlog
  leagues               $ref     → /athletes/{id}/leagues
  defaultLeague         $ref     → /leagues/{slug}
```

---

### 2.2 Event

```
IDENTITY
  id                    string   ESPN event ID
  uid                   string   "s:3301~l:{league_id}~e:{id}"
  guid                  string
  name                  string   "UFC Fight Night: Ankalaev vs. Guskov"
  shortName             string   "UFC Fight Night"

TIMING
  date                  string   ISO 8601 (event start)
  timeValid             bool

STATUS
  status.type           object   {id, name, state, completed, description, detail, shortDetail}
    state values: "pre" | "in" | "post"
    name values: "STATUS_SCHEDULED" | "STATUS_IN_PROGRESS" | "STATUS_FINAL"

RELATIONS
  season                $ref     → /seasons/{year}
  seasonType            $ref     → /seasons/{year}/types/{id}
  league                $ref     → /leagues/{slug}
  competitions          array    [{$ref, id, guid, uid, ...}]  — inline partial + ref
  venues                array    [{$ref}]

METADATA
  ticketsAvailable      bool
  links                 array    ESPN FightCenter URLs
```

---

### 2.3 Competition (Individual Fight)

```
IDENTITY
  id                    string   ESPN competition ID
  uid                   string   "s:3301~l:{league_id}~e:{event_id}~c:{id}"
  guid                  string
  description           string   "3 Rnd (5-5-5)" or "5 Rnd (5-5-5-5-5)"

TIMING
  date                  string   ISO 8601 (scheduled start)
  endDate               string   ISO 8601 (actual end)
  lastUpdated           string   ISO 8601

FIGHT METADATA
  matchNumber           int      Position on card (1=main event)
  cardSegment           object   {id, description, name}
    description values: "Main Card" | "Prelims" | "Early Prelims"
    name values: "main" | "prelims1" | "prelims2"
  type                  object   {id, text, abbreviation}  — weight class of this fight
  format.regulation     object   {periods, displayName, slug, clock}
    periods: 3 or 5 (rounds)
    clock: 300.0 (5 minutes per round)
  neutralSite           bool

AVAILABILITY FLAGS (all bool)
  boxscoreAvailable, gamecastAvailable, playByPlayAvailable,
  summaryAvailable, wallclockAvailable, recapAvailable,
  previewAvailable, lineupAvailable, conversationAvailable,
  highlightsAvailable, liveAvailable, ticketsAvailable,
  bracketAvailable, shotChartAvailable, timeoutsAvailable,
  possessionArrowAvailable, commentaryAvailable, pickcenterAvailable

DATA SOURCE
  gameSource            object   {id, description, state}  e.g. "feed" / "full"
  boxscoreSource        object   {id, description, state}
  playByPlaySource      object   {id, description, state}
  linescoreSource       object   {id, description, state}
  statsSource           object   {id, description, state}

REFS
  venue                 $ref     → /venues/{id}
  competitors           array    [{$ref, id, uid, type, order, winner, athlete{$ref}}]
  status                $ref     → /competitions/{id}/status
  broadcasts            $ref     → /competitions/{id}/broadcasts
  officials             $ref     → /competitions/{id}/officials
  details               $ref     → /competitions/{id}/plays  (play-by-play)
  links                 array    ESPN FightCenter fight-specific URL
```

---

### 2.4 Competition Status (Fight Result)

```
  clock                 float    Seconds elapsed in final round (e.g. 187.0 = 3:07)
  displayClock          string   "3:07"
  period                int      Round number fight ended (1–5)
  featured              bool

  type                  object
    id                  string   "1"=scheduled, "2"=in-progress, "3"=final
    name                string   "STATUS_SCHEDULED" | "STATUS_IN_PROGRESS" | "STATUS_FINAL"
    state               string   "pre" | "in" | "post"
    completed           bool
    description         string   "Final"
    detail              string   "Final"
    shortDetail         string   "Final"

  result                object   (only when completed)
    id                  int      Method ID
    name                string   "submission" | "ko" | "tko" | "decision" | "no_contest"
    displayName         string   "Submission" | "KO" | "TKO" | "Decision"
    description         string   Specific method: "Arm Triangle" | "Rear Naked Choke" | "Punches"
    displayDescription  string
    shortDisplayName    string   "Sub" | "KO" | "TKO" | "Dec"
    target              object   {id, name, description, displayDescription}
      name values: "head" | "body" | "leg"
```

---

### 2.5 Officials (Referee & Judges)

```
Per official item:
  id                    string   ESPN official ID
  firstName             string
  lastName              string
  position              object   {name, displayName, id}
    name values: "Referee" | "Judge"
    id: "42"=Referee, "41"=Judge
  order                 int      0=referee, 1-3=judges
```

---

### 2.6 Per-Fight Competitor Statistics (40+ fields)

```
STRIKING — DISTANCE
  totalStrikesAttempted       Total strikes thrown
  totalStrikesLanded          Total strikes connected
  sigStrikesAttempted         Significant strikes thrown
  sigStrikesLanded            Significant strikes connected
  sigDistanceHeadStrikesAttempted
  sigDistanceHeadStrikesLanded
  sigDistanceBodyStrikesAttempted
  sigDistanceBodyStrikesLanded
  sigDistanceLegStrikesAttempted
  sigDistanceLegStrikesLanded

STRIKING — CLINCH
  sigClinchHeadStrikesAttempted
  sigClinchHeadStrikesLanded
  sigClinchBodyStrikesAttempted
  sigClinchBodyStrikesLanded
  sigClinchLegStrikesAttempted
  sigClinchLegStrikesLanded

STRIKING — GROUND
  sigGroundHeadStrikesAttempted
  sigGroundHeadStrikesLanded
  sigGroundBodyStrikesAttempted
  sigGroundBodyStrikesLanded
  sigGroundLegStrikesAttempted
  sigGroundLegStrikesLanded

KNOCKDOWNS
  knockDowns

GRAPPLING
  takedownsAttempted
  takedownsLanded
  takedownsSlams
  takedownAccuracy            float (0.0–1.0)
  advances                    Position advances
  advanceToHalfGuard
  advanceToSide
  advanceToMount
  advanceToBack
  reversals
  submissions                 Submission attempts

CONTROL
  timeInControl               string "MM:SS"
  slamRate                    float

BREAKDOWN SUMMARIES
  targetBreakdownHead         Dominant target zone (0/1)
  targetBreakdownBody
  targetBreakdownLeg
  posBreakdownDistance        Dominant position (0/1)
  posBreakdownClinch
  posBreakdownGround

METADATA
  wallclock                   ISO 8601 timestamp of last update
```

---

### 2.7 Career Statistics (Athlete-Level Aggregates)

```
  takedownAccuracy      float    Career takedown accuracy %
  strikeLPM             float    Significant strikes landed per minute
  strikeAccuracy        float    Significant strike accuracy %
  takedownAvg           float    Avg takedowns per 15 minutes
  submissionAvg         float    Avg submission attempts per 15 minutes
  koPercentage          float    KO win percentage
  tkoPercentage         float    TKO win percentage
```

---

### 2.8 Career Record (Athlete-Level)

```
  summary               string   "22-13-0"
  displayValue          string   "22-13-0"
  value                 float    Win percentage

  stats[]
    wins                float
    losses              float
    draws               float
    noContests          float
    submissions         float    Sub wins
    submissionLosses    float    Sub losses
    tkos                float    TKO wins
    tkoLosses           float    TKO losses
    titleWins           float
    titleLosses         float
    titleDraws          float
```

---

### 2.9 Play-by-Play Event

```
  id                    string
  sequenceNumber        string
  type                  object   {id, text}  e.g. "Fight Open", "Round Start", "Fight End"
  awayScore             int
  homeScore             int
  period                object   {number}  — round number
  clock                 object   {value, displayValue}  — time in round
  scoringPlay           bool
  wallclock             string   ISO 8601 real-world timestamp
```

---

### 2.10 Venue

```
  id                    string
  guid                  string
  fullName              string   "Etihad Arena"
  address               object   {city, country}
  grass                 bool     (always false for MMA)
  indoor                bool     (always true for MMA)
```

---

### 2.11 Broadcast / Media

```
Broadcast item:
  type                  object   {id, shortName, longName, slug}
    slug values: "streaming" | "tv" | "ppv"
  channel               int
  slug                  string   "paramountplus" | "espn" | "espnplus" | "ufc-fight-pass"
  priority              int
  market                object   {id, type}  e.g. "National"
  lang                  string   "en"
  region                string   "us"
  media                 object   (inline + $ref)
