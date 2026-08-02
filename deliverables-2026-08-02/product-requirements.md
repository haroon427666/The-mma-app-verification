# MMA Platform — Master Product Requirements Document (PRD)

> **Version:** 1.0 · **Prepared:** 2026-07-30
> **Scope:** The single source of truth for *what* the product does. Every capability has a stable **Feature ID** (`FTR-xxx`) referenced by the companion **Data Specification** (`data-specification.md`) and **Feature Registry** (`feature-registry.md`).
> **Grounded in real code:** the backend zip was extracted and read (15 live endpoints, 16 models/15 tables, a 4-tier scheduler). Status flags below reflect the *actual* codebase, not aspiration.
> **Hard constraints (locked):** ❌ No AI (predictions/chat/summaries/anything) · ❌ No betting/odds · ❌ No fantasy · ❌ No public comments/social network · ❌ No premium/subscription · ❌ No paid APIs or services.

---

## How to read this document

**Priority**
- **P0** — MVP. Ships in the first public build.
- **P1** — v1.0. First major update after MVP.
- **P2** — v2.0. Depth/breadth once core is proven.
- **P3** — Future / optional (often the account+push layer or curated content).

**Status** (verified against the extracted codebase)
- **Implemented** — endpoint/route exists and is tested today.
- **Backend Ready** — the data is already synced into the DB, but **no API route serves it yet** (fast to expose).
- **Planned** — needs new backend work (endpoint and/or table) not yet present.
- **Client-only** — no backend change; pure Flutter.

**Phase** maps to the build roadmap (see `feature-master-plan.md`):
1. Finish Production Readiness · 2. Expose already-synced data · 3. Client-first features · 4. Computed/aggregate · 5. Optional accounts + push + curated.

**Ground-truth reminder (drives every Status flag):**
- ✅ **Live endpoints (15):** fighters (search/detail/next-fight/statistics/fights), events (list/detail), promotions (list/detail), competitions (detail), venues (list/detail), weight-classes (list), health, health/db.
- 🟡 **Synced but NOT exposed:** `rankings` table (populated every 12h) — no `/rankings` or `/champions` route yet. This is the single biggest "Backend Ready" cluster.
- 🔵 **Scaffolded, empty:** `users`, `fighter_follows`, `promotion_follows`, `reminders`, `notifications` — tables + config (Supabase Auth, JWT settings, FCM field) exist, but **no auth and no routes**.
- 🌐 **Configured but unused:** TheSportsDB (base URL + free key `"3"` + `promotions.thesportsdb_id`) — no client code calls it.

---

## Module Index

| # | Module | Prefix | Feature count |
|---|--------|--------|---------------|
| 1 | Home / Dashboard | FTR-0xx | 12 |
| 2 | Fighters | FTR-1xx | 22 |
| 3 | Organizations (Promotions) | FTR-2xx | 11 |
| 4 | Events | FTR-3xx | 16 |
| 5 | Fights (Competitions) | FTR-4xx | 14 |
| 6 | Rankings | FTR-5xx | 10 |
| 7 | Champions | FTR-6xx | 8 |
| 8 | Weight Classes | FTR-7xx | 8 |
| 9 | Statistics Hub | FTR-8xx | 12 |
| 10 | Search | FTR-9xx | 9 |
| 11 | Discover | FTR-10xx | 8 |
| 12 | News | FTR-11xx | 6 |
| 13 | Media / Images | FTR-12xx | 7 |
| 14 | Calendar | FTR-13xx | 7 |
| 15 | Notifications | FTR-14xx | 10 |
| 16 | Favorites | FTR-15xx | 9 |
| 17 | Personalized Feed | FTR-16xx | 7 |
| 18 | Historical Archive | FTR-17xx | 8 |
| 19 | Records & Achievements | FTR-18xx | 11 |
| 20 | Compare Fighters | FTR-19xx | 8 |
| 21 | User Account | FTR-20xx | 10 |
| 22 | Sharing | FTR-21xx | 7 |
| 23 | Offline | FTR-22xx | 7 |
| 24 | Knowledge Graph | FTR-23xx | 10 |

**Total user-facing capabilities catalogued: 247** (see `feature-registry.md` for the rollups by status/priority/phase).

---

## Navigation Flow (screen map)

```
                                  ┌──────────────┐
                                  │  Home / Feed │ (FTR-0xx, FTR-16xx)
                                  └──────┬───────┘
        ┌────────────┬────────────┬─────┴──────┬────────────┬─────────────┐
        ▼            ▼            ▼            ▼            ▼             ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Events  │  │ Fighters│  │Rankings │  │ Discover│  │ Search  │  │Calendar │
   │ (3xx)   │  │  (1xx)  │  │  (5xx)  │  │ (10xx)  │  │  (9xx)  │  │ (13xx)  │
   └────┬────┘  └────┬────┘  └────┬────┘  └─────────┘  └─────────┘  └─────────┘
        ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐
   │  Event  │  │ Fighter │  │ Champions│
   │  Detail │  │ Profile │  │  (6xx)   │
   │  (3xx)  │  │  (1xx)  │  └──────────┘
   └────┬────┘  └────┬────┘
        ▼            ├───────────────┬──────────────┐
   ┌─────────┐       ▼               ▼              ▼
   │  Fight  │  ┌─────────┐   ┌────────────┐  ┌──────────┐
   │ Detail  │  │ Compare │   │ Statistics │  │ Records/ │
   │  (4xx)  │  │ (19xx)  │   │   (8xx)    │  │ Achieve  │
   └────┬────┘  └─────────┘   └────────────┘  │  (18xx)  │
        ▼                                       └──────────┘
   ┌──────────┐
   │  Fight   │
   │  Stats   │  (8xx per-fight)
   └──────────┘

  Cross-cutting overlays (reachable from most screens):
   Favorites (15xx) · Notifications (14xx) · Sharing (21xx) · Account (20xx) · Offline (22xx)
  Relationship jumps (Knowledge Graph, 23xx) connect Fighter ↔ Event ↔ Venue ↔ Promotion ↔ WeightClass ↔ Ranking ↔ Official.
```

