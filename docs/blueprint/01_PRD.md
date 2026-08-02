# Part 1 — Master Product Requirements Document (PRD)

## Vision

A single app that answers one question better than anything else on the market: **"When is my fighter fighting, and how do I watch it?"** — expanded to every MMA organization the data will support, not just the UFC. Everything else in the product (rankings, stats, history, discovery) exists to deepen that core loop, not to compete with it.

## Product principles

1. **Coverage over depth, depth over decoration.** Adding a new organization (once verified) is more valuable than a fifth way to visualize stats for UFC alone.
2. **Never show a number we didn't verify.** A missing stat is an honest empty state, not a placeholder.
3. **The countdown is the emotional core.** Every "next fight" and "next event" surface is designed around the countdown-timer moment, not buried under it.
4. **Free forever, by design constraint, not marketing.** Every architectural decision (see `08_DATA_SOURCE_MATRIX.md`) assumes zero paid infrastructure, permanently — this shapes caching, notification, and sync design, not just hosting cost.

## Modules

### Home
The first screen after launch. A personalized feed: the user's followed fighters' next fights (with countdowns), followed organizations' next events, and a short "what's happening" strip (live or very-recent results). Empty and pre-follow states matter as much as the populated state — see `04_FLUTTER_SCREENS.md`.

### Dashboard
A denser, more configurable view than Home — for a returning power user who wants everything at a glance: all followed fighters' status, all followed orgs' upcoming/previous events, and quick links into Search/Discover. Distinguished from Home by density and lack of "storytelling" framing — Home is a feed, Dashboard is a control panel.

### Fighters
Search, browse, and view full fighter profiles: record, physical stats, current ranking(s), weight class, next fight (with countdown), and fight history (past + upcoming).

### Organizations
Browse every organization the backend has verified. Each org's page: logo/branding, country, next event (countdown), previous event, and a link into that org's full event archive and rankings (where verified to exist).

### Events
Browse upcoming and past events, globally or scoped to one organization. Each event: full card, competitions in order, per-bout status/result once available, broadcast info (where to watch), and venue.

### Fights
The individual-bout view — reached from an event's card or a fighter's fight history. Shows both competitors, weight class, card position, and (once the event has concluded) the method/round/time result.

### Rankings
Per-organization, per-category ranking lists (UFC only, until verified elsewhere). Filterable by weight class and gender where the underlying data supports it (see the documented pound-for-pound gender-filter gap).

### Champions
A cross-organization "who holds gold right now" view — derived from ranking data where `is_champion` is true, grouped by organization and weight class. **Requires Verification** for any organization beyond UFC.

### Statistics
A fighter's career numbers (strike accuracy, takedown average, etc.) from their most recently synced appearance — labeled honestly as "most recent recorded stats," not implied to be live-updating mid-fight.

### Historical Archive
Past events and results, browsable by organization and by date, functioning as the "encyclopedia" layer of the app. Built on the same verified event/competition data as the live app — no separate data source.

### Search
Global search across fighters, organizations, events, and venues (already implemented backend-side — see `07_API_COVERAGE_MAP.md`). The primary entry point for a user who knows what they're looking for.

### Discover
The entry point for a user who does *not* know what they're looking for: trending/upcoming big events, newly active organizations, and (later, once rankings coverage broadens) notable ranking movement. Distinguished from Search by intent, not mechanism.

### Calendar
A month/week/agenda view of upcoming events across all followed (or all known) organizations — the natural home for the countdown/timezone feature described in the original product motivation (a user in Pakistan needing accurate local fight times).

### Notifications
In-app notification center plus the push-notification system described in full in `09_NOTIFICATION_MATRIX.md`.

### User Features
Follow (fighter or organization), Favorite, personal settings, and the notification preferences that control the matrix above. No account "tiers" — a single free feature set for every signed-in user.

### Media Center
Broadcast/"where to watch" information surfaced contextually on events (verified data). Fighter/event imagery beyond ESPN's own CDN is **Requires Verification** and is designed for but not built until `entity_images` (already scaffolded backend-side) has a second provider wired in.

### AI (Future)
Explicitly Phase 5 and explicitly not specified in feature-by-feature detail in this version of the blueprint (per the "no premature commitment to unverified capability" principle) — see `03_DEVELOPMENT_PHASES.md` for the placeholder and `11_PRODUCT_REVIEW.md` for why it's intentionally underspecified here.

### Settings
Account, notification preferences, theme (light/dark), timezone/locale, and data-usage preferences (e.g. Wi-Fi-only sync, relevant for users on limited mobile data).

### Admin
Not a user-facing module. Placeholder for future operator tooling built on the backend's existing `/health/sync-status` and `/health/scheduler-status` endpoints (already implemented) — an internal dashboard, not part of the consumer app. Scoped out of Flutter entirely; see `11_PRODUCT_REVIEW.md`.

### Platform
Cross-cutting concerns: offline behavior, deep linking, accessibility, and state management — specified per-screen in `04_FLUTTER_SCREENS.md` rather than as a separate module screen.
