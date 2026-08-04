# MMA App — Master Feature Plan (No-AI, Free-Data Edition)

**Prepared:** 2026-07-30
**Scope:** Grounds every planning decision in the *actual* backend code (extracted & inspected, not assumed).
**Your constraints (locked in):** ❌ No AI predictions · ❌ No AI chat/assistant · ❌ No AI summaries · ❌ No AI of any kind · ❌ No betting · ❌ No paid services / paid APIs.

---

## 0. Ground Truth — What the Backend *Actually* Is Right Now

I extracted the zip and read the source. The often-quoted "15 endpoints" number is roughly right for *routes*, but the **data & model layer is further along than the routes expose**. This distinction drives the whole plan.

### 0.1 Endpoints that actually exist (registered in `router.py`)
| # | Method + Path | Returns |
|---|---|---|
| 1 | `GET /fighters?q=` | Search fighters by name (paged) |
| 2 | `GET /fighters/{id}` | Full fighter profile |
| 3 | `GET /fighters/{id}/next-fight` | Next scheduled bout |
| 4 | `GET /fighters/{id}/statistics` | Career stats (last synced) |
| 5 | `GET /fighters/{id}/fights` | Full fight history (paged) |
| 6 | `GET /events?promotion_id=` | Upcoming events (paged) |
| 7 | `GET /events/{id}` | Full event card (competitions + broadcasts) |
| 8 | `GET /promotions?` | List/search promotions |
| 9 | `GET /promotions/{id}` | Promotion by id |
| 10 | `GET /competitions/{id}` | Single bout detail |
| 11 | `GET /venues` | List venues |
| 12 | `GET /venues/{id}` | Venue by id |
| 13 | `GET /weight-classes` | List all weight classes |
| 14 | `GET /health` | Liveness |
| 15 | `GET /health/db` | DB readiness |

### 0.2 The important hidden truth — data models WITHOUT endpoints
These tables exist and (for rankings) are **actively populated by the scheduler**, but **no API route serves them yet**:

| Model / table | State | Gap |
|---|---|---|
| `Ranking` | ✅ synced every 12h by `sync_rankings`, has `rank`, `is_champion`, `trend`, `title_defenses` | ❌ **No `/rankings` or `/champions` endpoint.** Data sits in DB unseen. |
| `Broadcast` | ✅ synced, ✅ **served** inside event detail | (exposed) |
| `Statistic` | ✅ synced (per-competitor fight stats + career) | ✅ served via `/fighters/{id}/statistics` |
| `User` | table only | ❌ no auth, no endpoints |
| `FighterFollow` / `PromotionFollow` | tables only | ❌ favorites not exposed |
| `Reminder` | table only | ❌ no reminder endpoints, no sender |
| `Notification` | table only | ❌ no notification endpoints, no push |

**Takeaway #1:** Rankings/Champions is the single highest-leverage feature — the data is *already in the database*; it just needs an endpoint (hours of work, not weeks).
**Takeaway #2:** The "user layer" (accounts, favorites, reminders, notifications) is scaffolded as empty tables. It needs auth + endpoints + a push provider. This is the biggest real chunk of remaining work.

### 0.3 Data sources — what's wired
- **ESPN public API** — the *only* live source. Drives fighters, events, competitions, competitors, venues, promotions, weight classes, rankings, broadcasts, statistics.
- **TheSportsDB** — **configured but NOT used.** `THESPORTSDB_BASE_URL` + free key `"3"` sit in config and there's an unused `thesportsdb_id` column, but **no client code calls it yet.** It's a ready on-ramp, not a live source.
- **Redis** — dependency + `REDIS_URL` present; **no cache code written** (Production Readiness Phase 1 was interrupted at design — see the companion `assessment.md`).

### 0.4 Verified health (I ran it)
48 tests pass · 91% coverage · `ruff` clean · `mypy --strict` clean. The base is solid to build on.

---

## 1. Feature Audit — 25 Categories, Sub-Feature by Sub-Feature

Legend:
✅ **Supported now** (existing endpoint/data) · 🟡 **New endpoint** (data exists, no route) · 🔵 **New table/model** · 🌐 **Needs external data beyond ESPN** · 📱 **Flutter-only** (no backend change) · ⛔ **Not feasible on free data**

