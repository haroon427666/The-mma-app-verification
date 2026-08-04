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