---

## Module 1 — Home / Dashboard  (FTR-0xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-001 | Upcoming events list | As a user, I want the next cards at a glance so I know what's coming. | P0 | Home | FTR-301 | 3 | Implemented |
| FTR-002 | Next big event hero card | As a user, I want the marquee event featured so I can't miss it. | P0 | Home | FTR-301 | 3 | Implemented |
| FTR-003 | Live event banner | As a user, I want a live indicator when a card is in progress. | P0 | Home | FTR-303 | 3 | Implemented |
| FTR-004 | Latest results strip | As a user, I want recent results so I stay current. | P1 | Home | FTR-305 | 2 | Backend Ready |
| FTR-005 | Top-ranked fighters row | As a user, I want to see who's #1 across divisions. | P1 | Home | FTR-501 | 2 | Backend Ready |
| FTR-006 | Current champions strip | As a user, I want all current champs surfaced on home. | P1 | Home | FTR-601 | 2 | Backend Ready |
| FTR-007 | "Your fighters" row | As a user, I want my followed fighters' next fights up top. | P1 | Home | FTR-1601 | 3 | Client-only |
| FTR-008 | Featured promotions row | As a user, I want quick entry into UFC/PFL/etc. | P2 | Home | FTR-201 | 3 | Implemented |
| FTR-009 | Pull-to-refresh | As a user, I want to force-refresh home content. | P0 | Home | — | 3 | Client-only |
| FTR-010 | Home layout personalization | As a user, I want to reorder home sections. | P2 | Home, Settings | — | 3 | Client-only |
| FTR-011 | Theme (light/dark) | As a user, I want a dark theme for late-night browsing. | P1 | Global | — | 3 | Client-only |
| FTR-012 | Home skeleton/loading states | As a user, I want graceful loading instead of blank screens. | P0 | Home | — | 3 | Client-only |

---

## Module 2 — Fighters  (FTR-1xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-101 | Fighter search by name | As a user, I want to find any fighter fast. | P0 | Search, Fighters | — | (done) | Implemented |
| FTR-102 | Fighter profile — identity | As a user, I want name, nickname, nationality, photo. | P0 | Fighter Profile | FTR-1201 | (done) | Implemented |
| FTR-103 | Fighter physicals | As a user, I want height/weight/reach/stance. | P0 | Fighter Profile | — | (done) | Implemented |
| FTR-104 | Fighter record (W-L-D) | As a user, I want the win/loss/draw record. | P0 | Fighter Profile | — | (done) | Implemented |
| FTR-105 | Career statistics | As a user, I want striking/grappling career stats. | P0 | Fighter Profile, Stats | — | (done) | Implemented |
| FTR-106 | Full fight history | As a user, I want every past bout listed. | P0 | Fighter Profile | — | (done) | Implemented |
| FTR-107 | Next scheduled fight | As a user, I want to know when they fight next. | P0 | Fighter Profile | FTR-301 | (done) | Implemented |
| FTR-108 | Headshot image | As a user, I want the fighter's photo. | P0 | everywhere | FTR-1201 | 2 | Backend Ready |
| FTR-109 | Current ranking badge | As a user, I want their current rank shown on the profile. | P1 | Fighter Profile | FTR-501 | 2 | Backend Ready |
| FTR-110 | Champion indicator | As a user, I want a belt icon if they hold a title. | P1 | Fighter Profile | FTR-601 | 2 | Backend Ready |
| FTR-111 | Win-method breakdown (KO/Sub/Dec %) | As a user, I want to see how they win. | P1 | Fighter Profile | FTR-106 | 4 | Planned |
| FTR-112 | Current/recent win streak | As a user, I want their form at a glance. | P1 | Fighter Profile | FTR-106 | 4 | Planned |
| FTR-113 | Fighting style / stance tags | As a user, I want style descriptors (wrestler, striker). | P2 | Fighter Profile | FTR-1201 | 2 | Planned |
| FTR-114 | Gym / association | As a user, I want to know their camp. | P2 | Fighter Profile | 🌐 ESPN association | 2 | Planned |
| FTR-115 | Fighters in a division | As a user, I want to browse everyone at 155 lbs. | P1 | Weight Class, Fighters | FTR-701 | 2 | Backend Ready |
| FTR-116 | Head-to-head vs an opponent | As a user, I want their record against a specific foe. | P2 | Fighter Profile, Compare | FTR-106 | 4 | Planned |
| FTR-117 | Common opponents | As a user, I want fighters they've both faced. | P2 | Compare | FTR-106 | 4 | Planned |
| FTR-118 | Title history / reigns | As a user, I want their championship history. | P2 | Fighter Profile | 🌐 curation | 5 | Planned |
| FTR-119 | Fighter media gallery | As a user, I want more photos of the fighter. | P3 | Fighter Profile | 🌐 TheSportsDB | 5 | Planned |
| FTR-120 | Fighter career timeline | As a user, I want a chronological career view. | P2 | Fighter Profile | FTR-106 | 3 | Client-only |
| FTR-121 | Follow this fighter | As a user, I want to follow a fighter for updates. | P1 | Fighter Profile | FTR-1501 | 3 | Client-only |
| FTR-122 | Share fighter profile | As a user, I want to share a fighter card. | P1 | Fighter Profile | FTR-2101 | 3 | Client-only |