### 1. Home Screen
| Sub-feature | Status | Notes |
|---|---|---|
| Upcoming events list | ✅ | `GET /events` |
| Next big event hero card | ✅ | `GET /events` (take first) |
| Live/in-progress event banner | ✅ | `event.status == LIVE` (synced every 3 min) |
| Latest results strip | 🟡 | Need `GET /events?status=FINAL` filter (data exists) |
| Trending/top-ranked fighters | 🟡 | Needs rankings endpoint |
| Personalized "your fighters" row | 🟡🔵 | Needs favorites (user layer) |
| Layout, ordering, theming | 📱 | Pure client |

### 2. Fighter Profiles
| Sub-feature | Status | Notes |
|---|---|---|
| Name, nickname, photo, nationality | ✅ | `GET /fighters/{id}` |
| Physicals (height/weight/reach/stance) | ✅ | on model |
| Record (W-L-D) | ✅ | on model |
| Career statistics | ✅ | `/fighters/{id}/statistics` |
| Full fight history | ✅ | `/fighters/{id}/fights` |
| Next fight | ✅ | `/fighters/{id}/next-fight` |
| Current ranking badge | 🟡 | Rankings data exists, no route |
| Win method breakdown (KO/Sub/Dec %) | 🟡 | Derivable from fight history/stats; add computed field |
| Title history / championship reigns | 🟡🔵 | Partially from rankings (`is_champion`, `title_defenses`); full reign history needs curation |
| Social links / camp / coach | 🌐 | ESPN doesn't provide reliably; TheSportsDB partial |
| Head-to-head vs opponent | 🟡 | Compute from shared competitions |

### 3. Organizations (Promotions)
| Sub-feature | Status | Notes |
|---|---|---|
| List/search promotions | ✅ | `GET /promotions` |
| Promotion detail (logo, country, site) | ✅ | on model |
| Events by promotion | ✅ | `GET /events?promotion_id=` |
| Roster by promotion | 🟡 | Derivable (fighters via competitions); add endpoint |
| Promotion rankings | 🟡 | Rankings are promotion-scoped already |
| History / founding / owner bios | 🌐 | Manual/TheSportsDB |

### 4. Events
| Sub-feature | Status | Notes |
|---|---|---|
| Upcoming events (paged) | ✅ | `GET /events` |
| Event detail / full card | ✅ | `GET /events/{id}` |
| Broadcast info (network/region) | ✅ | Included in event detail |
| Venue info | ✅ | via venue relation |
| Past/finished events | 🟡 | Add status filter |
| Filter by promotion | ✅ | query param |
| Filter by date range / country | 🟡 | Add query params |
| Ticket links | 🌐 | Not in ESPN |

### 5. Fight Details
| Sub-feature | Status | Notes |
|---|---|---|
| Bout matchup (two fighters) | ✅ | `GET /competitions/{id}` |
| Card segment (main/prelim/early) | ✅ | on model |
| Result (method/round/time) | ✅ | on model |
| Per-fighter fight statistics | ✅ | `Statistic` per competitor |
| Weight class of bout | ✅ | relation |
| Round-by-round scorecards | ⛔ | Not in ESPN free; judges' scores unavailable |
| Play-by-play / live commentary | ⛔ | No free feed |

### 6. Rankings
| Sub-feature | Status | Notes |
|---|---|---|
| Divisional rankings (top 15) | 🟡 | **Data synced, no endpoint** — build `GET /rankings` |
| Pound-for-pound | 🟡 | `category` field supports it |
| Rank trend (up/down) | 🟡 | `trend` field exists |
| Ranking history over time | 🔵 | Would need snapshot table (currently overwrites) |
| Filter by promotion/division | 🟡 | Data is promotion+division scoped |

### 7. Champions
| Sub-feature | Status | Notes |
|---|---|---|
| Current champion per division | 🟡 | `is_champion` flag in rankings |
| Title defenses count | 🟡 | `title_defenses` field |
| Champion showcase screen | 🟡📱 | Endpoint + client |
| Interim/lineage history | 🔵🌐 | Needs curated reign table |

### 8. Search
| Sub-feature | Status | Notes |
|---|---|---|
| Search fighters | ✅ | `GET /fighters?q=` |
| Search promotions | ✅ | `GET /promotions?q=` |
| Search events | 🟡 | Add name search param |
| Unified/global search | 🟡 | Add aggregator endpoint |
| Recent searches / suggestions | 📱 | Client-side local storage |
| Fuzzy/typo tolerance | 🟡 | DB trigram index (nice-to-have) |

