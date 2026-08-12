# PRODUCTION_NEXT_WINDOW_AUDIT.md

> **Date:** 2026-08-10
> **Type:** Decision + data-quality audit (observation-only; **no production sync was executed**)
> **Author:** continuation session per the "next-window decision and data-quality audit" brief
> **Frozen research used (read-only):** `ATHLETE_CENSUS_FINAL.csv` (classification cross-check), `DISCOVERY_SOURCES_FINAL.json` (search endpoint), `ESPN_ENDPOINT_CATALOG.md` context

---

## 1. Current state

| Item | Value |
|---|---|
| Pushed HEAD | `19a87c7` `docs(espn): add production window 001/002 evidence` (origin/main, 0 ahead/behind) |
| History | `cda302c` (integration) → `56221cc` (acceptance docs) → `799c87f` (durable discovery) → `19a87c7` (window evidence) |
| Alembic | `008` (head == current, single head) |
| Discovery sources | 7/7 COMPLETED (global_listing 38,011; rosters ufc 1,840 / bellator 986 / pfl 587 / ofc 408 / ksw 208 / ifc 172) |
| Sync checkpoints | fighter COMPLETED, ranking COMPLETED |
| Production windows | baseline acceptance → W001 (1000) → W002 (1000 + rankings 110) → W003 (2000) |
| Zero-error/zero-429 history | 0 errors, 0 HTTP 429, 0 breaker opens across ALL production windows |

## 2. DB state + integrity (read-only capture, `localhost:5432/mma`, alembic 008)

| Table | Count | Table | Count |
|---|---|---|---|
| fighters | **5,355** | events | 24 |
| fighter_records | 5,062 | competitions | 260 |
| statistics | 399 | competitors | 47 |
| rankings | **142** (142/142 resolve) | promotions | 48 |
| external_ids | 5,706 | sync_runs | 12 COMPLETED + 2 stale RUNNING (killed-process artifacts, cosmetic) |

| Integrity check | Result |
|---|---|
| Duplicate (provider, external_id) — fighters | 0 |
| Duplicate external_ids | 0 |
| Duplicate discovery-registry rows | 0 |
| Orphan fighter_records / rankings / statistics / competitors | 0 / 0 / 0 / 0 |
| Orphan external_ids (fighter type) | 0 |
| NULL provider/external_id in fighters | 0 |

**Discovery registry:** total **38,011** (global_listing 36,011 + backfill 2,000) · consumed **5,355** · pending **32,656**
Consumed ID range: **2,085,811 → 4,426,000** (includes deep-ID ranking-injection athletes) · pending range: **2,609,393 → 5,395,233**
Roster/ranking/eventlog registrations converged into existing global rows (cross-source dedup proven; 0 new rows).

## 3. Coverage / ordering analysis (frozen census cross-check, read-only)

| Classification | Census total | Synced | Missing | Missing in pending registry? |
|---|---|---|---|---|
| confirmed_mma | 2,763 | 661 (24%) | 2,102 | **YES — all 2,102** (pending ∩ confirmed = 2,102) |
| mma_likely | 33,352 | 4,271 | 29,081 | pending (29,081) |

- **Every confirmed-MMA athlete that is not yet synced is already queued in the pending registry** — the deterministic ID-ordered walk will reach them; none is undiscoverable.
- Missing confirmed-MMA by ID band: 2.6–3.1M: 327 · 3.1–4M: 257 · 4–5M: 795 · >5M: 723.
- **Yield of the remaining census ≈ 6.4% confirmed MMA** (2,102 of 32,656 pending). The next 5,000 consecutive IDs contain roughly 300–350 confirmed-MMA athletes, sparsely distributed among mostly obscure/inactive `mma_likely` entries — confirming the Window-002 finding that consecutive-ID bands are low-yield for high-value coverage.
- **Ranking injection already covers the current ranked universe** (142/142 resolved; `ESPN_RANKING_INJECTION_LIMIT=110` injected 70 previously-unsynced ranked fighters at deep IDs).
- Ordering verdict: current ordering is **not** producing mostly confirmed MMA anymore (24% coverage, ~6% marginal yield); it is deterministic, crash-safe, and complete-but-slow.

