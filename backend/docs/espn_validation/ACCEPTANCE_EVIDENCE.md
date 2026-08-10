# ESPN MMA Integration — Acceptance Evidence

> **Date of record:** 2026-08-10 · **Primary source:** `backend/ESPN_PRODUCTION_VALIDATION_REPORT.md` (2026-08-09, "READY_FOR_COMMIT")
> **Preserved commit:** `cda302cc6f986aeabfad8ce2f790f5a37667a670`
> **Current HEAD:** `b723c7109da95b678e2ab67bf6aa12af84e0b217` (merge; tree identical to `cda302c` — empty diff verified)
> Every claim below is marked with its evidence source and status. Nothing in this file is fabricated; where evidence is absent the status is **UNKNOWN**.

---

## A. Identity of the accepted commit

| Item | Value | Evidence | Status |
|---|---|---|---|
| Commit SHA | `cda302cc6f986aeabfad8ce2f790f5a37667a670` | `git show` | VERIFIED |
| Author | Haroon Afridi | `git show` | VERIFIED |
| Author date | Mon Aug 10 00:37:23 2026 +0500 | `git show` | VERIFIED |
| Subject | `feat(espn): complete validated ESPN MMA integration` | `git show` | VERIFIED |
| Parent | `d3ecc68f42edc755582b7266a760cecd12c432e2` | `git show` | VERIFIED |
| HEAD relationship | `b723c71` is a merge whose tree diff vs `cda302c` is empty (HEAD tree = accepted tree) | `git diff b723c71 cda302c` (empty) | VERIFIED |
| Files in commit | 69 changed (24 added, 45 modified) | `git show --name-status cda302c` | VERIFIED |

## B. Static verification (from the validation report §14, implementation report §15)

| Check | Result (reported) | Source | Status |
|---|---|---|---|
| Full test suite | **455 passed, 2 skipped** (env-gated live tests) | VALIDATION_REPORT §14 | REPORTED |
| Test-def count in current tree | 457 `test_` defs = 455 + 2 skips — internally consistent | source inspection (2026-08-10) | VERIFIED |
| Implementation-close test count | 451 passed, 1 skipped | INTEGRATION_REPORT §15 | REPORTED |
| ruff | `All checks passed` | VALIDATION_REPORT §14 | REPORTED |
| mypy | `Success: no issues found in 189 source files` | VALIDATION_REPORT §14 | REPORTED |
| alembic heads/current | `006` (head) — consistent | VALIDATION_REPORT §14 | REPORTED |
| Migration 006 applied to live DB | nullable + partial unique index verified | VALIDATION_REPORT §14; DB check (below) | VERIFIED |
| `alembic check` | unsupported by project env.py — **pre-existing**, not a regression | VALIDATION_REPORT §14, §18 | REPORTED |

## C. Live validation evidence (2026-08-09, from VALIDATION_REPORT §10–§13)

### C.1 Live sync — two full bounded runs, both COMPLETED

Env-gated (`MMA_LIVE_SYNC=1`) against real ESPN API + live PostgreSQL
(bounded windows: 100 fighters, 5 historical events, 25 stat fighters, 10 eventlog fighters, 25 max pages).

- **Run 1:** 10/10 jobs COMPLETED, 0 errors.
- **Run 2:** COMPLETED, **identical row counts everywhere**, 0 errors → idempotency proven.

Live DB counts after acceptance (row counts re-verified read-only on 2026-08-10):

| Table | Count | DB re-check |
|---|---|---|
| fighters | 100 | VERIFIED |
| fighter_records | 100 | VERIFIED |
| events | 6 (1 upcoming + 5 historical) | VERIFIED |
| competitions | 73 | VERIFIED |
| competitors | 4 | VERIFIED |
| rankings | 4 | VERIFIED |
| statistics | 48 (report range 48–88 across runs) | VERIFIED |
| promotions | 48 | VERIFIED |
| weight_classes | 13 | VERIFIED |
| broadcasts | 1 | VERIFIED |
| venues | 0 (pre-existing) | VERIFIED |
| sync_runs | 2 (both COMPLETED) | VERIFIED |
| sync_jobs | 20 (10 jobs × 2 runs) | VERIFIED |
| external_ids | 240 | VERIFIED |
| users / provider_payloads / provider_conflicts / dead_letters / sync_checkpoints | 0 | VERIFIED |