### 9. Favorites
| Sub-feature | Status | Notes |
|---|---|---|
| Follow fighter | 🟡🔵 | `FighterFollow` table exists, **no endpoint/auth** |
| Follow promotion | 🟡🔵 | `PromotionFollow` table exists |
| Favorites list | 🟡🔵 | Needs user layer |
| Follow event (reminder) | 🔵 | `Reminder` table exists |
| Local-only favorites (no login) | 📱 | **Recommended MVP** — store on device, skip auth entirely |

### 10. Personalized Feed
| Sub-feature | Status | Notes |
|---|---|---|
| Feed of followed fighters' fights | 🟡🔵 | Needs favorites |
| Feed from local favorites | 📱🟡 | Client queries `/fighters/{id}/next-fight` for saved IDs — **no backend user layer needed** |
| Cross-promotion aggregation | ✅ | Data already multi-promotion |

### 11. News
| Sub-feature | Status | Notes |
|---|---|---|
| MMA news headlines | 🌐 | ESPN has a news endpoint (public, unofficial) — feasible but scrape-ish |
| News per fighter | 🌐 | Same source, filter |
| Article reader | 📱🌐 | Link out to source |
| Curated editorial | ⛔ | You'd be a publisher; not realistic solo |

### 12. Videos
| Sub-feature | Status | Notes |
|---|---|---|
| Highlight/embed links | 🌐 | YouTube search links only (no official free feed) |
| Full fight video | ⛔ | Licensed content — impossible free |
| Fighter media gallery | 🌐 | Limited via TheSportsDB fanart |

### 13. Compare Fighters
| Sub-feature | Status | Notes |
|---|---|---|
| Side-by-side stats | 🟡 | Call `/fighters/{id}` ×2, client renders; optional `GET /compare?a=&b=` |
| Physical comparison | ✅ | data present |
| Common opponents | 🟡 | Compute from competitions |
| Tale of the tape | 📱 | Client layout |

### 14. Notifications
| Sub-feature | Status | Notes |
|---|---|---|
| Event-start reminders | 🔵 | `Reminder` table exists, no sender |
| Fighter-fight alerts | 🔵 | Needs favorites + push |
| Push delivery | 🌐🔵 | **FCM (Firebase Cloud Messaging) — free tier**; `User.push_token` field already exists |
| Local notifications (device only) | 📱 | **Recommended MVP** — schedule on device from event times, no backend/push at all |
| In-app notification center | 🔵 | `Notification` table exists |

### 15. Statistics Hub
| Sub-feature | Status | Notes |
|---|---|---|
| Per-fighter career stats | ✅ | existing |
| Per-fight stats | ✅ | `Statistic` per competitor |
| Division leaders (most KOs, etc.) | 🟡 | Aggregate endpoint over stats |
| Records leaderboards | 🟡 | Aggregate queries |
| Advanced analytics dashboards | 📱🟡 | Client viz over aggregate endpoints |

### 16. Weight Classes
| Sub-feature | Status | Notes |
|---|---|---|
| List divisions | ✅ | `GET /weight-classes` |
| Division detail | ✅ | on model (limits, gender) |
| Fighters in a division | 🟡 | Filter fighters by weight_class |
| Division rankings/champion | 🟡 | Rankings are division-scoped |

### 17. Event Calendar
| Sub-feature | Status | Notes |
|---|---|---|
| Calendar view of events | 📱 | Client renders `GET /events` by date |
| Add to device calendar | 📱 | Client (ICS/native) |
| Filter by month/promotion | 🟡 | Add date filters |

### 18. Hall of Fame
| Sub-feature | Status | Notes |
|---|---|---|
| HOF inductee list | 🔵🌐 | **No free source** — must curate manually into a table |
| Inductee bios | 🌐 | Manual/TheSportsDB |
| Legendary fights | 🔵🌐 | Manual curation |

### 19. Fight Timeline
| Sub-feature | Status | Notes |
|---|---|---|
| Fighter career timeline | ✅ | Build from fight history (client) |
| Event-day timeline (card order) | ✅ | `match_number` + `card_segment` |
| Historical era timeline | 🔵🌐 | Needs curation |

### 20. Records & Achievements
| Sub-feature | Status | Notes |
|---|---|---|
| Win streaks | 🟡 | Compute from fight history |
| Finish rate | 🟡 | Compute from results |
| Title defense records | 🟡 | `title_defenses` in rankings |
| "Most wins in division" etc. | 🟡 | Aggregate queries |
| Verified all-time records | 🌐 | Some need curation for accuracy |

