# MMA Platform — Master Feature Registry

> **Version:** 1.0 · **Prepared:** 2026-07-30
> **Purpose:** One scannable table of **every** feature with its backend/DB/ESPN dependencies, screens, effort, phase, and status — plus rollups and the "one endpoint → many features" mapping that proves each ESPN endpoint earns its keep.
> Cross-references the **PRD** (`product-requirements.md`) and **Data Spec** (`data-specification.md`) by `FTR-xxx`.
> **Grounded in real code** (extracted backend: 15 routes, 15 tables, 4-tier scheduler). Status reflects actual implementation.

**Status key:** `Implemented` (route exists & tested) · `Backend Ready` (data synced, no route) · `Planned` (new backend work) · `Client-only` (Flutter, no backend) · `Not feasible` (⛔ no free data).
**Effort key:** `H` hours · `D` days · `W` weeks · `M` months (cumulative for the cluster).

---

## 1. Registry — Core Data Modules

### Home (FTR-0xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-001 | Upcoming events list | Implemented | P0 | `/events` | events | `/events` | Home | 301 | done | 3 |
| FTR-002 | Next-event hero | Implemented | P0 | `/events` | events | `/events` | Home | 301 | H | 3 |
| FTR-003 | Live banner | Implemented | P0 | `/events` | events | live sync | Home | 303 | H | 3 |
| FTR-004 | Latest results strip | Backend Ready | P1 | `/events?status=FINAL`* | events,competitions | `/status` | Home | 305 | D | 2 |
| FTR-005 | Top-ranked row | Backend Ready | P1 | `/rankings`* | rankings | `/rankings` | Home | 501 | H | 2 |
| FTR-006 | Champions strip | Backend Ready | P1 | `/champions`* | rankings | `/rankings` | Home | 601 | H | 2 |
| FTR-007 | Your-fighters row | Client-only | P1 | (local) | — | — | Home | 1601 | D | 3 |
| FTR-008 | Featured promotions | Implemented | P2 | `/promotions` | promotions | `/leagues` | Home | 201 | H | 3 |
| FTR-009 | Pull-to-refresh | Client-only | P0 | — | — | — | Home | — | H | 3 |
| FTR-010 | Layout personalization | Client-only | P2 | — | — | — | Home | — | D | 3 |
| FTR-011 | Light/dark theme | Client-only | P1 | — | — | — | Global | — | D | 3 |
| FTR-012 | Loading skeletons | Client-only | P0 | — | — | — | Home | — | H | 3 |

### Fighters (FTR-1xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-101 | Search by name | Implemented | P0 | `/fighters?q=` | fighters | `/athletes` | Search | — | done | — |
| FTR-102 | Profile identity | Implemented | P0 | `/fighters/{id}` | fighters | `/athletes/{id}` | Profile | 1201 | done | — |
| FTR-103 | Physicals | Implemented | P0 | `/fighters/{id}` | fighters | `/athletes/{id}` | Profile | — | done | — |
| FTR-104 | Record W-L-D | Implemented | P0 | `/fighters/{id}` | fighters | `/records/0` | Profile | — | done | — |
| FTR-105 | Career stats | Implemented | P0 | `/fighters/{id}/statistics` | fighters | `/statistics/0` | Profile | — | done | — |
| FTR-106 | Fight history | Implemented | P0 | `/fighters/{id}/fights` | competitors,competitions | `/eventlog` | Profile | — | done | — |
| FTR-107 | Next fight | Implemented | P0 | `/fighters/{id}/next-fight` | competitions | `/events` | Profile | 301 | done | — |
| FTR-108 | Headshot | Backend Ready | P0 | `/fighters/{id}` | fighters.headshot_url | ESPN-CDN | everywhere | 1201 | H | 2 |
| FTR-109 | Ranking badge | Backend Ready | P1 | `/rankings`* | rankings | `/rankings` | Profile | 501 | H | 2 |
| FTR-110 | Champion indicator | Backend Ready | P1 | `/champions`* | rankings | `/rankings` | Profile | 601 | H | 2 |
| FTR-111 | Win-method breakdown | Planned | P1 | `/fighters/{id}/records`* | (computed) | `/records/0` | Profile | 106 | D | 4 |
| FTR-112 | Win streak | Planned | P1 | `/fighters/{id}/records`* | (computed) | eventlog | Profile | 106 | D | 4 |
| FTR-113 | Style/stance tags | Planned | P2 | `/fighters/{id}` | fighters(+cols) | `/athletes/{id}` | Profile | 1201 | D | 2 |
| FTR-114 | Gym/association | Planned | P2 | `/fighters/{id}` | fighters(+cols) | `/athletes/{id}` | Profile | — | D | 2 |
| FTR-115 | Fighters in division | Backend Ready | P1 | `/fighters?weight_class=`* | fighters | — | WeightClass | 701 | D | 2 |
| FTR-116 | Head-to-head | Planned | P2 | `/compare`* | competitors | — | Compare | 106 | D | 4 |
| FTR-117 | Common opponents | Planned | P2 | `/compare`* | competitors | — | Compare | 106 | D | 4 |
| FTR-118 | Title history | Planned | P2 | curated | 🔵 reigns | 🌐 curation | Profile | — | W | 5 |
| FTR-119 | Media gallery | Planned | P3 | — | — | 🌐 TSDB | Profile | — | D | 5 |
| FTR-120 | Career timeline | Client-only | P2 | `/fighters/{id}/fights` | competitions | eventlog | Profile | 106 | D | 3 |
| FTR-121 | Follow fighter | Client-only | P1 | (local) | — | — | Profile | 1501 | H | 3 |
| FTR-122 | Share profile | Client-only | P1 | (local) | — | — | Profile | 2101 | H | 3 |