## 4. Representative live probes (small, controlled — 15 requests, ~0.7 s spacing, inside the validated 2–5 rps envelope)

| Athlete | ESPN ID | Live profile | In DB | Notes |
|---|---|---|---|---|
| Ronda Rousey | **2563796** | resolves (active) | ✅ synced, 13-2-0 | Research ID 245 was stale; real ID synced via band walk |
| Islam Makhachev | 3332412 | resolves (active) | ✅ synced | Research ID 2579938 stale |
| Francis Ngannou | 3933168 | resolves (active) | ✅ synced | Research ID 2579646 stale |
| Demetrious Johnson | 2512089 | resolves (active) | ✅ synced | — |
| Royce Gracie | 2335697 | resolves (inactive) | ✅ synced | — |
| Ken Shamrock | 2335653 | resolves (inactive) | ✅ synced | — |
| pending 2609393–2609397 | — | resolve | ❌ pending | Jay Isip, Rick Desper, Reynaldo Duarte, Gerald Lovato (all inactive) + John Dodson (active) — obscure band |

- Search API v2 (`/apis/search/v2?query=Rousey`) returned 404 with `query=` — endpoint nuance only; profile endpoint is authoritative and resolves. Not required for production.
- All 6 representative fighters live-verified with correct names. No name/identity mismatches found in the DB for any representative.

## 5. Known risks (unchanged, still open)

1. 38,014 census ≠ 38,014 MMA fighters — only 2,763 confirmed; remaining census is low-yield.
2. Rousey/Makhachev/Ngannou **research IDs are stale** — real IDs are 2563796 / 3332412 / 3933168 (this audit corrects them; `ESPN_HANDOFF_STATE.md` should be updated).
3. `ESPN_FIGHTER_SYNC_LIMIT` default 0 = unbounded — always set explicitly.
4. 2 stale `RUNNING` sync_runs rows (killed-process artifacts; cosmetic, no data impact).
5. Consecutive-ID windows: ~6.4% confirmed-MMA yield for the remaining 32,656.
6. Rankings are current-era only; historical ranked athletes rely on the census walk.
7. Census listing drifts between runs (38,014 → 38,011 observed; walk already COMPLETED so no re-walk occurs).

## 6. Decision gate

**A — Run another bounded fighter window.**

Rationale: no data-quality blocker exists (integrity perfect, representatives healthy, rankings complete, Rousey resolved). The pipeline is deterministic and will eventually reach all 2,102 missing confirmed-MMA athletes; the only question is pacing. Neither C (fix DQ first), D (code change), nor E (full census now) is justified by the evidence.

## 7. Recommended next operation

**`ESPN_FIGHTER_SYNC_LIMIT=2000` fighter window** (consistent with the established cadence):

- Expected: **+2,000 fighters** (~130 confirmed MMA + ~1,870 mma_likely), fighter_records +~1,700 (content-dependent 404s for the rest).
- API cost: **~4,000 requests** (2,000 profiles + 2,000 records) + **0 discovery requests** (all sources COMPLETED).
- Runtime: **~25–35 min** (previous 4,000-request window: 22.3 min).
- Pending after: **32,656 → 30,656**.
- Risk: **low** (5 consecutive windows at 0 errors / 0 429s / 0 integrity violations).
- Optional faster track: `LIMIT=5000` (~83 min, ~10,000 requests, ~325 confirmed MMA) if census pace is preferred over cadence.

## 8. Audit statement

**No production window was executed during this audit.** All operations were read-only: `SELECT` queries against the local acceptance DB, `git` inspection, and 15 controlled live HTTP probes. No code, no migrations, no mobile files, no planning/session files, and no frozen research were modified.