### C.2 Live sync runs (DB `sync_runs`, re-verified read-only 2026-08-10)

| Run | id | status | duration_ms | inserted | updated | skipped | errors |
|---|---|---|---|---|---|---|---|
| 1 | `accd73ad-4a32-413c-a2ca-68430d9b3054` | COMPLETED | 141,246.289 | 384 | 0 | 142 | 0 |
| 2 | `5e400b2a-cb2c-4986-ad24-c7712e58ed2f` | COMPLETED | 5,252.951 | 4 | 100 | 422 | 0 |

Run 2 (idempotency): fighters 0 inserted / 100 updated / 100 skipped; promotion 48 skipped; event 1 skipped;
competition 36 skipped; historical_event 188 skipped; statistic 48 skipped; ranking 4 inserted; broadcast 1 skipped.

### C.3 Representative surface probes (all PASSED, report §10)

| Probe | Result |
|---|---|
| profile:demetrious_johnson (hidden) | OK (Demetrious) |
| profile:royce_gracie (hidden) | OK (Royce) |
| profile:ken_shamrock (hidden) | OK (Ken) |
| profile:ronda_rousey (hidden) | OK (**Alexis** — live cross-ID collision, see §G) |
| profile:ufc_ranked#1 (active) | OK (active=True) |
| records:shamrock / gracie | OK (29-17-2 / 15-2-2) |
| stats:demetrious_johnson | OK (8 stats) |
| stats:ken_shamrock | EMPTY (0 stats — content-dependent, not failure) |
| eventlog:demetrious_johnson | OK (count=30, pages=2 — pagination proven) |
| eventlog:royce_gracie | OK (count=20, pages=1) |
| winningfight_refs:ufc | OK (19 refs) |
| historical:ufc/400818923 (UFC 200) | event=OK comps=OK (12 comps, 24 competitors) |
| historical:ufc/400943074 (Bellator 178) | event=OK comps=OK (12 comps, 24 competitors) |
| rankings:ufc | OK (133 ranks) |
| roster:ofc (ONE Championship) | OK (408 fighters — matches research exactly) |
| status:gracie / rousey | OK (is_active=False / False) |

### C.4 Database integrity (report §11)

- **Before:** alembic 005; promotions 48, fighters 1,831, records 0, statistics 0, rankings 110, events 1 (T05-era state). **After:** alembic 006 (upgrade + verify); full acceptance dataset above.
- No duplicates — `(provider, external_id)` group-by = 0 dupes (fighters/events/competitions).
- One `fighter_records` per fighter — duplicate-fighter_id check = 0.
- No orphans — competitions without event = 0; competitors without competition = 0; sync_jobs without run = 0.
- Content spot-checks — Horn 90-21-1, Overeem 47-19-0; all career stats (`competitor_id IS NULL`); is_active 93 False / 7 True (no NULLs, presence-guard correct); historical events 2016–2019 with FINAL status.
- Repeated sync does not multiply rows (run 2 equality).

### C.5 Performance benchmark (report §13; script `backend/scripts/espn_live_benchmark.py`)

100-ID pool, 20 fresh IDs per worker count, production config (3.0 rps, burst 6, cache on):

| Workers | Resolved | HTTP calls | Failures | Elapsed | Effective rps |
|---|---|---|---|---|---|
| 1 | 20/20 | 20 | 0 | 6.20s | **3.22** |
| 2 | 20/20 | 20 | 0 | 7.45s | **2.68** |
| 4 | 20/20 | 20 | 0 | 6.62s | **3.02** |
| 8 | 20/20 | 20 | 0 | 6.67s | **3.00** |

- **Pre-fix at 8 workers: 8.36 rps (envelope violated). Post-fix: all configs ≈ 3 rps** — within the researched 2–5 req/s envelope.
- In-flight dedup: 20 deduped / 20 actual HTTP calls for 40 concurrent requests (50% reduction).
- Cache reuse: re-fetch of 20 cached IDs = **0 new HTTP calls**.
- No retries, no failures, no 429s observed during the benchmark.
- Rate limiter (not ESPN) caps throughput; network ~1.9s first byte dominates per-request cost.