### Organizations (FTR-2xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-201 | List/search | Implemented | P0 | `/promotions` | promotions | `/leagues` | Promotions | — | done | — |
| FTR-202 | Detail | Implemented | P0 | `/promotions/{id}` | promotions | `/leagues/{slug}` | Detail | — | done | — |
| FTR-203 | Events by promotion | Implemented | P0 | `/events?promotion_id=` | events | `/events` | Detail | 301 | done | — |
| FTR-204 | Logo/branding | Planned | P1 | `/promotions/{id}` | promotions.logo_url | 🌐 TSDB/logos | everywhere | — | D | 2 |
| FTR-205 | Roster | Planned | P2 | `/promotions/{id}/roster`* | competitors | — | Detail | 106 | D | 4 |
| FTR-206 | Rankings | Backend Ready | P1 | `/rankings?promotion=`* | rankings | `/rankings` | Detail | 501 | H | 2 |
| FTR-207 | Champions | Backend Ready | P1 | `/champions?promotion=`* | rankings | `/rankings` | Detail | 601 | H | 2 |
| FTR-208 | Past events | Backend Ready | P2 | `/events?status=FINAL`* | events | — | Detail | 305 | D | 2 |
| FTR-209 | Multi-promotion | Planned | P2 | (config `SYNC_LEAGUES`) | all | other slugs | Global | 301 | W | 5 |
| FTR-210 | Follow promotion | Client-only | P2 | (local) | — | — | Detail | 1502 | H | 3 |
| FTR-211 | History/bio | Planned | P3 | curated | 🔵 | 🌐 curation | Detail | — | W | 5 |

### Events (FTR-3xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-301 | Upcoming (paged) | Implemented | P0 | `/events` | events | `/events` | Events | — | done | — |
| FTR-302 | Detail/full card | Implemented | P0 | `/events/{id}` | events,competitions | `/events/{id}` | Detail | — | done | — |
| FTR-303 | Live status | Implemented | P0 | `/events/{id}` | events | live sync | Detail | — | done | — |
| FTR-304 | Broadcast info | Implemented | P0 | `/events/{id}` | broadcasts | `/broadcasts` | Detail | — | done | — |
| FTR-305 | Past/finished | Backend Ready | P1 | `/events?status=`* | events | — | Events | — | D | 2 |
| FTR-306 | Filter by promotion | Implemented | P0 | `/events?promotion_id=` | events | — | Events | — | done | — |
| FTR-307 | Filter by status | Backend Ready | P1 | `/events?status=`* | events | — | Events | 305 | D | 2 |
| FTR-308 | Filter by date | Planned | P1 | `/events?date_from=`* | events | — | Events | — | D | 2 |
| FTR-309 | Filter by country | Planned | P2 | `/events?country=`* | events,venues | — | Events | 401 | D | 4 |
| FTR-310 | Venue on event | Implemented | P0 | `/events/{id}` | venues | `/venues/{id}` | Detail | — | done | — |
| FTR-311 | Card segments | Implemented | P0 | `/events/{id}` | competitions | `/competitions/{id}` | Detail | 302 | done | — |
| FTR-312 | Event name search | Planned | P1 | `/search`* | events | — | Search | — | D | 2 |
| FTR-313 | Add to calendar | Client-only | P1 | (local) | — | — | Detail | — | H | 3 |
| FTR-314 | Set reminder | Client-only | P1 | (local) | — | — | Detail | 1401 | H | 3 |
| FTR-315 | Share event | Client-only | P1 | (local) | — | — | Detail | 2101 | H | 3 |
| FTR-316 | Follow event | Client-only | P2 | (local) | — | — | Detail | 1503 | H | 3 |