---

## Module 3 — Organizations / Promotions  (FTR-2xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-201 | List/search promotions | As a user, I want to browse organizations. | P0 | Promotions | — | (done) | Implemented |
| FTR-202 | Promotion detail | As a user, I want a promotion's info page. | P0 | Promotion Detail | — | (done) | Implemented |
| FTR-203 | Events by promotion | As a user, I want a promotion's upcoming cards. | P0 | Promotion Detail | FTR-301 | (done) | Implemented |
| FTR-204 | Promotion logo/branding | As a user, I want the org's logo. | P1 | everywhere | 🌐 TheSportsDB | 2 | Planned |
| FTR-205 | Roster by promotion | As a user, I want fighters who compete there. | P2 | Promotion Detail | FTR-106 | 4 | Planned |
| FTR-206 | Promotion rankings | As a user, I want that org's rankings. | P1 | Promotion Detail | FTR-501 | 2 | Backend Ready |
| FTR-207 | Promotion champions | As a user, I want that org's current champs. | P1 | Promotion Detail | FTR-601 | 2 | Backend Ready |
| FTR-208 | Past events by promotion | As a user, I want a promotion's event archive. | P2 | Promotion Detail | FTR-305 | 2 | Backend Ready |
| FTR-209 | Multi-promotion support (PFL/Bellator/etc.) | As a user, I want more than just UFC. | P2 | Global | FTR-301 | 5 | Planned |
| FTR-210 | Follow a promotion | As a user, I want updates from an org I like. | P2 | Promotion Detail | FTR-1502 | 3 | Client-only |
| FTR-211 | Promotion history/bio | As a user, I want founding/ownership background. | P3 | Promotion Detail | 🌐 curation | 5 | Planned |

---

## Module 4 — Events  (FTR-3xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-301 | Upcoming events (paged) | As a user, I want the schedule of upcoming cards. | P0 | Events | — | (done) | Implemented |
| FTR-302 | Event detail / full card | As a user, I want the complete fight card. | P0 | Event Detail | — | (done) | Implemented |
| FTR-303 | Live event status | As a user, I want to know a card is live. | P0 | Events, Event Detail | — | (done) | Implemented |
| FTR-304 | Broadcast info | As a user, I want to know where to watch. | P0 | Event Detail | — | (done) | Implemented |
| FTR-305 | Past/finished events | As a user, I want to browse completed cards. | P1 | Events | — | 2 | Backend Ready |
| FTR-306 | Filter by promotion | As a user, I want only one org's events. | P0 | Events | — | (done) | Implemented |
| FTR-307 | Filter by status | As a user, I want to filter live/upcoming/finished. | P1 | Events | FTR-305 | 2 | Backend Ready |
| FTR-308 | Filter by date range | As a user, I want events in a window. | P1 | Events, Calendar | — | 2 | Planned |
| FTR-309 | Filter by country/venue | As a user, I want events near me / in a country. | P2 | Events | FTR-401 | 4 | Planned |
| FTR-310 | Venue detail on event | As a user, I want where the card is held. | P0 | Event Detail | FTR-701v | (done) | Implemented |
| FTR-311 | Card segments (main/prelim/early) | As a user, I want the card grouped by segment. | P0 | Event Detail | FTR-302 | (done) | Implemented |
| FTR-312 | Event search by name | As a user, I want to search for a specific card. | P1 | Search | — | 2 | Planned |
| FTR-313 | Add event to calendar | As a user, I want to save a card to my device calendar. | P1 | Event Detail | — | 3 | Client-only |
| FTR-314 | Set event reminder | As a user, I want a reminder before a card. | P1 | Event Detail | FTR-1401 | 3 | Client-only |
| FTR-315 | Share event | As a user, I want to share a card. | P1 | Event Detail | FTR-2101 | 3 | Client-only |
| FTR-316 | Follow event | As a user, I want to track a specific card. | P2 | Event Detail | FTR-1503 | 3 | Client-only |

---

## Module 5 — Fights / Competitions  (FTR-4xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-401 | Bout matchup detail | As a user, I want the two-fighter matchup view. | P0 | Fight Detail | — | (done) | Implemented |
| FTR-402 | Bout weight class | As a user, I want the division of the bout. | P0 | Fight Detail | — | (done) | Implemented |
| FTR-403 | Card position (match number) | As a user, I want to know where it sits on the card. | P0 | Fight Detail | — | (done) | Implemented |
| FTR-404 | Result (method/round/time) | As a user, I want how the fight ended. | P0 | Fight Detail | — | (done) | Implemented |
| FTR-405 | Per-fighter fight statistics | As a user, I want each fighter's stats for that bout. | P0 | Fight Stats | FTR-105 | (done) | Implemented |
| FTR-406 | Tale of the tape | As a user, I want a physical side-by-side pre-fight. | P1 | Fight Detail | FTR-103 | 3 | Client-only |
| FTR-407 | Finish method detail | As a user, I want the specific finish (e.g. arm triangle). | P1 | Fight Detail | FTR-404 | 2 | Backend Ready |
| FTR-408 | Referee & judges | As a user, I want to know the officials. | P2 | Fight Detail | 🌐 ESPN officials | 4 | Planned |
| FTR-409 | Per-fight striking breakdown | As a user, I want strikes-by-zone for a bout. | P2 | Fight Stats | 🌐 ESPN comp stats | 4 | Planned |
| FTR-410 | Per-fight grappling breakdown | As a user, I want takedowns/control time for a bout. | P2 | Fight Stats | 🌐 ESPN comp stats | 4 | Planned |
| FTR-411 | Fight-of-the-night / bonuses | As a user, I want to see bout accolades. | P3 | Fight Detail | 🌐 curation | 5 | Planned |
| FTR-412 | Round-by-round scorecards | As a user, I want judges' scores per round. | — | — | ⛔ no free data | — | Not feasible |
| FTR-413 | Play-by-play / live commentary | As a user, I want live text commentary. | — | — | ⛔ no free feed | — | Not feasible |
| FTR-414 | Share fight result | As a user, I want to share a bout result. | P1 | Fight Detail | FTR-2101 | 3 | Client-only |