## D. Bugs found during validation — all 5 fixed and re-validated live (report §16–§17)

| # | Problem | Root cause | Fix | Evidence |
|---|---|---|---|---|
| 1 | Breaker poisoned runs | `on_failure()` on every 4xx | 4xx never trips breaker; only 429/5xx-exhausted + network | unit tests (404 CLOSED / 5xx OPEN); live sync PASSED |
| 2 | Envelope exceeded | release-during-wait token bucket leaked under concurrency | standard refill/sleep-outside/recheck loop | pacing unit test; benchmark 8.36→3.00 rps |
| 3 | Eventlog truncated | first page only | page loop + pageCount + cap 5 | unit test (pages [1,2] merged); live probe pages=2 |
| 4 | Historical dup fetches + attribution | hooks keyed league:event | dedupe by event_id, first-scope-wins | live sync PASSED (events 6, no dupes) |
| 5 | Live test gaps | missing job + unbounded windows | registered historical job, bounded env, dual-run + integrity assertions | live test PASSED (twice) |

## E. Research grounding (frozen research workspace — external, read-only, NOT modified)

- Frozen entry point: `START_HERE.md` (generated 2026-08-09T16:51:30+00:00), `FINAL_RESEARCH_STATUS.md`, `RESEARCH_MANIFEST.json` (2026-08-09T17:03:49+00:00).
- Key baselines relied upon: 38,014-athlete census; 38,006 verified; 8 hard-400; 0 unresolved; 49 leagues;
  96 families (75 confirmed / 15 failed / 4 content-dependent / 1 current-only / 1 observed); 19/32 live-probed;
  10 P0 blockers; rate envelope **2–5 req/s at 4–8 workers**; original resolver 10.6h; 47 winningFight hooks;
  hidden profiles (DJ `2512089`, Rousey `2563796`, Gracie `2335697`, Shamrock `2335653`, Ngannou `3933168`);
  `ofc` roster = 408.
- Research→production mapping: 100% IMPLEMENTED per report §2 (one item PARTIALLY_IMPLEMENTED: resumable discovery
  uses in-process store; DB-backed store = documented future work).

## F. Audit coverage (report §21 A–B)

- **Audited:** all production ESPN provider/client/jobs/parsers/upserts, sync engine/plan/dependency/state,
  migration 006, tests, CLI, plus frozen research baselines.
- **Verified:** every research→implementation mapping (code + tests + live), rate envelope (benchmark),
  cache/dedup (benchmark), idempotency (dual run), DB integrity (queries), migration state (006 applied + verified).

## G. Remaining limitations (report §18) — documented, none blocking

1. **Ronda Rousey ID `2563797` resolves to "Alexis"** — live cross-ID collision; same class as research-documented Fedor (`2335301` → Frank Mir). Integration faithfully resolves what ESPN serves.
2. **Cross-promotion historical event attribution = first ref scope** (e.g., Bellator 214 attributed to ufc) — deterministic; no authoritative promotion marker in payload.
3. **Full-census runs ≈ 3.5h at 3 rps** — use `ESPN_FIGHTER_SYNC_LIMIT` windows.
4. **Discovery checkpoint is in-process** (MemorySyncStateStore) — DB-backed store is future work.
5. **Statistics count varies between runs** (48 vs 88) — listing churn shifts sorted window; content-dependent.
6. **Eventlog capped at 5 pages/fighter** (125 fights).
7. **`other` league (~27,286 IDs) excluded** from active discovery (composition unresolved per research).
8. **`alembic check` unsupported** (pre-existing env.py).
9. **venues = 0** — pre-existing.

## H. Readiness conclusion

**READY_FOR_COMMIT** (report §19): all five genuine problems fixed and re-validated live
(sync PASSED twice, probes PASSED, benchmark gates PASSED after each fix); full gates green
(455 passed + 2 env-gated skips, ruff/mypy clean, alembic 006 consistent); live DB real data,
zero duplicates, zero orphans, idempotency proven. The commit itself was the user's decision —
`cda302c` is that commit. **This evidence package accepts `cda302c` as the validated integration.**