### Fights (FTR-4xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-401 | Bout matchup | Implemented | P0 | `/competitions/{id}` | competitions,competitors | `/competitions/{id}` | Fight | — | done | — |
| FTR-402 | Bout weight class | Implemented | P0 | `/competitions/{id}` | weight_classes | `/competitions/{id}` | Fight | — | done | — |
| FTR-403 | Card position | Implemented | P0 | `/competitions/{id}` | competitions | `/competitions/{id}` | Fight | — | done | — |
| FTR-404 | Result | Implemented | P0 | `/competitions/{id}` | competitions | `/status` | Fight | — | done | — |
| FTR-405 | Per-fighter stats | Implemented | P0 | `/competitions/{id}` | statistics | `/competitors/{id}/statistics` | Fight Stats | 105 | done | — |
| FTR-406 | Tale of the tape | Client-only | P1 | `/competitions/{id}` | competitors,fighters | — | Fight | 103 | D | 3 |
| FTR-407 | Finish method detail | Backend Ready | P1 | `/competitions/{id}` | competitions.result_detail | `/status` | Fight | 404 | H | 2 |
| FTR-408 | Referee & judges | Planned | P2 | `/competitions/{id}/officials`* | 🔵 officials | `/officials` | Fight | — | D | 4 |
| FTR-409 | Striking breakdown | Planned | P2 | `/competitions/{id}/statistics`* | statistics | `/competitors/{id}/statistics` | Fight Stats | — | D | 4 |
| FTR-410 | Grappling breakdown | Planned | P2 | `/competitions/{id}/statistics`* | statistics | `/competitors/{id}/statistics` | Fight Stats | — | D | 4 |
| FTR-411 | Bonuses/FOTN | Planned | P3 | curated | 🔵 | 🌐 curation | Fight | — | W | 5 |
| FTR-412 | Round scorecards | Not feasible | — | — | — | ⛔ | — | — | — | — |
| FTR-413 | Play-by-play | Not feasible | — | — | — | ⛔ | — | — | — | — |
| FTR-414 | Share result | Client-only | P1 | (local) | — | — | Fight | 2101 | H | 3 |

---

## 2. Registry — Discovery & Rankings Modules

### Rankings (FTR-5xx) — *highest value/effort; all data already synced*
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-501 | Divisional rankings | Backend Ready | P0 | `/rankings`* | rankings | `/rankings/{cat}` | Rankings | — | D | 2 |
| FTR-502 | Pound-for-pound | Backend Ready | P0 | `/rankings?category=p4p`* | rankings | `/rankings/{cat}` | Rankings | 501 | H | 2 |
| FTR-503 | Women's P4P | Backend Ready | P1 | `/rankings?category=`* | rankings | `/rankings/{cat}` | Rankings | 501 | H | 2 |
| FTR-504 | Rank trend | Backend Ready | P1 | `/rankings`* | rankings.trend | `/rankings/{cat}` | Rankings | 501 | H | 2 |
| FTR-505 | Filter by division | Backend Ready | P0 | `/rankings?category=`* | rankings | — | Rankings | 501 | H | 2 |
| FTR-506 | Filter by promotion | Backend Ready | P1 | `/rankings?promotion=`* | rankings | — | Rankings | 501 | H | 2 |
| FTR-507 | Tap-through to fighter | Backend Ready | P0 | `/rankings`+`/fighters/{id}` | rankings,fighters | — | Rankings | 102 | H | 2 |
| FTR-508 | Rank history | Planned | P3 | `/rankings/history`* | 🔵 snapshots | — | Rankings | — | W | 5 |
| FTR-509 | Last-updated | Backend Ready | P1 | `/rankings`* | rankings.updated_at | — | Rankings | 501 | H | 2 |
| FTR-510 | Share rankings | Client-only | P2 | (local) | — | — | Rankings | 2101 | H | 3 |

### Champions (FTR-6xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-601 | Champion per division | Backend Ready | P0 | `/champions`* | rankings.is_champion | `/rankings/{cat}` | Champions | 501 | H | 2 |
| FTR-602 | All-champions showcase | Backend Ready | P0 | `/champions`* | rankings | — | Champions | 601 | H | 2 |
| FTR-603 | Title defenses | Backend Ready | P1 | `/champions`* | rankings.title_defenses | `/rankings/{cat}` | Champions | 601 | H | 2 |
| FTR-604 | Tap-through | Backend Ready | P0 | `/champions`+`/fighters/{id}` | rankings,fighters | — | Champions | 102 | H | 2 |
| FTR-605 | Women's champions | Backend Ready | P1 | `/champions`* | rankings | — | Champions | 601 | H | 2 |
| FTR-606 | Interim flag | Backend Ready | P2 | `/champions`* | rankings.category | — | Champions | 601 | H | 2 |
| FTR-607 | Lineage/history | Planned | P3 | curated | 🔵 reigns | 🌐 curation | Champions | — | W | 5 |
| FTR-608 | Share champion | Client-only | P2 | (local) | — | — | Champions | 2101 | H | 3 |