---

## Module 6 — Rankings  (FTR-5xx)

> **The highest value-per-effort module.** The `rankings` table is already populated every 12h by `sync_rankings` — but **no route serves it**. Building `GET /rankings` unlocks this whole module (and feeds Home, Fighters, Champions, Weight Classes, Compare, Discover).

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-501 | Divisional rankings (top 15) | As a user, I want each division's top 15. | P0 | Rankings | — | 2 | Backend Ready |
| FTR-502 | Pound-for-pound rankings | As a user, I want the P4P list. | P0 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-503 | Women's P4P | As a user, I want the women's P4P list. | P1 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-504 | Rank trend (up/down) | As a user, I want to see movement since last update. | P1 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-505 | Filter rankings by division | As a user, I want to jump to a division's list. | P0 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-506 | Filter rankings by promotion | As a user, I want an org's rankings. | P1 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-507 | Tap-through to fighter | As a user, I want to open a ranked fighter's profile. | P0 | Rankings | FTR-102 | 2 | Backend Ready |
| FTR-508 | Ranking history over time | As a user, I want how a fighter's rank changed. | P3 | Rankings, Fighter | 🔵 snapshot table | 5 | Planned |
| FTR-509 | Rankings last-updated timestamp | As a user, I want to know how fresh the list is. | P1 | Rankings | FTR-501 | 2 | Backend Ready |
| FTR-510 | Share rankings list | As a user, I want to share a division's rankings. | P2 | Rankings | FTR-2101 | 3 | Client-only |

---

## Module 7 — Champions  (FTR-6xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-601 | Current champion per division | As a user, I want each division's champ. | P0 | Champions | FTR-501 | 2 | Backend Ready |
| FTR-602 | All champions showcase | As a user, I want every champ on one screen. | P0 | Champions | FTR-601 | 2 | Backend Ready |
| FTR-603 | Title defenses count | As a user, I want how many times they defended. | P1 | Champions, Fighter | FTR-601 | 2 | Backend Ready |
| FTR-604 | Champion tap-through | As a user, I want to open the champ's profile. | P0 | Champions | FTR-102 | 2 | Backend Ready |
| FTR-605 | Women's champions | As a user, I want women's champs surfaced. | P1 | Champions | FTR-601 | 2 | Backend Ready |
| FTR-606 | Interim champions flag | As a user, I want to distinguish interim titles. | P2 | Champions | FTR-601 | 2 | Backend Ready |
| FTR-607 | Champion lineage / history | As a user, I want past champions of a division. | P3 | Champions | 🌐 curation | 5 | Planned |
| FTR-608 | Share champion card | As a user, I want to share a champ. | P2 | Champions | FTR-2101 | 3 | Client-only |

---

## Module 8 — Weight Classes  (FTR-7xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-701 | List all weight classes | As a user, I want to browse divisions. | P0 | Weight Classes | — | (done) | Implemented |
| FTR-702 | Division detail | As a user, I want a division's info (limit, gender). | P0 | Weight Class Detail | FTR-701 | (done) | Implemented |
| FTR-703 | Fighters in division | As a user, I want the roster of a division. | P1 | Weight Class Detail | FTR-115 | 2 | Backend Ready |
| FTR-704 | Division rankings | As a user, I want the division's rankings inline. | P1 | Weight Class Detail | FTR-501 | 2 | Backend Ready |
| FTR-705 | Division champion | As a user, I want the division's champ inline. | P1 | Weight Class Detail | FTR-601 | 2 | Backend Ready |
| FTR-706 | Men's vs women's divisions | As a user, I want them grouped by gender. | P1 | Weight Classes | FTR-701 | 2 | Backend Ready |
| FTR-707 | Weight limits display | As a user, I want the lb/kg limits. | P1 | Weight Class Detail | FTR-702 | 3 | Client-only |
| FTR-708 | Division leaders (stats) | As a user, I want stat leaders per division. | P2 | Weight Class Detail | FTR-801 | 4 | Planned |

---

