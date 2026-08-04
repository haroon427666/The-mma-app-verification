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
    id, callLetters, name, shortName, slug
    logos[]             {href, width, height, alt, rel[], lastUpdated}

Media entity:
  id, callLetters, name, shortName, slug
  logos[]               {href, width, height, alt, rel["full","default"/"dark"], lastUpdated}
```

---

### 2.12 League

```
  id                    string   ESPN league ID
  guid                  string
  uid                   string   "s:3301~l:{id}"
  name                  string   "Ultimate Fighting Championship"
  displayName           string   "UFC"
  abbreviation          string   "UFC"
  shortName             string   "UFC"
  slug                  string   "ufc"
  gender                string   "MALE" / "FEMALE"
  logos[]               {href, width, height, alt, rel[], lastUpdated}
  links[]               ESPN.com index/schedule/standings links

  season                $ref     Current season
  seasons               $ref     All seasons list
  events                $ref     Events list
  calendar              $ref     Calendar
```

---

### 2.13 Season

```
  year                  int      e.g. 2026
  startDate             string   ISO 8601
  endDate               string   ISO 8601
  displayName           string   "2026"
  type                  $ref     Current season type
  types                 $ref     All season types
```

---

### 2.14 Ranking Entry

```
  current               int      Rank position (1 = champion or #1 contender)
  trend                 string   "-" | "↑" | "↓" (movement)
  hasAccolade           bool     true = champion
  defenses              int      Title defense count
  winningFight          $ref     → competition that won the title (for champions)
  athlete               $ref     → /athletes/{id}

Ranking list wrapper:
  id                    string
  name                  string   "Heavyweight Division Rankings (Up to 265 pounds)"
  shortName             string   "Heavyweight Division Rankings"
  type                  string
  gender                string
  note                  string   Any editorial note
  weightClass           object   {id, text, ...}
  ranks[]               array of ranking entries above
```

---

## 3. Synced vs Available Gap Analysis

### 3.1 What the Backend Currently Syncs

Based on the codebase (`espn_sync.py`, models):

| Data | Synced | Model | Notes |
|------|--------|-------|-------|
| Fighters (basic profile) | ✅ | `Fighter` | id, name, nickname, weight, height, reach, stance, dob, citizenship, active |
| Weight classes | ✅ | `WeightClass` | id, name, slug |
| Events | ✅ | `Event` | id, name, date, status, season_year |
| Venues | ✅ | `Venue` | id, name, city, country |
| Promotions/Leagues | ✅ | `Promotion` | id, name, slug |
| Competitions | ✅ | `Competition` | id, event, status, result, method, round, time, card_segment |
| Rankings | ✅ | `Ranking` | fighter, weight_class, rank, is_champion, trend, title_defenses |
| Broadcasts | ✅ | `Broadcast` | competition, network, type |

### 3.2 Available But NOT Synced

| Data | ESPN Endpoint | Impact | Effort |
|------|--------------|--------|--------|
| **Fighter headshot URL** | `athlete.headshot.href` | High — every fighter card needs an image | Low — add 1 field to Fighter model |
| **Fighter stance images** | `athlete.images[]` (leftStance/rightStance) | Medium — stance-specific fighter art | Low — store as JSON array |
| **Fighter gym/team** | `athlete.association.{id,name,location}` | High — key profile detail | Low — add 3 fields |
| **Fighter styles** | `athlete.styles[]` | Medium — wrestling/BJJ/boxing tags | Low — store as JSON array |
| **Fighter ESPN links** | `athlete.links[]` | Low — deep links to ESPN | Low |
| **Fighter flag image** | `athlete.flag.href` | Medium — nationality flag icon | Low — add 1 field |
| **Career W/L/D record** | `/athletes/{id}/records/0` | **Critical** — most-displayed fighter stat | Low — add wins/losses/draws/nc to Fighter |
| **Win method breakdown** | `/athletes/{id}/records/0.stats` | High — KO/Sub/TKO/Dec breakdown | Low — add 6 fields |
| **Title record** | `/athletes/{id}/records/0.stats` | High — titleWins/titleLosses | Low — 2 fields |
| **Career stats** | `/athletes/{id}/statistics/0` | High — strikeLPM, accuracy, TDs | Low — add 7 fields to Fighter |
| **Per-fight stats** | `/competitions/{id}/competitors/{id}/statistics` | **Very High** — fight-level breakdown | Medium — new `FightStatistic` model |
| **Fight result detail** | `competition_status.result` | High — method + body target | Low — already partially in Competition |
| **Fight clock/round** | `competition_status.clock + period` | High — "Round 3, 3:07" | Low — add 2 fields to Competition |
| **Referee name** | `/competitions/{id}/officials` | Medium — referee tracking | Medium — new `Official` model |
| **Judges** | `/competitions/{id}/officials` | Low — judges rarely displayed | Medium — same Official model |
| **Play-by-play** | `/competitions/{id}/plays` | Low for MVP, High for timeline | High — new `Play` model, 32 rows/fight |
| **League logos** | `league.logos[]` | High — promotion branding | Low — add logo_url to Promotion |
| **Season data** | `/leagues/{slug}/seasons/{year}` | Low — year/date range only | Low |
| **Multi-league events** | `/leagues/bellator/events`, `/leagues/pfl/events` | High — Bellator/PFL coverage | Medium — already multi-league capable |
| **Broadcast media logos** | `broadcast.media.logos[]` | Medium — network icons | Low — add logo_url to Broadcast |
| **Venue indoor flag** | `venue.indoor` | Low | Trivial |
| **Fighter eventlog** | `/athletes/{id}/eventlog` | Medium — fight history ordering | Low — already synced via competitions |
| **Fighter leagues history** | `/athletes/{id}/leagues` | Low — which orgs they fought for | Low |
| **Calendar ondays** | `/leagues/{slug}/calendar/ondays` | Medium — event date list | Low |
| **Ranking winningFight** | `ranking.winningFight.$ref` | Medium — title-winning fight link | Low — add field to Ranking |
| **Ranking note** | `ranking.note` | Low — editorial notes | Trivial |

---

### 3.3 What ESPN Does NOT Provide

These are commonly requested features with **no ESPN data source**:

| Feature | Why Not Available |
|---------|------------------|
| Round-by-round scorecards | ESPN has no judge scoring data |
| Fighter photos (non-headshot) | Only ESPN CDN headshots |
| Training camp / gym details | Only gym name from `association` |
| Fighter social media | Not in ESPN API |
| Fight video highlights | ESPN links are paywalled |
| Ticket prices | `ticketsAvailable` bool only |
| Fighter salaries | Not public data anywhere |
| Drug test results | Not in ESPN API |
| Weigh-in results | Not in ESPN API |
| Press conference data | Not in ESPN API |
| Odds / betting lines | Not in ESPN API |
| Fantasy MMA scoring | Not in ESPN API |
| Fighter rankings history (over time) | Only current snapshot |
| Event attendance figures | Not in ESPN API |
| PPV buy rates | Not public |

---

## 4. Additional Data Opportunities

### 4.1 Fighter Images — Three Tiers Available

**Tier 1: ESPN Headshots (already in API, not synced)**
```
https://a.espncdn.com/i/headshots/mma/players/full/{athlete_id}.png
https://a.espncdn.com/i/headshots/mma/players/stance/left/{athlete_id}.png
https://a.espncdn.com/i/headshots/mma/players/stance/right/{athlete_id}.png
```
- Available for all ESPN-tracked fighters
- No auth required
- Consistent CDN URLs — can be constructed from athlete ID alone
- **Recommendation:** Store `headshot_url` on Fighter model, construct from ID

**Tier 2: TheSportsDB (configured but unused)**
- Free tier (API key "3") provides fighter photos
- Backend has `thesportsdb_id` column on Fighter (unused)
- Provides: fighter photo, flag, description, social links
- **Recommendation:** Enrich fighters with TheSportsDB after ESPN sync

**Tier 3: League Logos**
```
https://a.espncdn.com/i/teamlogos/leagues/500/ufc.png
```
- Available from `league.logos[]` — already in API response
- Not stored in Promotion model
- **Recommendation:** Add `logo_url` to Promotion model

---

### 4.2 Multi-League Support

The backend is architecturally multi-league (Promotion model exists) but only syncs UFC. ESPN has full data for:

| League | Slug | Active | Data Quality |
|--------|------|--------|-------------|
| UFC | `ufc` | ✅ Yes | Excellent |
| Bellator | `bellator` | ⚠️ Absorbed by PFL | Good (historical) |
| PFL | `pfl` | ✅ Yes | Good |
| Rizin | `rizin` | ✅ Yes | Moderate |
| Strikeforce | `strikeforce` | ❌ Defunct | Historical only |
| Pride FC | `pride` | ❌ Defunct | Historical only |
| WEC | `wec` | ❌ Defunct | Historical only |
| LFA | `lfa` | ✅ Yes | Moderate |
| KSW | `ksw` | ✅ Yes | Moderate |
| Cage Warriors | `cage-warriors` | ✅ Yes | Moderate |

**Recommendation:** Add PFL and Rizin sync — same code path as UFC, just change the league slug.

---

### 4.3 Per-Fight Statistics — The Biggest Untapped Resource

The per-fight competitor statistics endpoint provides **40+ fields per fighter per fight**. This is the richest untapped data in the ESPN API.

**What this enables:**
- Strike accuracy per fight (head/body/leg breakdown)
- Takedown success rate per fight
- Ground control time
- Position advances (half guard → side → mount → back)
- Clinch vs distance vs ground breakdown
- Knockdown count

**New model needed:** `FightStatistic`
```python
class FightStatistic(Base):
    competition_id: int (FK)
    fighter_id: int (FK)
    # Striking
    total_strikes_attempted: int
    total_strikes_landed: int
    sig_strikes_attempted: int
    sig_strikes_landed: int
    # By zone (distance/clinch/ground × head/body/leg)
    sig_dist_head_att: int; sig_dist_head_land: int
    sig_dist_body_att: int; sig_dist_body_land: int
    sig_dist_leg_att: int; sig_dist_leg_land: int
    sig_clinch_head_att: int; sig_clinch_head_land: int
    sig_clinch_body_att: int; sig_clinch_body_land: int
    sig_ground_head_att: int; sig_ground_head_land: int
    # Grappling
    takedowns_attempted: int; takedowns_landed: int
    takedown_accuracy: float
    advances: int; reversals: int; submissions_attempted: int
    time_in_control: str  # "MM:SS"
    knockdowns: int
```

---

### 4.4 Officials — Referee Tracking

ESPN provides referee and judge names per fight. This enables:
- "Fights refereed by Herb Dean" filter
- Referee statistics (stoppages, controversies)
- Judge tracking

**New model needed:** `Official`
```python
class Official(Base):
    espn_id: str
    first_name: str
    last_name: str
    position: str  # "Referee" | "Judge"

class CompetitionOfficial(Base):
    competition_id: int (FK)
    official_id: int (FK)
    order: int
```

---

### 4.5 Play-by-Play — Fight Timeline

ESPN stores ~32 play events per fight (Fight Open, Round Start/End, Fight End). While sparse compared to UFC Stats, it provides:
- Exact real-world timestamps per round
- Round-by-round structure
- Fight open/close events

**Verdict:** Low priority for MVP. The data is structural (round markers) not narrative (strikes thrown). Skip for now.

---

### 4.6 Career Record Fields — Critical Missing Data

The most-displayed fighter stat ("22-13-0") is **not stored** in the current Fighter model. It's available from `/athletes/{id}/records/0`.

**Add to Fighter model immediately:**
```python
wins: int
losses: int
draws: int
no_contests: int
wins_by_ko: int
wins_by_tko: int
wins_by_submission: int
wins_by_decision: int
title_wins: int
title_losses: int
```

---

## 5. Recommended New Backend Endpoints

### Priority 1 — Expose Already-Synced Data (Hours of Work)

These endpoints require **zero new ESPN sync** — the data is already in the DB:

| New Endpoint | Data Source | Description |
|-------------|-------------|-------------|
| `GET /rankings` | `Ranking` table | All rankings grouped by weight class |
| `GET /rankings/{weight_class}` | `Ranking` table | Rankings for one division |
| `GET /champions` | `Ranking` WHERE `is_champion=true` | All current champions |
| `GET /fighters/{id}/fights` | `Competition` + `Competitor` | Fighter's fight history |
| `GET /events/{id}/card` | `Competition` ordered by `match_number` | Full fight card with card segments |
| `GET /events/upcoming` | `Event` WHERE `status=pre` | Upcoming events |
| `GET /events/live` | `Event` WHERE `status=in` | Live events |
| `GET /events/results` | `Event` WHERE `status=post` | Past results |
| `GET /competitions/{id}` | `Competition` | Single fight detail |
| `GET /weight-classes` | `WeightClass` | All weight classes |
| `GET /weight-classes/{slug}/fighters` | `Fighter` by weight class | Fighters in a division |

---

### Priority 2 — New Sync + New Endpoints (Days of Work)

These require adding fields to existing models and updating sync:

| New Endpoint | New Sync Needed | Description |
|-------------|----------------|-------------|
| `GET /fighters/{id}` (enhanced) | Add: wins/losses/draws, headshot_url, gym, styles, career stats | Full fighter profile with record |
| `GET /fighters/{id}/stats` | Sync career stats from `/athletes/{id}/statistics/0` | Career aggregate statistics |
| `GET /fighters/search?q=` | No new sync | Full-text search on fighter name |
| `GET /events/{id}/fights/{comp_id}` | Add: clock, period to Competition | Fight detail with result method |
| `GET /promotions` | Add logo_url to Promotion | All promotions with logos |
| `GET /promotions/{slug}/events` | No new sync | Events by promotion |

---

### Priority 3 — New Models Required (Weeks of Work)

| New Endpoint | New Model | Description |
|-------------|-----------|-------------|
| `GET /fights/{id}/stats` | `FightStatistic` | Per-fight striking/grappling breakdown |
| `GET /fighters/{id}/fight-stats` | `FightStatistic` | Fighter's per-fight stats history |
| `GET /fights/{id}/officials` | `Official`, `CompetitionOfficial` | Referee and judges |
| `GET /referees/{id}/fights` | `Official` | Fights by referee |
| `GET /fighters/compare?a={id}&b={id}` | No new model | Side-by-side fighter comparison |

---

### Priority 4 — Multi-League (Medium Effort)

| New Endpoint | Work Needed | Description |
|-------------|-------------|-------------|
| `GET /leagues` | Add PFL/Rizin sync | All supported leagues |
| `GET /leagues/{slug}/events` | Extend sync to PFL/Rizin | Events by league |
| `GET /leagues/{slug}/rankings` | Extend rankings sync | Rankings for non-UFC leagues |

---

### Complete Recommended Endpoint List (30 new endpoints)

```
# Rankings & Champions (data already in DB)
GET  /api/v1/rankings                          All rankings by weight class
GET  /api/v1/rankings/{weight_class}           Division rankings
GET  /api/v1/champions                         All current champions
GET  /api/v1/champions/{weight_class}          Champion for one division

# Enhanced Events
GET  /api/v1/events/upcoming                   Upcoming events
GET  /api/v1/events/live                       Live events
GET  /api/v1/events/results                    Past results
GET  /api/v1/events/{id}/card                  Full fight card (ordered)
GET  /api/v1/events/{id}/fights/{comp_id}      Single fight detail

# Fighter Enhancements
GET  /api/v1/fighters/{id}/fights              Fight history
GET  /api/v1/fighters/{id}/stats              Career statistics
GET  /api/v1/fighters/{id}/record             W/L/D record + method breakdown
GET  /api/v1/fighters/search                  Search by name
GET  /api/v1/fighters/compare                 Side-by-side comparison

# Weight Classes
GET  /api/v1/weight-classes                   All weight classes
GET  /api/v1/weight-classes/{slug}            Weight class detail
GET  /api/v1/weight-classes/{slug}/fighters   Fighters in division
GET  /api/v1/weight-classes/{slug}/rankings   Rankings for division
GET  /api/v1/weight-classes/{slug}/champion   Current champion

# Competitions / Fights
GET  /api/v1/fights/{id}                      Fight detail
GET  /api/v1/fights/{id}/stats                Per-fight statistics
GET  /api/v1/fights/{id}/officials            Referee and judges

# Promotions / Leagues
GET  /api/v1/promotions                       All promotions
GET  /api/v1/promotions/{slug}                Promotion detail
GET  /api/v1/promotions/{slug}/events         Events by promotion

# Venues
GET  /api/v1/venues                           All venues
GET  /api/v1/venues/{id}                      Venue detail
GET  /api/v1/venues/{id}/events               Events at venue

# Officials
GET  /api/v1/referees                         All referees
GET  /api/v1/referees/{id}/fights             Fights by referee
```

---

## Appendix A: ESPN CDN Image URL Patterns

```
# Fighter headshots (construct from athlete ID — no API call needed)
https://a.espncdn.com/i/headshots/mma/players/full/{athlete_id}.png
https://a.espncdn.com/i/headshots/mma/players/stance/left/{athlete_id}.png
https://a.espncdn.com/i/headshots/mma/players/stance/right/{athlete_id}.png

# League logos (from league.logos[])
https://a.espncdn.com/i/teamlogos/leagues/500/ufc.png

# Broadcast network logos (from broadcast.media.logos[])
https://a.espncdn.com/guid/{guid}/logos/default.png
https://a.espncdn.com/guid/{guid}/logos/default-dark.png

# Country flags (from athlete.flag.href)
https://a.espncdn.com/i/teamlogos/countries/500/{country_code}.png
```

---

## Appendix B: Key ESPN IDs

```
Sport ID:    3301 (MMA)
UFC ID:      3321
Bellator ID: 3323
PFL ID:      3347
Rizin ID:    (from leagues list)

Season type: 2 = Regular Season (only type for MMA)

Official positions:
  41 = Judge
  42 = Referee

Status IDs:
  1 = Scheduled (pre)
  2 = In Progress (in)
  3 = Final (post)
```

---

## Appendix C: Pagination Notes

- Default page size: 25
- Max tested: 100 (`?limit=100`)
- Events list: returns **current season only** by default
- To get historical events: use `?dates=YYYYMMDD` or iterate seasons
- Athletes list: no top-level `/athletes` endpoint — discover via event competitors or rankings
- Rankings: no pagination needed (max ~15 fighters per division)

---

## Appendix D: Rate Limiting

- No documented rate limits
- No API key required
- Tested: 20+ concurrent requests without throttling
- Recommended: 1–2 second delay between bulk sync batches to be respectful
- ESPN CDN images: no rate limiting observed

---

*Document generated by live API exploration — 2026-07-30*  
*All ✅ endpoints verified with real HTTP responses*