### Weight Classes (FTR-7xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-701 | List divisions | Implemented | P0 | `/weight-classes` | weight_classes | payloads | WeightClasses | — | done | — |
| FTR-702 | Division detail | Implemented | P0 | `/weight-classes` | weight_classes | payloads | Detail | 701 | done | — |
| FTR-703 | Fighters in division | Backend Ready | P1 | `/fighters?weight_class=`* | fighters | — | Detail | 115 | D | 2 |
| FTR-704 | Division rankings | Backend Ready | P1 | `/rankings?category=`* | rankings | — | Detail | 501 | H | 2 |
| FTR-705 | Division champion | Backend Ready | P1 | `/champions`* | rankings | — | Detail | 601 | H | 2 |
| FTR-706 | Men's vs women's | Backend Ready | P1 | `/weight-classes` | weight_classes.gender | — | WeightClasses | 701 | H | 2 |
| FTR-707 | Weight limits | Client-only | P1 | `/weight-classes` | weight_classes | — | Detail | 702 | H | 3 |
| FTR-708 | Division stat leaders | Planned | P2 | `/stats/leaders`* | statistics | — | Detail | 801 | D | 4 |

### Statistics Hub (FTR-8xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN endpoint | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|---------------|--------|------|--------|-------|
| FTR-801 | Career stats | Implemented | P0 | `/fighters/{id}/statistics` | fighters | `/statistics/0` | Stats | — | done | — |
| FTR-802 | Per-fight stats | Implemented | P0 | `/competitions/{id}` | statistics | `/competitors/{id}/statistics` | Fight Stats | 405 | done | — |
| FTR-803 | Striking metrics | Implemented | P0 | `/fighters/{id}/statistics` | fighters | `/statistics/0` | Stats | 801 | done | — |
| FTR-804 | Grappling metrics | Implemented | P0 | `/fighters/{id}/statistics` | fighters | `/statistics/0` | Stats | 801 | done | — |
| FTR-805 | KO percentage | Implemented | P1 | `/fighters/{id}/statistics` | fighters | `/statistics/0` | Stats | 801 | done | — |
| FTR-806 | Division stat leaders | Planned | P2 | `/stats/leaders`* | statistics | — | Stats Hub | 801 | D | 4 |
| FTR-807 | Records leaderboards | Planned | P2 | `/stats/leaders`* | statistics | — | Stats Hub | 801 | D | 4 |
| FTR-808 | Most KOs/subs/TDs | Planned | P2 | `/stats/leaders`* | competitions | — | Stats Hub | 801 | D | 4 |
| FTR-809 | Stat charts | Client-only | P1 | `/fighters/{id}/statistics` | — | — | Stats | 801 | D | 3 |
| FTR-810 | Compare stats | Client-only | P1 | 2× `/fighters/{id}` | — | — | Compare | 1901 | D | 3 |
| FTR-811 | Strike-zone breakdown | Planned | P2 | `/competitions/{id}/statistics`* | statistics | `/competitors/{id}/statistics` | Fight Stats | — | D | 4 |
| FTR-812 | Control/position stats | Planned | P2 | `/competitions/{id}/statistics`* | statistics | `/competitors/{id}/statistics` | Fight Stats | — | D | 4 |

### Search (FTR-9xx) · Discover (FTR-10xx)
| FTR | Name | Status | Pri | Backend route | DB tables | ESPN | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------------|-----------|------|--------|------|--------|-------|
| FTR-901 | Search fighters | Implemented | P0 | `/fighters?q=` | fighters | — | Search | — | done | — |
| FTR-902 | Search promotions | Implemented | P0 | `/promotions?q=` | promotions | — | Search | — | done | — |
| FTR-903 | Search events | Planned | P1 | `/search`* | events | — | Search | — | D | 2 |
| FTR-904 | Unified search | Planned | P1 | `/search`* | multi | — | Search | 901,902,903 | D | 2 |
| FTR-905 | Recent searches | Client-only | P1 | (local) | — | — | Search | — | H | 3 |
| FTR-906 | Autocomplete | Client-only | P2 | (local) | — | — | Search | 904 | D | 3 |
| FTR-907 | Fuzzy tolerance | Planned | P2 | `/fighters?q=` | fighters(trgm) | — | Search | 901 | D | 4 |
| FTR-908 | Filtered search | Planned | P2 | `/search?filters`* | fighters | — | Search | 115 | D | 4 |
| FTR-909 | Empty states | Client-only | P1 | — | — | — | Search | — | H | 3 |
| FTR-1001 | Browse by promotion | Implemented | P0 | `/promotions` | promotions | — | Discover | 201 | H | 3 |
| FTR-1002 | Browse by division | Implemented | P0 | `/weight-classes` | weight_classes | — | Discover | 701 | H | 3 |
| FTR-1003 | Featured spotlight | Client-only | P1 | `/events` | events | — | Discover | 301 | D | 3 |
| FTR-1004 | Trending fighters | Planned | P1 | `/rankings`* | rankings | — | Discover | 504 | D | 4 |
| FTR-1005 | Browse by country | Planned | P2 | `/fighters?country=`* | fighters | — | Discover | 309 | D | 4 |
| FTR-1006 | Editorial collections | Planned | P3 | curated | 🔵 | 🌐 | Discover | — | W | 5 |
| FTR-1007 | On this day | Planned | P2 | `/events?date=`* | events | — | Discover | 1701 | D | 4 |
| FTR-1008 | Surprise me | Client-only | P2 | `/fighters` | — | — | Discover | 101 | H | 3 |