## Module 9 — Statistics Hub  (FTR-8xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-801 | Per-fighter career stats | As a user, I want a fighter's aggregate stats. | P0 | Stats, Fighter | — | (done) | Implemented |
| FTR-802 | Per-fight stats | As a user, I want stats for one bout. | P0 | Fight Stats | FTR-405 | (done) | Implemented |
| FTR-803 | Striking accuracy metrics | As a user, I want strike LPM/accuracy. | P0 | Stats | FTR-801 | (done) | Implemented |
| FTR-804 | Grappling metrics | As a user, I want takedown avg/accuracy, sub avg. | P0 | Stats | FTR-801 | (done) | Implemented |
| FTR-805 | KO percentage | As a user, I want finish rate by KO. | P1 | Stats | FTR-801 | (done) | Implemented |
| FTR-806 | Division stat leaders | As a user, I want who leads a division in a stat. | P2 | Stats Hub | FTR-801 | 4 | Planned |
| FTR-807 | Records leaderboards | As a user, I want all-time-in-app leaderboards. | P2 | Stats Hub | FTR-801 | 4 | Planned |
| FTR-808 | Most KOs / subs / takedowns | As a user, I want finish leaderboards. | P2 | Stats Hub | FTR-801 | 4 | Planned |
| FTR-809 | Stat visualizations (charts) | As a user, I want charts, not just numbers. | P1 | Stats | FTR-801 | 3 | Client-only |
| FTR-810 | Compare stats between fighters | As a user, I want stat side-by-side. | P1 | Compare | FTR-1901 | 3 | Client-only |
| FTR-811 | Per-fight strike-zone breakdown | As a user, I want head/body/leg splits. | P2 | Fight Stats | 🌐 ESPN comp stats | 4 | Planned |
| FTR-812 | Control-time / position stats | As a user, I want ground control metrics. | P2 | Fight Stats | 🌐 ESPN comp stats | 4 | Planned |

---

## Module 10 — Search  (FTR-9xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-901 | Search fighters | As a user, I want to find fighters. | P0 | Search | FTR-101 | (done) | Implemented |
| FTR-902 | Search promotions | As a user, I want to find organizations. | P0 | Search | FTR-201 | (done) | Implemented |
| FTR-903 | Search events | As a user, I want to find a card by name. | P1 | Search | FTR-312 | 2 | Planned |
| FTR-904 | Unified/global search | As a user, I want one search across all types. | P1 | Search | FTR-901,902,903 | 2 | Planned |
| FTR-905 | Recent searches | As a user, I want my recent queries remembered. | P1 | Search | — | 3 | Client-only |
| FTR-906 | Search suggestions/autocomplete | As a user, I want type-ahead suggestions. | P2 | Search | FTR-904 | 3 | Client-only |
| FTR-907 | Fuzzy/typo tolerance | As a user, I want results despite typos. | P2 | Search | FTR-901 | 4 | Planned |
| FTR-908 | Filtered search (division/nationality) | As a user, I want to narrow fighter search. | P2 | Search | FTR-115 | 4 | Planned |
| FTR-909 | Empty/zero-result states | As a user, I want helpful "no results" guidance. | P1 | Search | — | 3 | Client-only |

---

## Module 11 — Discover  (FTR-10xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1001 | Browse by promotion | As a user, I want to explore by org. | P0 | Discover | FTR-201 | 3 | Implemented |
| FTR-1002 | Browse by division | As a user, I want to explore by weight class. | P0 | Discover | FTR-701 | 3 | Implemented |
| FTR-1003 | Featured/upcoming spotlight | As a user, I want curated highlights. | P1 | Discover | FTR-301 | 3 | Client-only |
| FTR-1004 | Trending fighters | As a user, I want who's hot (rank movers). | P1 | Discover | FTR-504 | 4 | Planned |
| FTR-1005 | Browse by country | As a user, I want fighters/events by country. | P2 | Discover | FTR-309 | 4 | Planned |
| FTR-1006 | Editorial collections | As a user, I want themed lists (e.g. "best KO artists"). | P3 | Discover | 🌐 curation | 5 | Planned |
| FTR-1007 | "On this day" | As a user, I want historical events on today's date. | P2 | Discover | FTR-1701 | 4 | Planned |
| FTR-1008 | Random fighter / surprise me | As a user, I want to discover someone new. | P2 | Discover | FTR-101 | 3 | Client-only |

---

## Module 12 — News  (FTR-11xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1101 | MMA news headlines | As a user, I want current headlines. | P2 | News | 🌐 ESPN news feed | 5 | Planned |
| FTR-1102 | News per fighter | As a user, I want news about a fighter. | P3 | Fighter, News | 🌐 ESPN news feed | 5 | Planned |
| FTR-1103 | News per event | As a user, I want news about a card. | P3 | Event, News | 🌐 ESPN news feed | 5 | Planned |
| FTR-1104 | Article reader / link-out | As a user, I want to read the full article. | P2 | News | FTR-1101 | 5 | Client-only |
| FTR-1105 | Share article | As a user, I want to share news. | P3 | News | FTR-2101 | 5 | Client-only |
| FTR-1106 | Curated editorial | As a user, I want original written content. | — | — | ⛔ not solo-realistic | — | Not feasible |

---

## Module 13 — Media / Images  (FTR-12xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1201 | Fighter headshots | As a user, I want fighter photos. | P0 | everywhere | ESPN CDN (from athlete_id) | 2 | Backend Ready |
| FTR-1202 | Promotion logos | As a user, I want org logos. | P1 | everywhere | 🌐 TheSportsDB / ESPN logos | 2 | Planned |
| FTR-1203 | Country flags | As a user, I want nationality flags. | P1 | Fighter | ESPN flag / static set | 3 | Client-only |
| FTR-1204 | Broadcast network logos | As a user, I want the broadcaster's logo. | P2 | Event Detail | 🌐 ESPN media | 4 | Planned |
| FTR-1205 | Fighter fanart gallery | As a user, I want extra imagery. | P3 | Fighter | 🌐 TheSportsDB | 5 | Planned |
| FTR-1206 | Image caching | As a user, I want images to load instantly on revisit. | P0 | Global | — | 3 | Client-only |
| FTR-1207 | Video highlights | As a user, I want fight highlights. | — | — | ⛔ licensed content | — | Not feasible |

