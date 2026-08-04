# MMA Platform — Master Data Specification

> **Version:** 1.0 · **Prepared:** 2026-07-30
> **Purpose:** The authoritative map of *where every piece of data comes from, how it flows, where it lives, how long it's cached, and which features consume it.* Cross-references the **PRD** (`product-requirements.md`) via `FTR-xxx` IDs and the **Feature Registry** (`feature-registry.md`).
> **Grounded in real code:** models, scheduler cadences, sync functions, and config below are transcribed from the extracted backend zip — not assumed. ESPN endpoints are from the live-tested `espn-mma-api-reference.md`.
> **Sources policy:** ESPN public API (no key) is the only live source wired today. TheSportsDB (free key `"3"`) is **configured but unused**. No paid sources. No AI.

---

## Table of Contents
1. [Data Sources Overview](#1-data-sources-overview)
2. [Endpoint → Data Map (ESPN)](#2-endpoint--data-map-espn)
3. [Backend API Surface (current + planned)](#3-backend-api-surface-current--planned)
4. [Database ERD](#4-database-erd)
5. [Knowledge Graph Model](#5-knowledge-graph-model)
6. [Data Flow Diagram](#6-data-flow-diagram)
7. [Scheduler Jobs & Cadence](#7-scheduler-jobs--cadence)
8. [Cache Policy](#8-cache-policy)
9. [Fields Synced vs Available](#9-fields-synced-vs-available)

---

## 1. Data Sources Overview

| Source | Auth | Status in code | Powers |
|--------|------|----------------|--------|
| **ESPN public API** (`sports.core.api.espn.com/v2/sports/mma`) | None | ✅ Live — sole active source | Fighters, events, competitions, competitors, venues, promotions(leagues), weight classes, rankings, broadcasts, statistics |
| **ESPN CDN** (`a.espncdn.com/i/headshots/mma/players/full/{id}.png`) | None | 🟡 Constructable from `espn_id` — not yet stored | Fighter headshots (FTR-1201) |
| **TheSportsDB free** (`thesportsdb.com/api/v1/json`, key `"3"`) | Free key | 🌐 Configured (`THESPORTSDB_*`, `promotions.thesportsdb_id`) but **no client code** | Promotion logos (FTR-1202), fanart (FTR-1205), some legend bios |
| **Computed / in-DB aggregation** | — | 🔵 Planned (Phase 4) | Records, streaks, finish rates, division leaders (FTR-18xx, FTR-806/807) |
| **Manual curation** (small seed tables) | — | 🔵 Planned (Phase 5) | Hall of Fame, lineage, legendary fights (FTR-1706/1707/1708) |
| **On-device (client)** | — | 📱 Flutter-only | Local favorites, local reminders, offline cache, recent searches (FTR-15xx local, FTR-1401, FTR-22xx) |

**⛔ Not available from any free source** (excluded from scope): round-by-round scorecards, live play-by-play feed, full-fight video, betting odds, original editorial.

---

## 2. Endpoint → Data Map (ESPN)

Legend for **Data source**: `ESPN` (live) · `ESPN-CDN` (constructed URL) · `TSDB` (TheSportsDB, planned) · `Computed`.
"Synced?" = does the current `espn_sync.py` actually write these fields to the DB today.

### 2.1 League / Promotion

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `/leagues/{slug}` | Promotion identity | on event/rankings sync | 24h | `promotions` | Promotions, Promotion Detail | FTR-201,202 | ✅ name/slug/espn_id (via `sync_promotion`) · ❌ logo_url, country, website |
| `/leagues/{slug}/logos[]` | Promotion logo | on demand | 7d | `promotions.logo_url` | everywhere | FTR-204,1202 | ❌ available, not synced |
| `/leagues/{slug}/seasons` | Season list | manual/rare | 24h | (none yet) | Archive | FTR-1704 | ❌ not synced |
| `/leagues/{slug}/calendar/ondays` | Event dates | daily | 6h | (none yet) | Calendar | FTR-1301,1303 | ❌ not synced |

### 2.2 Rankings

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `/leagues/{slug}/rankings` | Ranking category index (24 categories) | **12h** (`rankings_ufc` job) | 6h | `rankings` | Rankings, Champions | FTR-501..507,601..606 | ✅ walked by `sync_rankings` via `get_rankings_index` |
| `/leagues/{slug}/rankings/{category}` | Per-category list w/ athlete refs, rank, trend, champion flag, defenses | 12h | 6h | `rankings` (+ resolves `fighters`) | Rankings, Champions, Fighter badge | FTR-501,504,603,109,110 | ✅ rank, trend, is_champion (`hasAccolade`), title_defenses, category, weight_class_id |

> **Critical gap:** this data is written every 12h but **no `GET /rankings` route exists**. Exposing it is the #1 Phase-2 task and unlocks FTR-5xx + FTR-6xx + Home/Fighter/WeightClass/Compare cross-refs.

### 2.3 Events

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `/leagues/{slug}/events` (paged) | Event discovery walk | **60 min** (`upcoming_{slug}`) | 5 min | `events`, `venues`, `promotions` | Events, Home, Calendar | FTR-301,302,306,310 | ✅ via `sync_league_events` (max 3 pages) |
| `/leagues/{slug}/events/{id}` | Full event detail | on walk + **3 min** live window | 5 min (2 min if live) | `events` (+ `competitions`, `broadcasts`) | Event Detail | FTR-302,303,304,311 | ✅ via `sync_event` |
| live re-fetch window | Re-sync events within ±window | **3 min** (`live_{slug}`, window 12h) | 60 s | `events`, `competitions` | Home banner, Event Detail | FTR-303 | ✅ via `sync_live_events` |

### 2.4 Competitions (fights) & Competitors

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `.../competitions/{id}` | Bout detail, card segment, match number, format | on event sync | 5 min | `competitions` | Fight Detail | FTR-401,402,403,311 | ✅ via `sync_competition` |
| `.../competitions/{id}/status` | Result: method/round/time, completed | on live sync | 60 s | `competitions.status/result_*` | Fight Detail | FTR-404,407 | ✅ via `_apply_competition_status` |
| `.../competitions/{id}/broadcasts` | Networks + logos (dedup to event) | on event sync | 30 min | `broadcasts` | Event Detail | FTR-304,1204 | ✅ network/region/lang/type/market/logo via `sync_event_broadcasts` |
| `.../competitions/{id}/officials` | Referee + judges | on event sync | 24h | 🔵 `officials` (new) | Fight Detail | FTR-408,2308 | ❌ available, not synced |
| `.../competitors/{aid}` | Winner flag, order, corner | on event sync | 5 min | `competitors` | Fight Detail | FTR-401,404 | ✅ outcome/corner via `_resolve_competitor_entry` |
| `.../competitors/{aid}/statistics` | 40+ per-fight stats | on event sync (finished bouts) | 24h | `statistics` | Fight Stats | FTR-405,802,811,812 | 🟡 core stats synced via `sync_fighter_statistics`; per-fight strike-zone detail available, not fully synced |

### 2.5 Athletes / Fighters

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `/athletes/{id}` | Full profile | on fight sync + **24h** refresh (`fighter_sync`) | 1h | `fighters`, `weight_classes` | Fighter Profile | FTR-102,103,104,113 | ✅ name, nickname, nationality, physicals, stance, W/L/D via `sync_fighter` |
| `/athletes/{id}/statistics/0` | Career aggregates | 24h | 1h | (career stats) | Stats | FTR-105,801,803,804,805 | ✅ via `get_athlete_statistics` |
| `/athletes/{id}/records/0` | W/L/D + method breakdown | 24h | 1h | `fighters.wins/losses/draws` | Fighter, Records | FTR-104,111 | 🟡 W/L/D synced; method breakdown available, not stored |
| `/athletes/{id}/eventlog` | Fight history | 24h | 1h | `competitors`/`competitions` | Fighter history | FTR-106,1703 | ✅ drives history |
| headshot URL (ESPN-CDN) | `.../players/full/{espn_id}.png` | derive on read | 7d | `fighters.headshot_url` | everywhere | FTR-108,1201 | ❌ column exists, not populated |
| `/athletes/{id}/leagues` | Orgs competed in | rare | 24h | (none) | Fighter | FTR-209 | ❌ not synced |

### 2.6 Venues, Weight Classes

| ESPN endpoint | Purpose | Cadence | Cache TTL | DB tables | Screens | Features (FTR) | Synced? |
|---|---|---|---|---|---|---|---|
| `/leagues/{slug}/venues/{id}` | Venue detail | as side-effect of event sync | 24h | `venues` | Venue, Event Detail | FTR-310,2303 | ✅ via `_sync_venue` (name/city/country) |
| weightClass payloads (athlete + ranking) | Divisions | side-effect | 24h | `weight_classes` | Weight Classes | FTR-701,702,706 | ✅ via `_upsert_weight_class` (merge-safe gender) |

---

## 3. Backend API Surface (current + planned)

### 3.1 Implemented today (15 routes, verified in `router.py`)

| Route | Serves | Feeds features |
|---|---|---|
| `GET /api/v1/fighters?q=` | fighter search (paged) | FTR-101,901 |
| `GET /api/v1/fighters/{id}` | full profile | FTR-102,103,104 |
| `GET /api/v1/fighters/{id}/next-fight` | next bout | FTR-107,1508,1602 |
| `GET /api/v1/fighters/{id}/statistics` | career stats | FTR-105,801,803,804,805 |
| `GET /api/v1/fighters/{id}/fights` | fight history (paged) | FTR-106,1703,120 |
| `GET /api/v1/events?promotion_id=` | upcoming events (paged) | FTR-301,306,203 |
| `GET /api/v1/events/{id}` | full card + broadcasts | FTR-302,303,304,311 |
| `GET /api/v1/promotions?q=` | promotions list/search | FTR-201,902 |
| `GET /api/v1/promotions/{id}` | promotion detail | FTR-202 |
| `GET /api/v1/competitions/{id}` | bout detail | FTR-401,402,403,404,405 |
| `GET /api/v1/venues` | venues list | FTR-2303 |
| `GET /api/v1/venues/{id}` | venue detail | FTR-310 |
| `GET /api/v1/weight-classes` | divisions list | FTR-701,702,706 |
| `GET /api/v1/health` | liveness | infra |
| `GET /api/v1/health/db` | DB readiness | infra |

### 3.2 Planned routes (grouped by phase — data already available)

**Phase 2 (data already synced — expose only):**
| Route | Serves | Features |
|---|---|---|
| `GET /rankings?promotion=&category=` | ranking lists | FTR-501..507,509,704,2306 |
| `GET /champions?promotion=` | current champions | FTR-601..606,705 |
| `GET /events?status=FINAL|LIVE|SCHEDULED` | status filter + past events | FTR-305,307,1701,1702 |
| `GET /fighters?weight_class=` | division roster | FTR-115,703 |
| `GET /promotions/{id}/roster` | fighters in org | FTR-205 |
| `GET /search?q=` (unified) | cross-entity search | FTR-903,904 |
| `GET /events?date_from=&date_to=` | date range | FTR-308,1303 |

**Phase 4 (new computed/aggregate):**
| Route | Serves | Features |
|---|---|---|
| `GET /fighters/{id}/records` | streaks, finish rate, method breakdown | FTR-111,112,1801,1802 |
| `GET /stats/leaders?metric=&division=` | division/all-time leaders | FTR-806,807,808,1804,1806 |
| `GET /competitions/{id}/officials` | referee/judges | FTR-408,2308 |
| `GET /competitions/{id}/statistics` | per-fight strike/grapple detail | FTR-409,410,811,812 |
| `GET /compare?a=&b=` | compare payload incl. common opponents | FTR-1905,1906,1907 |

**Phase 5 (optional account layer):**
| Route | Serves | Features |
|---|---|---|
| `POST /auth/*` (Supabase-verified JWT) | sign in/up | FTR-2001 |
| `GET/POST/DELETE /me/follows/fighters` | server follows | FTR-1506 |
| `GET/POST/DELETE /me/follows/promotions` | server follows | FTR-1507 |
| `GET/POST /me/reminders` | server reminders | FTR-1405 |
| `GET /me/notifications` | in-app inbox | FTR-1407,1408 |
| `POST /me/push-token` | FCM registration | FTR-1406,2007 |

---

## 4. Database ERD

15 tables today (16 models — `Notification` shares the reminder module). All use UUID PKs + `created_at`/`updated_at` (see `mixins.py`). Verified from `alembic/versions/7affa1216de0_initial_schema.py` + two follow-up migrations.

```
                         ┌──────────────┐
                         │  promotions  │  (league)
                         │──────────────│
                         │ id (PK)      │
                         │ name, slug   │
                         │ espn_id      │
                         │ espn_slug    │
                         │ thesportsdb_id (unused) │
                         │ logo_url ○   │
                         │ country ○    │
                         │ website ○    │
                         └──────┬───────┘
                                │ 1
                                │
                                │ N
┌──────────────┐         ┌──────▼───────┐         ┌──────────────┐
│    venues    │ 1     N │    events    │ N     1 │ weight_classes│
│──────────────│◄────────│──────────────│         │──────────────│
│ id (PK)      │ venue_id│ id (PK)      │         │ id (PK)      │
│ name,city    │         │ espn_id      │         │ espn_id      │
│ country      │         │ name,short   │         │ name (uniq)  │
│ espn_id      │         │ start_time   │         │ max_weight_lbs│
└──────────────┘         │ status       │         │ gender ○     │
                         │ promotion_id │         └──────┬───────┘
                         │ venue_id ○   │                │
                         └──┬────────┬──┘                │ (SET NULL refs)
                       1 N  │        │ 1 N               │
              ┌─────────────▼──┐  ┌──▼───────────┐       │
              │  broadcasts    │  │ competitions │◄──────┤
              │────────────────│  │──────────────│ wc_id │
              │ id (PK)        │  │ id (PK)      │       │
              │ event_id       │  │ espn_id      │       │
              │ network        │  │ card_segment │       │
              │ region,lang    │  │ match_number │       │
              │ broadcast_type │  │ status,state │       │
              │ market_type    │  │ completed    │       │
              │ logo_url       │  │ result_method│       │
              │ UQ(event,net,  │  │ result_detail│       │
              │    region,lang)│  │ result_round │       │
              └────────────────┘  │ result_time  │       │
                                  │ event_id     │       │
                                  │ weight_class_id ○────┘
                                  └──────┬───────┘
                                    1    │  N
                                  ┌──────▼────────┐        ┌──────────────┐
                                  │  competitors  │ N    1 │   fighters   │
                                  │───────────────│◄───────│──────────────│
                                  │ id (PK)       │fighter_│ id (PK)      │
                                  │ competition_id│  id    │ espn_id (uq) │
                                  │ fighter_id    │        │ full_name    │
                                  │ corner        │        │ nickname     │
                                  │ outcome       │        │ nationality  │
                                  └──────┬────────┘        │ headshot_url ○│
                                    1    │ N               │ height/weight/│
                                  ┌──────▼────────┐        │ reach/stance ○│
                                  │  statistics   │        │ wins/losses/ │
                                  │───────────────│        │ draws        │
                                  │ id (PK)       │        │ weight_class_id ○│
                                  │ competitor_id │        └──────┬───────┘
                                  │ name          │               │
                                  │ display_name  │               │ N
                                  │ value         │        ┌──────▼───────┐
                                  └───────────────┘        │   rankings   │
                                                           │──────────────│
                                                           │ id (PK)      │
                                                           │ fighter_id   │
                                                           │ promotion_id │
                                                           │ weight_class_id ○│
                                                           │ category     │
                                                           │ rank         │
                                                           │ trend ○      │
                                                           │ is_champion  │
                                                           │ title_defenses ○│
                                                           │ UQ(promo,cat,rank)│
                                                           └──────────────┘

   USER LAYER (tables exist, NO endpoints, NO auth — Phase 5):
   ┌──────────┐   ┌──────────────────┐   ┌───────────────────┐   ┌───────────┐   ┌───────────────┐
   │  users   │ 1 │ fighter_follows  │   │ promotion_follows │   │ reminders │   │ notifications │
   │──────────│──►│ user_id,fighter_id│  │ user_id,promo_id  │   │ user_id,  │   │ user_id,title,│
   │ id (PK)  │   │ UQ(user,fighter) │   │ UQ(user,promo)    │   │ event_id, │   │ body,read     │
   │ email    │   └──────────────────┘   └───────────────────┘   │ minutes_  │   └───────────────┘
   │ display_ │                                                   │ before,sent│
   │ name     │                                                   └───────────┘
   │ push_token│
   └──────────┘

  ○ = nullable    UQ = unique constraint    (SET NULL) = ondelete behavior
```

**Notable design decisions (from model docstrings):**
- `Statistic` is name/value rows (not fixed columns) — ESPN stat categories grow; avoids a migration per new stat.
- `Ranking` rows are **cleared + reinserted per (promotion, category)** each sync (like Statistic) — rankings are a small fully-replaced list.
- `Broadcast` is stored at **Event** level (deduped across the event's competitions), though ESPN scopes it per-competition.
- `Competitor` is a first-class join entity (carries `corner`, `outcome`), not a bare association table.
- `User.id` is intended to equal the **Supabase Auth** UUID; **no password stored** (auth delegated). Config also carries JWT `SECRET_KEY`/`ALGORITHM` — reconcile the auth approach in Phase 5 before building.

---

## 5. Knowledge Graph Model

All relationships are plain relational joins — **no AI**. This is the traversal layer behind Module 24 (FTR-23xx).

```
                          ┌───────────────┐
              ┌──────────►│   PROMOTION   │◄──────────┐
              │           └──┬────────┬───┘           │
              │ ranks in     │ hosts  │ ranks         │ competed in
              │              ▼        ▼               │
        ┌─────┴─────┐   ┌────────┐  ┌─────────┐  ┌────┴──────┐
        │  RANKING  │──►│ EVENT  │  │ RANKING │  │  FIGHTER  │
        │ (rank,    │   │ (card) │  │ (champ) │  │ (athlete) │
        │  champ)   │   └───┬────┘  └────┬────┘  └────┬──────┘
        └─────┬─────┘       │ held at    │ #1 =        │ appears as
              │ of division │            ▼             ▼
              ▼             ▼        ┌─────────┐  ┌────────────┐
        ┌───────────┐  ┌────────┐   │CHAMPION │  │ COMPETITOR │
        │WEIGHT CLASS│  │ VENUE  │   │(fighter)│  │(one bout   │
        │(division) │  └────────┘   └─────────┘  │ appearance)│
        └─────┬─────┘                            └─────┬──────┘
              │ categorizes                             │ in
              ▼                                         ▼
        ┌───────────┐        broadcast on        ┌────────────┐
        │COMPETITION│◄───────┌──────────┐───────►│ STATISTICS │
        │  (bout)   │        │BROADCAST │        │(per bout)  │
        │           │───────►└──────────┘        └────────────┘
        │           │ officiated by (🌐 planned)
        │           │───────►┌──────────┐
        └───────────┘        │ OFFICIAL │ (referee/judges)
                             └──────────┘

  Traversal examples (features):
   FIGHTER ─competed in→ COMPETITION ─part of→ EVENT ─at→ VENUE            (FTR-2301,2303)
   EVENT ─has→ COMPETITION ─has→ COMPETITOR ─is→ FIGHTER                   (FTR-2302)
   WEIGHT CLASS ─has→ RANKING ─#1→ CHAMPION; ─lists→ FIGHTERS              (FTR-2305,705,703)
   PROMOTION ─publishes→ RANKING ─of→ FIGHTER ─next→ COMPETITION           (FTR-2306,2304)
   FIGHTER ↔ FIGHTER via shared COMPETITION = common opponents / H2H       (FTR-117,2307)
   OFFICIAL ─officiated→ COMPETITION list                                  (FTR-2308, 🌐)
```

---

## 6. Data Flow Diagram

```
   ┌────────────────────┐        ┌──────────────────────────────────────┐
   │  ESPN Public API   │        │        TheSportsDB (free, 🌐 planned) │
   │ (no key, HTTP GET) │        │        logos / fanart                  │
   └─────────┬──────────┘        └───────────────────┬────────────────────┘
             │  httpx (ESPNClient, per-job instance)  │  (future client)
             ▼                                        ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  SCHEDULER (APScheduler, 4 tiers)  app/tasks/scheduler.py              │
   │   live(3m) · upcoming(60m) · fighters(24h) · rankings(12h)            │
   │   each job: new Session + new ESPNClient, closed after run            │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    │ idempotent upserts (espn_sync.py)
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  PostgreSQL (Supabase in prod / Docker in dev)  15 tables, 3 migrations│
   │   repositories/*  ← the ONLY layer that touches SQL                    │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  CACHE (Redis)  ⚠ NOT built yet │  ← Production Readiness Phase 1
                    │  cache-aside at service/route  │     (interrupted at design)
                    │  boundary; fakeredis in tests  │
                    └───────────────┬───────────────┘
                                    │ services/*  ← business logic
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  FastAPI  (thin routes → services → repositories)                     │
   │   /api/v1/*  Pydantic schemas at the edges                            │
   └───────────────────────────────┬──────────────────────────────────────┘
                                    │ JSON over HTTPS
                                    ▼
   ┌──────────────────────────────────────────────────────────────────────┐
   │  FLUTTER APP                                                           │
   │   local storage: favorites, reminders, offline cache, recent searches │
   │   (device-local layer = MVP; no account needed)                       │
   └──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Scheduler Jobs & Cadence

Transcribed from `app/tasks/scheduler.py` + `app/core/config.py`. Job IDs are per-league (`SYNC_LEAGUES=["ufc"]`) except fighter refresh (global).

| Job ID | Function | Trigger | Interval (default) | What it syncs | Sync fn | Feeds |
|---|---|---|---|---|---|---|
| `live_{slug}` | `run_live_sync` | interval | **3 min** (window 12h) | events in live window + their competitions/status | `sync_live_events` | FTR-303,404 |
| `upcoming_{slug}` | `run_upcoming_sync` | interval | **60 min** (max 3 pages) | full event walk → events, venues, broadcasts, competitions | `sync_league_events` | FTR-301,302,304,310 |
| `fighter_sync` | `run_fighter_sync` | interval | **24 h** | refresh every known fighter's profile/stats | `sync_known_fighters` | FTR-102..106 |
| `rankings_{slug}` | `run_rankings_sync` | interval | **12 h** | all ranking categories | `sync_rankings` | FTR-501..507,601..606 |

**Scheduler invariants (must preserve in Phase 1 hardening):**
- `coalesce=True`, `max_instances=1`, `misfire_grace_time=60`, `ThreadPoolExecutor(max_workers=4)`.
- **Each job opens/closes its own `Session` + `ESPNClient`** (never shared across threads).
- `next_run_time=now` forces first run immediately (interval trigger otherwise waits one interval).
- Venues/weight-classes/broadcasts have **no standalone job** — synced as side effects of event/fighter jobs.
- **No standalone job for rankings→endpoint** — data lands in DB but isn't served (Phase 2 gap).

**Phase 1 open item:** move APScheduler to a Redis job store / separate process so multi-worker deployments don't double-run jobs (config comment already anticipates Redis as "caching + APScheduler job store").

---

## 8. Cache Policy

⚠️ **No cache code exists yet** — Redis is a dependency + `REDIS_URL` setting + compose service only. This table is the *target* policy for Production Readiness Phase 1. Implement as cache-aside at the **service/route boundary** (not in repositories), DI-overridable, with `fakeredis` in tests and graceful degradation when Redis is down.

| Data | Route(s) | TTL | Invalidate on | Rationale |
|---|---|---|---|---|
| Fighter detail | `/fighters/{id}` | 1h | fighter_sync writes | slow-changing |
| Fighter stats | `/fighters/{id}/statistics` | 1h | fighter_sync | slow-changing |
| Fight history | `/fighters/{id}/fights` | 1h | live/event sync touching fighter | changes only after fights |
| Next fight | `/fighters/{id}/next-fight` | 15 min | upcoming/live sync | schedule can shift |
| Event list | `/events` | 5 min | upcoming sync | discovery churn |
| Event detail | `/events/{id}` | 5 min (**60 s if live**) | live sync | live results must surface fast |
| Competition detail | `/competitions/{id}` | 5 min (60 s if live) | live sync | same |
| Rankings | `/rankings` (planned) | 6h | rankings_sync (12h) | published on ESPN's cadence |
| Champions | `/champions` (planned) | 6h | rankings_sync | same |
| Promotions / venues / weight-classes | list routes | 24h | rare | near-static reference data |
| Search results | `/fighters?q=`, `/search` | 5 min | — | short TTL, high variety |

**Client-side (Flutter) caching** (FTR-22xx): last-viewed entities in local store; stale-while-revalidate UX; optional backend `ETag`/`Cache-Control` headers (FTR-2205) pair naturally with the Redis phase.

---

## 9. Fields Synced vs Available

High-value ESPN fields **available but not yet written** (ordered by ROI). Full inventory in `espn-mma-api-reference.md §3`.

| Field / data | ESPN source | Target column/table | Effort | Feature |
|---|---|---|---|---|
| **Fighter headshot** | construct from `espn_id` | `fighters.headshot_url` (exists!) | Trivial | FTR-108,1201 |
| **Method breakdown (KO/Sub/Dec)** | `/athletes/{id}/records/0` | new columns or computed | Small | FTR-111 |
| **Promotion logo** | `/leagues/{slug}/logos[]` or TSDB | `promotions.logo_url` (exists!) | Small | FTR-204,1202 |
| **Officials (ref/judges)** | `.../competitions/{id}/officials` | 🔵 new `officials` table | Medium | FTR-408,2308 |
| **Per-fight strike-zone stats** | `.../competitors/{aid}/statistics` | `statistics` (extend rows) | Medium | FTR-409,410,811,812 |
| **Broadcast network logos** | `.../broadcasts` media / `/media/{id}` | `broadcasts.logo_url` (exists!) | Small | FTR-1204 |
| **Seasons / calendar** | `/leagues/{slug}/seasons`, `/calendar/ondays` | 🔵 new table | Medium | FTR-1704,1303 |
| **Multi-league (PFL/Bellator/…)** | same patterns, other slugs | existing tables | Medium (needs per-league verification) | FTR-209 |
| **Fighter styles / association** | `/athletes/{id}` styles/association | new columns | Small | FTR-113,114 |

**Already fully synced (no action):** fighter identity/physicals/W-L-D, career stats, fight history, events, competitions + status/result, competitors (corner/outcome), venues, promotions (id/name/slug), weight classes, broadcasts (network/region/lang/type/market/logo), rankings (rank/trend/champion/defenses/category).

---

*Companion documents: `product-requirements.md` (what to build) · `feature-registry.md` (status/effort rollups) · `espn-mma-api-reference.md` (raw endpoint/field reference) · `assessment.md` + `continuation-prompt.md` (Production Readiness state).*