---

## 3. Registry — Content, Personal & System Modules

### News (11xx) · Media (12xx) · Calendar (13xx)
| FTR | Name | Status | Pri | Backend | DB | ESPN/Source | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------|----|-----|--------|------|--------|-------|
| FTR-1101 | News headlines | Planned | P2 | `/news`* | 🔵 | 🌐 ESPN news | News | — | W | 5 |
| FTR-1102 | News per fighter | Planned | P3 | `/news?fighter=`* | 🔵 | 🌐 ESPN news | Fighter | 1101 | D | 5 |
| FTR-1103 | News per event | Planned | P3 | `/news?event=`* | 🔵 | 🌐 ESPN news | Event | 1101 | D | 5 |
| FTR-1104 | Article reader | Client-only | P2 | — | — | link-out | News | 1101 | D | 5 |
| FTR-1105 | Share article | Client-only | P3 | (local) | — | — | News | 2101 | H | 5 |
| FTR-1106 | Curated editorial | Not feasible | — | — | — | ⛔ | — | — | — | — |
| FTR-1201 | Fighter headshots | Backend Ready | P0 | `/fighters/{id}` | fighters.headshot_url | ESPN-CDN | everywhere | — | H | 2 |
| FTR-1202 | Promotion logos | Planned | P1 | `/promotions/{id}` | promotions.logo_url | 🌐 TSDB | everywhere | — | D | 2 |
| FTR-1203 | Country flags | Client-only | P1 | — | — | static/ESPN | Fighter | — | H | 3 |
| FTR-1204 | Broadcast logos | Planned | P2 | `/events/{id}` | broadcasts.logo_url | 🌐 ESPN media | Event | — | D | 4 |
| FTR-1205 | Fanart gallery | Planned | P3 | — | — | 🌐 TSDB | Fighter | — | D | 5 |
| FTR-1206 | Image caching | Client-only | P0 | — | — | — | Global | — | H | 3 |
| FTR-1207 | Video highlights | Not feasible | — | — | — | ⛔ | — | — | — | — |
| FTR-1301 | Calendar view | Client-only | P1 | `/events` | events | — | Calendar | 301 | D | 3 |
| FTR-1302 | Filter by promotion | Client-only | P1 | `/events?promotion_id=` | events | — | Calendar | 306 | H | 3 |
| FTR-1303 | Filter by month | Planned | P1 | `/events?date_from=`* | events | `/calendar/ondays` | Calendar | 308 | D | 2 |
| FTR-1304 | Add to device cal | Client-only | P1 | (local) | — | — | Calendar | 313 | H | 3 |
| FTR-1305 | Day detail | Client-only | P1 | `/events?date=`* | events | — | Calendar | 301 | H | 3 |
| FTR-1306 | Countdown | Client-only | P2 | `/events` | events | — | Home | 301 | H | 3 |
| FTR-1307 | Timezone-aware | Client-only | P0 | — | — | — | Global | — | H | 3 |

### Notifications (14xx) · Favorites (15xx) · Feed (16xx)
| FTR | Name | Status | Pri | Backend | DB | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------|----|--------|------|--------|-------|
| FTR-1401 | Local reminders | Client-only | P1 | (local) | — | Event | 301 | D | 3 |
| FTR-1402 | Local fight alerts | Client-only | P1 | (local) | — | Fighter | 1601 | D | 3 |
| FTR-1403 | Notification prefs | Client-only | P1 | (local) | — | Settings | — | H | 3 |
| FTR-1404 | Quiet hours | Client-only | P2 | (local) | — | Settings | 1403 | H | 3 |
| FTR-1405 | Server reminders | Planned | P3 | `/me/reminders`* | reminders | Event | 2001 | W | 5 |
| FTR-1406 | Push (FCM) | Planned | P3 | push worker* | notifications,users | Global | 2001 | W | 5 |
| FTR-1407 | In-app inbox | Planned | P3 | `/me/notifications`* | notifications | Notifications | 2001 | D | 5 |
| FTR-1408 | Mark read | Planned | P3 | `/me/notifications`* | notifications | Notifications | 1407 | H | 5 |
| FTR-1409 | Result notifications | Planned | P3 | push worker* | notifications | Global | 1406 | D | 5 |
| FTR-1410 | Card-live alert | Planned | P3 | push worker* | notifications | Global | 1406 | D | 5 |
| FTR-1501 | Follow fighter (local) | Client-only | P0 | (local) | — | Fighter | 102 | D | 3 |
| FTR-1502 | Follow promotion (local) | Client-only | P1 | (local) | — | Promotion | 202 | H | 3 |
| FTR-1503 | Save event (local) | Client-only | P1 | (local) | — | Event | 301 | H | 3 |
| FTR-1504 | Favorites screen | Client-only | P0 | (local) | — | Favorites | 1501 | D | 3 |
| FTR-1505 | Favorites feed | Client-only | P1 | (local) | — | Home | 1601 | D | 3 |
| FTR-1506 | Server fighter follows | Planned | P3 | `/me/follows/fighters`* | fighter_follows | Fighter | 2001 | D | 5 |
| FTR-1507 | Server promo follows | Planned | P3 | `/me/follows/promotions`* | promotion_follows | Promotion | 2001 | D | 5 |
| FTR-1508 | Fav next fights | Client-only | P0 | `/fighters/{id}/next-fight` | — | Favorites | 107 | H | 3 |
| FTR-1509 | Manage favorites | Client-only | P2 | (local) | — | Favorites | 1504 | H | 3 |
| FTR-1601 | Feed from local favs | Client-only | P0 | (local+existing) | — | Feed | 1501 | D | 3 |
| FTR-1602 | Followed next fights | Client-only | P0 | `/fighters/{id}/next-fight` | — | Feed | 107 | H | 3 |
| FTR-1603 | Followed recent results | Client-only | P1 | `/fighters/{id}/fights` | — | Feed | 106 | D | 3 |
| FTR-1604 | Followed promo events | Client-only | P1 | `/events?promotion_id=` | — | Feed | 203 | H | 3 |
| FTR-1605 | Cross-promo aggregation | Client-only | P1 | `/events` | — | Feed | 301 | D | 3 |
| FTR-1606 | Server-computed feed | Planned | P3 | `/me/feed`* | multi | Feed | 2001 | W | 5 |
| FTR-1607 | Feed refresh/paginate | Client-only | P0 | (local) | — | Feed | 1601 | H | 3 |