---

## Module 14 — Calendar  (FTR-13xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1301 | Calendar view of events | As a user, I want a month view of cards. | P1 | Calendar | FTR-301 | 3 | Client-only |
| FTR-1302 | Filter calendar by promotion | As a user, I want one org's calendar. | P1 | Calendar | FTR-306 | 3 | Client-only |
| FTR-1303 | Filter calendar by month | As a user, I want to page by month. | P1 | Calendar | FTR-308 | 2 | Planned |
| FTR-1304 | Add to device calendar | As a user, I want native calendar entries. | P1 | Calendar, Event | FTR-313 | 3 | Client-only |
| FTR-1305 | Day detail (events on a date) | As a user, I want all cards on a day. | P1 | Calendar | FTR-301 | 3 | Client-only |
| FTR-1306 | Countdown to next event | As a user, I want a countdown timer. | P2 | Home, Calendar | FTR-301 | 3 | Client-only |
| FTR-1307 | Timezone-aware display | As a user, I want event times in my timezone. | P0 | Global | — | 3 | Client-only |

---

## Module 15 — Notifications  (FTR-14xx)

> **MVP path is device-local.** Local notifications (scheduled on-device from event times) need **no backend and no push server** — recommended for P0/P1. Server-driven push (FCM) is P3 and requires the account layer.

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1401 | Local event reminders | As a user, I want a reminder before a card, no login. | P1 | Event, Settings | FTR-301 | 3 | Client-only |
| FTR-1402 | Local fighter-fight alerts | As a user, I want an alert when my fighter is booked. | P1 | Fighter | FTR-1601 | 3 | Client-only |
| FTR-1403 | Notification preferences | As a user, I want to control what notifies me. | P1 | Settings | — | 3 | Client-only |
| FTR-1404 | Quiet hours | As a user, I want no alerts overnight. | P2 | Settings | FTR-1403 | 3 | Client-only |
| FTR-1405 | Server-side event reminders | As a user, I want reminders even if the app never opens. | P3 | Event | FTR-2001 | 5 | Planned |
| FTR-1406 | Push delivery (FCM) | As a user, I want push notifications. | P3 | Global | FTR-2001 | 5 | Planned |
| FTR-1407 | In-app notification center | As a user, I want a history of my alerts. | P3 | Notifications | FTR-2001 | 5 | Planned |
| FTR-1408 | Mark notification read | As a user, I want to clear read alerts. | P3 | Notifications | FTR-1407 | 5 | Planned |
| FTR-1409 | Result notifications | As a user, I want to know how my fighter did. | P3 | Global | FTR-1406 | 5 | Planned |
| FTR-1410 | Card-starting-now alert | As a user, I want to know a card just went live. | P3 | Global | FTR-1406 | 5 | Planned |

---

## Module 16 — Favorites  (FTR-15xx)

> **MVP path is device-local** (store IDs on device). Server-synced favorites (below, marked Planned) require the account layer — P3.

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1501 | Follow/unfollow fighter (local) | As a user, I want to save fighters without an account. | P0 | Fighter, Favorites | FTR-102 | 3 | Client-only |
| FTR-1502 | Follow/unfollow promotion (local) | As a user, I want to save orgs locally. | P1 | Promotion, Favorites | FTR-202 | 3 | Client-only |
| FTR-1503 | Save/unsave event (local) | As a user, I want to bookmark cards locally. | P1 | Event, Favorites | FTR-301 | 3 | Client-only |
| FTR-1504 | Favorites list screen | As a user, I want all my saved items in one place. | P0 | Favorites | FTR-1501 | 3 | Client-only |
| FTR-1505 | Favorites-driven feed | As a user, I want a feed built from my favorites. | P1 | Home, Feed | FTR-1601 | 3 | Client-only |
| FTR-1506 | Server-synced fighter follows | As a user, I want my follows on all my devices. | P3 | Fighter | FTR-2001 | 5 | Planned |
| FTR-1507 | Server-synced promotion follows | As a user, I want org follows synced. | P3 | Promotion | FTR-2001 | 5 | Planned |
| FTR-1508 | Favorite fighters' next fights | As a user, I want upcoming bouts for saved fighters. | P0 | Favorites, Home | FTR-107 | 3 | Client-only |
| FTR-1509 | Reorder/manage favorites | As a user, I want to organize my saved items. | P2 | Favorites | FTR-1504 | 3 | Client-only |

---

## Module 17 — Personalized Feed  (FTR-16xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1601 | Feed from local favorites | As a user, I want a feed of my saved fighters' activity, no login. | P0 | Home, Feed | FTR-1501 | 3 | Client-only |
| FTR-1602 | Upcoming fights of followed fighters | As a user, I want their next bouts surfaced. | P0 | Feed | FTR-107 | 3 | Client-only |
| FTR-1603 | Recent results of followed fighters | As a user, I want their latest results. | P1 | Feed | FTR-106 | 3 | Client-only |
| FTR-1604 | Followed promotions' events | As a user, I want cards from orgs I follow. | P1 | Feed | FTR-203 | 3 | Client-only |
| FTR-1605 | Cross-promotion aggregation | As a user, I want one feed across all orgs. | P1 | Feed | FTR-301 | 3 | Client-only |
| FTR-1606 | Server-computed feed | As a user, I want a feed computed server-side. | P3 | Feed | FTR-2001 | 5 | Planned |
| FTR-1607 | Feed refresh & pagination | As a user, I want to scroll and refresh the feed. | P0 | Feed | FTR-1601 | 3 | Client-only |

