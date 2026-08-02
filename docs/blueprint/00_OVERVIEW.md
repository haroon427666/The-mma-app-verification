# MMA App — Master Product Blueprint

**Status:** Source of truth for product direction, effective from the end of Backend Milestone 5.
**Scope of this document:** Product, UX, information architecture, and mobile app design only. No backend code changes are implied or required by anything in this blueprint. Where a feature depends on data the backend has not verified, it is explicitly marked **Requires Verification** — see `08_DATA_SOURCE_MATRIX.md`.

## How to read this blueprint

| File | Contents |
|---|---|
| `01_PRD.md` | Product vision, modules, and what each module actually does |
| `02_FEATURE_REGISTRY.md` | Every feature, individually specified (ID, priority, dependencies, verification status) |
| `03_DEVELOPMENT_PHASES.md` | Which features ship in which phase, and why |
| `04_FLUTTER_SCREENS.md` | Every screen, fully specified (states, navigation, accessibility) |
| `05_NAVIGATION_MAP.md` | The complete navigation graph |
| `06_DATABASE_ENTITY_MAP.md` | Entity relationships (descriptive, matches the real backend schema) |
| `07_API_COVERAGE_MAP.md` | Every endpoint the app needs, mapped to implementation status |
| `08_DATA_SOURCE_MATRIX.md` | Where every piece of data actually comes from, and its verification status |
| `09_NOTIFICATION_MATRIX.md` | Every notification type, fully specified |
| `10_DESIGN_SYSTEM.md` | Visual language for the Flutter app |
| `11_PRODUCT_REVIEW.md` | Critical self-review — risks, gaps, and challenged assumptions |

## Ground rules this blueprint follows

- **No monetization.** No subscriptions, premium tiers, ads, or in-app purchases appear anywhere in this document, per instruction.
- **No paid infrastructure.** Every feature is designed to work on the free-tier stack already established (FastAPI + Postgres + APScheduler + Firebase Cloud Messaging free tier).
- **No invented data.** Every feature that displays data is traced back to a real, verified backend source in `08_DATA_SOURCE_MATRIX.md`. Where verification is outstanding, the feature is marked accordingly and is not blocked from being *designed* — only from being *built* — until verification completes.
- **The backend is the foundation, not a redesign target.** Every API referenced in this blueprint either already exists (see `PROJECT_STATUS.md`/`API_REFERENCE.md` in the backend repo) or is a natural, additive extension of the existing Repository → Service → API pattern. Nothing here requires re-architecting what's already built.

## What's actually true about the data today (read this before anything else)

Per the backend's own verification record (`PROJECT_STATUS.md`, Milestones 3.75–5):

**Verified and safe to build on:**
- UFC: events, competitions/bouts, competitors, fighters, venues, weight classes, broadcasts, per-bout status and results (method/detail/round/time), rankings (with a documented gender-filter gap for pound-for-pound categories).
- Full-text search across fighters/promotions/events/venues.
- Fighter career statistics (from most recent synced appearance), fight history.

**Explicitly NOT verified — anything built on these must be marked accordingly:**
- Any organization other than UFC at full data depth. Bellator, "Absolute" (ACB/ACA), Affliction, and Bang Fighting have had *some* fields spot-checked (see `PROJECT_STATUS.md` Milestone 5), but full event/competition/broadcast/ranking coverage is confirmed for UFC only.
- Rankings for any non-UFC organization (no `rankings` resource was found linked on a non-UFC league object).
- Fighter biography, social links, walk-around weight, bonuses (Fight of the Night etc.), judging scorecards, live strike-by-strike data, betting odds beyond the basic verified odds endpoint, and fighter images from any source other than ESPN's own CDN.
- Live/in-progress event status — only `STATUS_SCHEDULED` and `STATUS_FINAL` have ever been observed in real data.

This blueprint treats the above as a hard boundary: any screen or feature depending on unverified data is designed *end-to-end* (so no future redesign is needed once verification completes) but is sequenced into a later phase and flagged, never silently assumed to work.