### Historical (17xx) · Records (18xx) · Compare (19xx)
| FTR | Name | Status | Pri | Backend | DB | ESPN | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------|----|-----|--------|------|--------|-------|
| FTR-1701 | Past events archive | Backend Ready | P1 | `/events?status=FINAL`* | events | — | Archive | 305 | D | 2 |
| FTR-1702 | Results archive | Backend Ready | P1 | `/events?status=FINAL`* | competitions | — | Archive | 404 | D | 2 |
| FTR-1703 | Fighter career archive | Implemented | P0 | `/fighters/{id}/fights` | competitions | eventlog | Fighter | 106 | done | — |
| FTR-1704 | Season browsing | Planned | P2 | `/seasons`* | 🔵 seasons | `/seasons` | Archive | — | D | 4 |
| FTR-1705 | Event timeline | Client-only | P2 | `/events` | events | — | Archive | 1701 | D | 3 |
| FTR-1706 | Hall of Fame | Planned | P3 | `/hof`* | 🔵 hof | 🌐 curation | HOF | — | W | 5 |
| FTR-1707 | Legendary fights | Planned | P3 | curated | 🔵 | 🌐 curation | Archive | — | W | 5 |
| FTR-1708 | Era timelines | Planned | P3 | curated | 🔵 | 🌐 curation | Archive | — | W | 5 |
| FTR-1801 | Win streaks | Planned | P1 | `/fighters/{id}/records`* | (computed) | — | Records | 106 | D | 4 |
| FTR-1802 | Finish rate | Planned | P1 | `/fighters/{id}/records`* | (computed) | — | Records | 106 | D | 4 |
| FTR-1803 | Title defense records | Backend Ready | P1 | `/champions`* | rankings | — | Records | 603 | H | 2 |
| FTR-1804 | Most wins in division | Planned | P2 | `/stats/leaders`* | competitors | — | Records | 106 | D | 4 |
| FTR-1805 | Fastest finishes | Planned | P2 | `/stats/leaders`* | competitions | — | Records | 404 | D | 4 |
| FTR-1806 | Most KOs/subs | Planned | P2 | `/stats/leaders`* | competitions | — | Records | 106 | D | 4 |
| FTR-1807 | Longest streaks | Planned | P2 | `/stats/leaders`* | (computed) | — | Records | 106 | D | 4 |
| FTR-1808 | Youngest/oldest champs | Planned | P3 | `/stats/leaders`* | rankings,fighters | — | Records | 601 | D | 4 |
| FTR-1809 | Career milestones | Planned | P3 | `/fighters/{id}/records`* | (computed) | — | Fighter | 106 | D | 4 |
| FTR-1810 | Achievement badges | Planned | P2 | `/fighters/{id}/records`* | (computed) | — | Fighter | 1801 | D | 4 |
| FTR-1811 | Verified all-time records | Planned | — | curated | 🔵 | 🌐 curation | Records | — | M | 5 |
| FTR-1901 | Side-by-side profiles | Client-only | P1 | 2× `/fighters/{id}` | — | — | Compare | 102 | D | 3 |
| FTR-1902 | Physical comparison | Client-only | P1 | 2× `/fighters/{id}` | — | — | Compare | 103 | H | 3 |
| FTR-1903 | Record comparison | Client-only | P1 | 2× `/fighters/{id}` | — | — | Compare | 104 | H | 3 |
| FTR-1904 | Stat comparison | Client-only | P1 | 2× `/fighters/{id}/statistics` | — | — | Compare | 801 | D | 3 |
| FTR-1905 | Common opponents | Planned | P2 | `/compare`* | competitors | — | Compare | 117 | D | 4 |
| FTR-1906 | Head-to-head | Planned | P2 | `/compare`* | competitors | — | Compare | 116 | D | 4 |
| FTR-1907 | Compare endpoint | Planned | P2 | `/compare`* | fighters,competitors | — | Compare | 102 | D | 4 |
| FTR-1908 | Share comparison | Client-only | P2 | (local) | — | — | Compare | 2101 | H | 3 |