---

## Module 18 — Historical Archive  (FTR-17xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1701 | Past events archive | As a user, I want to browse historical cards. | P1 | Archive | FTR-305 | 2 | Backend Ready |
| FTR-1702 | Event results archive | As a user, I want results from old cards. | P1 | Archive | FTR-404 | 2 | Backend Ready |
| FTR-1703 | Fighter career archive | As a user, I want a fighter's full history. | P0 | Fighter | FTR-106 | (done) | Implemented |
| FTR-1704 | Season browsing | As a user, I want events grouped by year/season. | P2 | Archive | 🌐 ESPN seasons | 4 | Planned |
| FTR-1705 | Historical event timeline | As a user, I want a chronological event view. | P2 | Archive | FTR-1701 | 3 | Client-only |
| FTR-1706 | Hall of Fame | As a user, I want inducted legends. | P3 | Hall of Fame | 🌐 curation | 5 | Planned |
| FTR-1707 | Legendary fights collection | As a user, I want classic bouts curated. | P3 | Archive | 🌐 curation | 5 | Planned |
| FTR-1708 | Era timelines | As a user, I want the sport's history by era. | P3 | Archive | 🌐 curation | 5 | Planned |

---

## Module 19 — Records & Achievements  (FTR-18xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1801 | Win streaks | As a user, I want current/longest streaks. | P1 | Records, Fighter | FTR-106 | 4 | Planned |
| FTR-1802 | Finish rate | As a user, I want % of wins by finish. | P1 | Records, Fighter | FTR-106 | 4 | Planned |
| FTR-1803 | Title defense records | As a user, I want most title defenses. | P1 | Records | FTR-603 | 2 | Backend Ready |
| FTR-1804 | Most wins in division | As a user, I want divisional win leaders. | P2 | Records | FTR-106 | 4 | Planned |
| FTR-1805 | Fastest finishes | As a user, I want quickest KOs/subs. | P2 | Records | FTR-404 | 4 | Planned |
| FTR-1806 | Most KOs / submissions | As a user, I want finish leaders. | P2 | Records | FTR-106 | 4 | Planned |
| FTR-1807 | Longest win streaks (all-time in-app) | As a user, I want historical streak leaders. | P2 | Records | FTR-106 | 4 | Planned |
| FTR-1808 | Youngest/oldest champions | As a user, I want age-based records. | P3 | Records | FTR-601 | 4 | Planned |
| FTR-1809 | Debut/veteran milestones | As a user, I want career milestone markers. | P3 | Fighter | FTR-106 | 4 | Planned |
| FTR-1810 | Achievement badges (fighter) | As a user, I want visual achievement badges. | P2 | Fighter | FTR-1801 | 4 | Planned |
| FTR-1811 | Verified all-time records | As a user, I want authoritative historical records. | — | — | 🌐 curation for accuracy | 5 | Planned |

---

## Module 20 — Compare Fighters  (FTR-19xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-1901 | Side-by-side profiles | As a user, I want to compare two fighters. | P1 | Compare | FTR-102 | 3 | Client-only |
| FTR-1902 | Physical comparison | As a user, I want height/reach/weight compared. | P1 | Compare | FTR-103 | 3 | Client-only |
| FTR-1903 | Record comparison | As a user, I want W-L-D compared. | P1 | Compare | FTR-104 | 3 | Client-only |
| FTR-1904 | Stat comparison | As a user, I want career stats compared. | P1 | Compare | FTR-801 | 3 | Client-only |
| FTR-1905 | Common opponents | As a user, I want shared opponents shown. | P2 | Compare | FTR-117 | 4 | Planned |
| FTR-1906 | Head-to-head record | As a user, I want their record vs each other. | P2 | Compare | FTR-116 | 4 | Planned |
| FTR-1907 | Compare endpoint (optional) | As a user, I want a fast single call for compare. | P2 | Compare | FTR-102 | 4 | Planned |
| FTR-1908 | Share comparison | As a user, I want to share a comparison card. | P2 | Compare | FTR-2101 | 3 | Client-only |

---

## Module 21 — User Account  (FTR-20xx)

> **Optional layer.** `users` table exists and config carries JWT settings + a Supabase-Auth-oriented `User` model (email, no local password) + `FCM_SERVICE_ACCOUNT_JSON`. But **no auth code and no account routes are implemented.** The app is designed to work fully in anonymous/local mode; accounts are P3.

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-2001 | Sign up / sign in | As a user, I want an account to sync data. | P3 | Auth | Supabase Auth | 5 | Planned |
| FTR-2002 | Anonymous / no-account mode | As a user, I want full use without signing up. | P0 | Global | — | 3 | Client-only |
| FTR-2003 | Profile / display name | As a user, I want a profile identity. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2004 | Cross-device sync | As a user, I want my data on all devices. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2005 | Sign out | As a user, I want to sign out. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2006 | Delete account / data | As a user, I want to delete my account. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2007 | Register push token | As a user, I want push tied to my account. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2008 | Migrate local → account | As a user, I want my local favorites imported on sign-in. | P3 | Auth | FTR-2001,1501 | 5 | Planned |
| FTR-2009 | Privacy / data export | As a user, I want to export my data. | P3 | Account | FTR-2001 | 5 | Planned |
| FTR-2010 | Settings screen | As a user, I want app settings in one place. | P0 | Settings | — | 3 | Client-only |

---