### 21. User Account
| Sub-feature | Status | Notes |
|---|---|---|
| Sign up / login | 🔵 | `User` table exists, **no auth built** |
| Profile / display name | 🔵 | field exists |
| Cross-device sync | 🔵 | Needs auth |
| **Anonymous / no-account mode** | 📱 | **Recommended MVP** — everything personal stored on device |

### 22. Offline Support
| Sub-feature | Status | Notes |
|---|---|---|
| Cache last-viewed data | 📱 | Client (sqflite/Hive) |
| Offline favorites | 📱 | Client storage |
| Sync-on-reconnect | 📱 | Client logic (backend already REST) |
| ETag/HTTP caching | 🟡 | Backend can add cache headers (pairs with Redis phase) |

### 23. Sharing
| Sub-feature | Status | Notes |
|---|---|---|
| Share fighter/event/card | 📱 | Native share sheet |
| Deep links | 📱🟡 | Client + stable IDs (already UUIDs) |
| Share image cards | 📱 | Client renders |

### 24. Discover
| Sub-feature | Status | Notes |
|---|---|---|
| Browse by promotion/division | ✅ | existing filters |
| Featured/upcoming | ✅ | events |
| Trending fighters | 🟡 | rankings-based |
| Editorial collections | ⛔/🔵 | Manual curation only |

### 25. Advanced Filters
| Sub-feature | Status | Notes |
|---|---|---|
| Filter events (date/promotion/status/country) | 🟡 | Extend query params |
| Filter fighters (division/nationality/record) | 🟡 | Extend query params |
| Sort options | 🟡 | Add sort params |
| Saved filters | 📱 | Client storage |

---

## 2. Realistic Feature Count (after removing what you don't want / can't have)

Starting from the ~350-feature vision across 32 modules:

| Bucket | Approx removed | Why |
|---|---|---|
| AI features (predictions, chat, summaries, "smart" anything) | ~70–90 | You explicitly don't want them |
| Betting / odds / picks | ~25–35 | Excluded + mostly paid data |
| Paid-API / premium-data features (live scorecards, PBP, video, deep analytics) | ~30–40 | No free source |
| Community/social needing moderation (comments, forums, UGC, chat) | ~30–40 | Moderation infra = ongoing cost/risk |
| Duplicates & variations of the same core feature (the same list re-skinned per screen) | ~60–80 | The 350 is inflated by restating features per module |

**Realistic, buildable-for-free, unique features: ~110–140.**
Of those, a **tight, genuinely valuable MVP is ~35–45 features** (see roadmap). The rest are polish/expansion.

> Blunt version: the "350 features" is really **~120 real distinct features** wearing 350 costumes. Don't let the number set your expectations.

---

## 3. Data-Source Gap Analysis

| Need | ESPN public API | TheSportsDB free (key "3") | Not available free | Manual / scrape |
|---|---|---|---|---|
| Fighters, records, physicals | ✅ Strong | Partial (bios, fanart) | — | — |
| Events, cards, results | ✅ Strong | Partial | — | — |
| Rankings & champions | ✅ (already synced) | ❌ | — | — |
| Broadcasts | ✅ | ❌ | — | — |
| Per-fight statistics | ✅ (basic) | ❌ | Round-by-round detail | — |
| Weight classes / venues | ✅ | Partial | — | — |
| Promotion logos/branding | Partial | ✅ (logos, badges, fanart) | — | — |
| News headlines | ⚠️ Unofficial news endpoint | ❌ | Curated editorial | Link-out |
| Video highlights | ❌ | Fanart only | ✅ Full fights (licensed) | YouTube links |
| Judges' scorecards / PBP | ❌ | ❌ | ✅ | — |
| Hall of Fame / lineage / historical records | ❌ | ⚠️ some legends | Verified reign history | ✅ Must curate |
| Social/camp/coach info | ⚠️ spotty | ⚠️ some | — | Curate |
| Odds / betting | ❌ | ❌ | ✅ (paid) | — |

**Two clear free-source moves you haven't tapped yet:**
1. **Turn on TheSportsDB** (already in config, unused) → fills promotion logos, fighter fanart, some legend bios. Zero cost.
2. **Add a tiny curated tables layer** (Hall of Fame, notable historical reigns) — a few hundred hand-entered rows, one-time effort, unlocks 3 whole "categories" that otherwise are impossible.

---

## 4. Prioritized Build Order (solo-dev realistic)