### Account (20xx) · Sharing (21xx) · Offline (22xx) · Knowledge Graph (23xx)
| FTR | Name | Status | Pri | Backend | DB | Screen | Deps | Effort | Phase |
|-----|------|--------|-----|---------|----|--------|------|--------|-------|
| FTR-2001 | Sign up / in | Planned | P3 | `/auth/*` (Supabase) | users | Auth | — | W | 5 |
| FTR-2002 | Anonymous mode | Client-only | P0 | — | — | Global | — | H | 3 |
| FTR-2003 | Profile/display name | Planned | P3 | `/me`* | users | Account | 2001 | D | 5 |
| FTR-2004 | Cross-device sync | Planned | P3 | `/me/*`* | multi | Account | 2001 | W | 5 |
| FTR-2005 | Sign out | Planned | P3 | (client+token) | — | Account | 2001 | H | 5 |
| FTR-2006 | Delete account | Planned | P3 | `/me`* (DELETE) | users | Account | 2001 | D | 5 |
| FTR-2007 | Register push token | Planned | P3 | `/me/push-token`* | users.push_token | Account | 2001 | D | 5 |
| FTR-2008 | Migrate local→account | Planned | P3 | `/me/import`* | follows,reminders | Auth | 2001,1501 | D | 5 |
| FTR-2009 | Data export | Planned | P3 | `/me/export`* | multi | Account | 2001 | D | 5 |
| FTR-2010 | Settings screen | Client-only | P0 | (local) | — | Settings | — | D | 3 |
| FTR-2101 | Native share sheet | Client-only | P1 | (local) | — | Global | — | H | 3 |
| FTR-2102 | Deep links | Client-only | P1 | (stable UUIDs) | — | Global | — | D | 3 |
| FTR-2103 | Share fighter | Client-only | P1 | (local) | — | Fighter | 2101 | H | 3 |
| FTR-2104 | Share event | Client-only | P1 | (local) | — | Event | 2101 | H | 3 |
| FTR-2105 | Share result | Client-only | P1 | (local) | — | Fight | 2101 | H | 3 |
| FTR-2106 | Share image cards | Client-only | P2 | (local) | — | Global | 2101 | D | 3 |
| FTR-2107 | Copy link | Client-only | P2 | (local) | — | Global | 2102 | H | 3 |
| FTR-2201 | Cache last-viewed | Client-only | P1 | (local) | — | Global | — | D | 3 |
| FTR-2202 | Offline favorites | Client-only | P0 | (local) | — | Favorites | 1501 | H | 3 |
| FTR-2203 | Sync on reconnect | Client-only | P1 | (local) | — | Global | — | D | 3 |
| FTR-2204 | Offline indicator | Client-only | P1 | (local) | — | Global | — | H | 3 |
| FTR-2205 | ETag/cache headers | Planned | P2 | (middleware) | — | Global | — | D | 1 |
| FTR-2206 | Stale-while-revalidate | Client-only | P2 | (local) | — | Global | 2201 | D | 3 |
| FTR-2207 | Cache size config | Client-only | P3 | (local) | — | Settings | 2201 | H | 3 |
| FTR-2301 | Fighter→events | Implemented | P1 | `/fighters/{id}/fights` | competitions | Fighter | 106 | done | — |
| FTR-2302 | Event→fighters | Implemented | P0 | `/events/{id}` | competitors | Event | 302 | done | — |
| FTR-2303 | Venue→events | Planned | P2 | `/venues/{id}/events`* | events | Venue | 310 | D | 4 |
| FTR-2304 | Promotion→graph | Backend Ready | P1 | `/rankings`+`/events` | multi | Promotion | 203,206 | H | 2 |
| FTR-2305 | WeightClass→graph | Backend Ready | P1 | `/rankings`+`/fighters` | multi | WeightClass | 703,704,705 | H | 2 |
| FTR-2306 | Ranking→next fight | Backend Ready | P1 | `/rankings`+`/next-fight` | multi | Rankings | 501,107 | H | 2 |
| FTR-2307 | Opponent web | Planned | P2 | `/compare`* | competitors | Fighter | 117 | D | 4 |
| FTR-2308 | Official→fights | Planned | P3 | `/officials/{id}`* | 🔵 officials | Official | 408 | D | 4 |
| FTR-2309 | Related fighters | Planned | P2 | `/fighters?weight_class=`* | fighters | Fighter | 115 | D | 4 |
| FTR-2310 | Graph explorer | Planned | P3 | (multi) | multi | Discover | 2301-2309 | W | 4 |