## Module 22 — Sharing  (FTR-21xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-2101 | Native share sheet | As a user, I want to share via the OS share sheet. | P1 | Global | — | 3 | Client-only |
| FTR-2102 | Deep links | As a user, I want links that open the right screen. | P1 | Global | stable UUIDs | 3 | Client-only |
| FTR-2103 | Share fighter | As a user, I want to share a fighter. | P1 | Fighter | FTR-2101 | 3 | Client-only |
| FTR-2104 | Share event | As a user, I want to share a card. | P1 | Event | FTR-2101 | 3 | Client-only |
| FTR-2105 | Share fight result | As a user, I want to share a result. | P1 | Fight | FTR-2101 | 3 | Client-only |
| FTR-2106 | Generated share image cards | As a user, I want a nice image to share. | P2 | Global | FTR-2101 | 3 | Client-only |
| FTR-2107 | Copy link | As a user, I want to copy a deep link. | P2 | Global | FTR-2102 | 3 | Client-only |

---

## Module 23 — Offline  (FTR-22xx)

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-2201 | Cache last-viewed data | As a user, I want recently viewed content offline. | P1 | Global | — | 3 | Client-only |
| FTR-2202 | Offline favorites | As a user, I want my favorites available offline. | P0 | Favorites | FTR-1501 | 3 | Client-only |
| FTR-2203 | Sync on reconnect | As a user, I want fresh data when back online. | P1 | Global | — | 3 | Client-only |
| FTR-2204 | Offline indicator | As a user, I want to know I'm offline. | P1 | Global | — | 3 | Client-only |
| FTR-2205 | ETag / HTTP cache headers | As a user, I want efficient re-fetches. | P2 | Global (backend) | FTR (cache phase) | 1 | Planned |
| FTR-2206 | Stale-while-revalidate UX | As a user, I want instant cached view then refresh. | P2 | Global | FTR-2201 | 3 | Client-only |
| FTR-2207 | Configurable cache size | As a user, I want to manage local storage. | P3 | Settings | FTR-2201 | 3 | Client-only |

---

## Module 24 — Knowledge Graph  (FTR-23xx)

> Relationship-centric navigation. No AI — pure relational joins across existing entities (Fighter ↔ Competitor ↔ Competition ↔ Event ↔ Venue ↔ Promotion ↔ WeightClass ↔ Ranking ↔ Broadcast, plus 🌐 Officials). See the graph model in `data-specification.md`.

| ID | Feature | User story | Priority | Screen(s) | Depends on | Phase | Status |
|----|---------|-----------|----------|-----------|-----------|-------|--------|
| FTR-2301 | Fighter → all events fought | As a user, I want to jump from fighter to their events. | P1 | Fighter | FTR-106 | (done) | Implemented |
| FTR-2302 | Event → all fighters on card | As a user, I want to jump from event to fighters. | P0 | Event | FTR-302 | (done) | Implemented |
| FTR-2303 | Venue → events held there | As a user, I want a venue's event history. | P2 | Venue | FTR-310 | 4 | Planned |
| FTR-2304 | Promotion → fighters/events/rankings | As a user, I want to traverse a promotion's graph. | P1 | Promotion | FTR-203,206 | 2 | Backend Ready |
| FTR-2305 | Weight class → fighters/rankings/champ | As a user, I want to traverse a division. | P1 | Weight Class | FTR-703,704,705 | 2 | Backend Ready |
| FTR-2306 | Ranking → fighter → next fight | As a user, I want to chain rank to upcoming bout. | P1 | Rankings | FTR-501,107 | 2 | Backend Ready |
| FTR-2307 | Opponent web (who fought whom) | As a user, I want to explore opponent networks. | P2 | Fighter | FTR-117 | 4 | Planned |
| FTR-2308 | Official → fights officiated | As a user, I want a referee's fight history. | P3 | Official | 🌐 ESPN officials | 4 | Planned |
| FTR-2309 | Related fighters (same division/gym) | As a user, I want suggested related fighters. | P2 | Fighter | FTR-115 | 4 | Planned |
| FTR-2310 | Graph-based "explore" screen | As a user, I want a visual relationship explorer. | P3 | Discover | FTR-2301..2309 | 4 | Planned |

---

## Appendix A — Status rollup (see `feature-registry.md` for the full table)

- **Implemented today:** the entire pre-Redis read product — ~30 features across Fighters, Events, Fights, Promotions, Venues, Weight Classes, Stats, Search, plus graph jumps that fall out of existing endpoints.
- **Backend Ready (data synced, no route):** the Rankings, Champions, past-events/archive, division-roster, and headshot clusters — the fastest wins, mostly **Phase 2**.
- **Client-only (no backend):** Favorites, Local Notifications, Feed, Compare, Calendar, Sharing, Offline, Discover composition, Account-free mode — most of the *felt* product, **Phase 3**.
- **Planned (new backend):** computed Records/Stats-leaders, per-fight ESPN detail, officials, search upgrades — **Phase 4**.
- **Planned (optional heavy):** Accounts, server push/FCM, server-synced follows, curated Hall-of-Fame/history, News — **Phase 5**.
- **Not feasible on free data (⛔):** round-by-round scorecards, live play-by-play, full-fight video, betting odds, original editorial. Explicitly out.

## Appendix B — MVP definition (the P0 slice)

A polished, **account-free** app: Home + Events + full cards + live/finished status + broadcast info + Fighter profiles (identity, physicals, record, career stats, fight history, next fight, **headshot**) + **Rankings + Champions** + Weight Classes + Search + Compare + Calendar + **on-device Favorites, Feed, and local reminders** + Sharing + Offline. **~40 P0 features**, all powered by the current backend plus the Phase 1–2 work. No login, no push server, no AI, no paid anything.