### PHASE 1 — Finish Production Readiness (do this FIRST, ~1–2 weeks)
*Do not build features on an unhardened base.* Interrupted at Redis design (see `assessment.md` + `continuation-prompt.md`).
- Redis cache-aside layer (DI-overridable, `fakeredis` in tests)
- Scheduler job-store hardening / separate scheduler process
- Structured logging + Prometheus metrics
- Health endpoints (already have `/health`, `/health/db`; add `/health/ready`, dependency checks)
- Performance audit (N+1s), config hardening, production Dockerfile, docs
- **Also here:** flip on TheSportsDB client for logos/images (small, low-risk, high visual payoff)

### PHASE 2 — Expose the data you ALREADY have (~1 week, huge value/effort ratio)
These are nearly free because the data is already synced:
- `GET /rankings` (+ filter by promotion/division/category) 🟡
- `GET /champions` (from `is_champion`) 🟡
- Event status filter (`?status=FINAL|LIVE|SCHEDULED`) + past-events 🟡
- Fighters-in-division filter 🟡
- Roster-by-promotion 🟡
- Global search endpoint 🟡

### PHASE 3 — Client-first features (no/low backend, fast wins) (~1–2 weeks)
- Home screen composition, Discover, Event Calendar, Fight Timeline (client) 📱
- Compare Fighters (2× existing calls) 📱🟡
- **Local favorites + local notifications** 📱 — deliver Favorites/Feed/Reminders *without* building auth
- Offline caching, Sharing, deep links 📱

### PHASE 4 — Computed/aggregate features (~2–3 weeks)
- Records & Achievements (streaks, finish rate) 🟡
- Statistics Hub leaderboards / division leaders 🟡
- Win-method breakdowns, common opponents, head-to-head 🟡
- Advanced filters & sorting across endpoints 🟡

### PHASE 5 — The heavy/optional layer (only if you want accounts) (~3–5 weeks)
- User accounts + auth (`User` table → JWT), server-side favorites/feed sync 🔵
- Push notifications via **FCM free tier** (`push_token` exists) + reminder sender 🔵🌐
- In-app notification center 🔵
- **Curated tables:** Hall of Fame, historical reigns, legendary fights 🔵 (manual)
- TheSportsDB news/fanart enrichment 🌐

> If you never build Phase 5's account layer, **the app still works fully** in anonymous/local mode. Treat accounts as optional, not foundational.

---

## 5. The Honest Truth

**Realistic for a solo dev (do these):**
Everything in Phases 1–4. That's a genuinely good, complete-feeling MMA app: home, fighters, events, cards, results, rankings, champions, search, compare, calendar, records, stats, local favorites & reminders, offline, sharing. ~35–45 MVP features, expandable to ~110–140.

**Sounds cool, but NO free data source (don't promise these):**
- Round-by-round scorecards & judges' scores ⛔
- Live play-by-play / real-time commentary ⛔
- Full fight video / official highlights ⛔ (licensed)
- Betting odds / picks ⛔
- Verified all-time historical records & full title lineage without manual curation ⛔

**Days vs months:**
- **Days each:** rankings/champions endpoints, status filters, compare, most client screens, local favorites/notifications. (Phase 2–3.)
- **1–2 weeks:** Production Readiness (Phase 1), aggregate/records features (Phase 4).
- **Months (combined):** full user-account + push + server-sync layer, plus meaningful curated Hall-of-Fame/history content (Phase 5). This is where "just add accounts and notifications" secretly hides most of the remaining effort.

**What the MVP should actually be:**
> A polished, **account-free** UFC app: browse events & full cards, live/finished status, fighter profiles with stats & history, **rankings & champions**, search, compare, calendar, and **on-device favorites + local reminders**. All powered by the *current* backend + Phase 2 endpoints. No login, no push server, no AI, no paid anything. Ships in weeks, not months.

**On the 350 number:**
It's ~120 real distinct features restated across 32 modules. Removing AI (~70–90), betting (~25–35), paid-data (~30–40), and moderation-heavy community (~30–40) — then de-duplicating — lands you at **~110–140 buildable features**, with a **~40-feature MVP** that already feels complete. Build the MVP, ship it, then expand from Phase 4/5 based on real usage.

---

## Appendix — Immediate Next Actions
1. **Finish Phase 1** using the ready-to-paste `continuation-prompt.md` (Redis first — it was interrupted at design).
2. **Then Phase 2** — the fastest value: expose rankings/champions (data already in DB).
3. **Decide early:** anonymous-only (skip Phase 5) vs accounts. This one choice determines whether the project is a *few-weeks* app or a *few-months* app.