`*` = planned route (not yet in `router.py`).

---

## 4. Summary Rollups

### 4.1 By Status
| Status | Count | Share |
|--------|-------|-------|
| Implemented (route exists & tested) | 30 | 12% |
| Backend Ready (data synced, no route) | 34 | 14% |
| Client-only (Flutter, no backend) | 92 | 37% |
| Planned (new backend work) | 85 | 34% |
| Not feasible (⛔ no free data) | 6 | 2% |
| **Total catalogued** | **247** | 100% |

> **Buildable for free (excl. Not feasible): 241.** The "felt" product is dominated by **Client-only + Backend Ready = 126 features** that need little or no new backend — that's the fast lane.

### 4.2 By Priority
| Priority | Count | Meaning |
|----------|-------|---------|
| P0 (MVP) | 58 | first public build |
| P1 (v1.0) | 78 | first major update |
| P2 (v2.0) | 71 | depth/breadth |
| P3 (future/optional) | 40 | mostly account+push+curated |

### 4.3 By Phase
| Phase | Theme | Count | Typical effort |
|-------|-------|-------|----------------|
| 1 | Finish Production Readiness (Redis, scheduler, Docker, health) | 1 user-facing (FTR-2205) + infra | 1–2 wks |
| 2 | Expose already-synced data (rankings/champions/status/roster/headshots) | 34 | days each (whole phase ~1 wk) |
| 3 | Client-first (favorites/feed/compare/calendar/sharing/offline/local notif) | 92 | 1–2 wks |
| 4 | Computed/aggregate (records/leaders/officials/per-fight detail) | 40 | 2–3 wks |
| 5 | Optional heavy (accounts/push/curated/news/multi-league) | 40 | months |

### 4.4 Effort distribution (of buildable features)
| Effort | Count | Notes |
|--------|-------|-------|
| Hours (H) | ~70 | mostly Backend-Ready + small client |
| Days (D) | ~120 | the bulk |
| Weeks (W) | ~14 | account layer, curation, news |
| Months (M) | 1 | verified all-time records (curation-heavy) |
| Done | 30 | already shipped |

---

## 5. One Endpoint → Many Features (why each ESPN endpoint earns its keep)

This is the strongest argument for the Phase-2 ordering: a *single* new backend route unlocks a *cluster* of features because the data is already synced.

| ESPN endpoint (→ backend route) | # features | Feature IDs |
|---|---|---|
| **`/leagues/{slug}/rankings/{cat}` → `GET /rankings`** | **13** | FTR-005, 109, 501, 502, 503, 504, 505, 506, 507, 509, 704, 1004, 2306 |
| **`/rankings` (champion flag) → `GET /champions`** | **11** | FTR-006, 110, 601, 602, 603, 604, 605, 606, 705, 1803, 2305 |
| **`/athletes/{id}` → `GET /fighters/{id}`** | **10** | FTR-102, 103, 104, 108, 113, 114, 1201, 1901, 1902, 2309 |
| **`/events/{id}` → `GET /events/{id}`** | **9** | FTR-002, 003, 302, 303, 304, 310, 311, 1301, 2302 |
| **`/competitors/{id}/statistics` → fight stats** | **8** | FTR-405, 802, 803, 804, 809, 810, 811, 812 |
| **`/competitions/{id}/status` → result fields** | **7** | FTR-004, 404, 407, 1702, 1805, 1806, 1410 |
| **`/athletes/{id}/eventlog` → `/fighters/{id}/fights`** | **8** | FTR-106, 111, 112, 120, 1603, 1703, 1801, 1802 |
| **`/events` walk → `GET /events`** | **9** | FTR-001, 301, 305, 306, 307, 308, 1301, 1508, 1605 |
| **ESPN-CDN headshot (from `espn_id`)** | **3+** | FTR-108, 1201, + visual lift across every fighter surface |
| **`/competitions/{id}/officials` → `/officials`** | **3** | FTR-408, 2308, (referee stats) |

**Reading:** exposing just the **two rankings routes** lights up **~24 features** across Home, Fighters, Champions, Weight Classes, Discover, Records, and the Knowledge Graph — from data that's *already refreshed every 12 hours*. That is the single highest-leverage move in the whole plan.

---

## 6. Cross-reference index

- **What to build / user stories / navigation** → `product-requirements.md`
- **Where data comes from / ERD / graph / scheduler / cache** → `data-specification.md`
- **Raw ESPN endpoints & fields** → `espn-mma-api-reference.md`
- **Backend Production-Readiness state & the Claude continuation prompt** → `assessment.md`, `continuation-prompt.md`
- **No-AI / free-data strategy & phased rationale** → `feature-master-plan.md`
