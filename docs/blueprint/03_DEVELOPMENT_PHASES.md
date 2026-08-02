# Part 3 — Development Phases

Every feature in `02_FEATURE_REGISTRY.md` belongs to exactly one phase below. The rule for placement: a feature moves to the earliest phase where (a) its backend dependency is Ready or trivially Planned, and (b) it doesn't depend on a feature placed in a later phase.

## Phase 1 — Foundation
**Goal: the backend and Flutter project scaffolding exist; nothing user-facing yet.**

This phase is largely already complete on the backend side (Milestones 1–5). What remains for Phase 1 specifically:
- Flutter project scaffold, design system implementation (`10_DESIGN_SYSTEM.md`), navigation shell (`05_NAVIGATION_MAP.md`) with placeholder screens.
- API client layer wired to the existing, verified backend endpoints.
- Authentication (USER-03) — the one genuine backend gap blocking everything personalized. This is a backend milestone, not a Flutter one, but Phase 1 doesn't complete until it exists, because Phase 2's follow/notification features depend on it.

## Phase 2 — Flutter MVP
**Goal: the core countdown/tracking promise, fully working, for verified data only.**

Features: HOME-01, HOME-02, HOME-04, FIGHT-01, FIGHT-02, FIGHT-03, FIGHT-06, ORG-01, ORG-02, ORG-03, EVT-01, EVT-02, EVT-03, EVT-04, SRCH-01, CAL-01, SET-01, SET-02, USER-01, USER-02, USER-04.

## Phase 3 — Advanced Features
**Goal: depth for the fan who's already hooked by the MVP.**

Features: DASH-01, DASH-02, FIGHT-04, FIGHT-05, FIGHTBOUT-01, FIGHTBOUT-02, RANK-01, RANK-02, CHAMP-01, STAT-01, ORG-04, ORG-05, EVT-05, SRCH-02, DISC-01, DISC-02, CAL-02, SET-03, NOTIF-UI-01, NOTIF-UI-02.

## Phase 4 — Historical Platform
**Goal: the app becomes a reference, not just a live-event companion — and organization coverage expands.**

Features: HIST-01, and the re-evaluation/unblocking of every feature currently marked Blocked pending multi-organization verification.

## Phase 5 — AI Features
**Goal: intentionally underspecified.**

Features: AI-01 (placeholder only).
