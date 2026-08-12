# PRODUCTION_WINDOW_005_POST_AUDIT.md

> **Date:** 2026-08-10
> **Type:** Post-window audit + W006 decision gate (observation-only; **W006 NOT executed**)
> **Scope:** W005 (LIMIT=2000), first-run 503/breaker incident + resumable retry, environment/toolchain repair, scaling + coverage analysis

---

## 1. W005 baseline (pre-run capture)

| Metric | Before |
|---|---|
| fighters | 5,355 |
| fighter_records | 5,062 |
| external_ids | 5,706 |
| rankings / statistics | 142 / 399 |
| registry consumed / pending | 5,355 / 32,656 |
| sync_runs | 14 |
| alembic | 008 |

## 2. First-run 503 incident

- Launch: `ESPN_FIGHTER_SYNC_LIMIT=2000 sync.py --full --entity fighter` (run `1ed8e522`, 17:17:08 → 17:20:55 UTC).
- ESPN returned **40 × HTTP 503** (transient server-side; **0 × 429** — no rate-envelope breach).
- After 5 consecutive failures the **circuit breaker tripped: CLOSED → OPEN** (log-verified `22:20:47`).
- Window stopped with **633 resolved of 2000**; process ended `COMPLETED` with `inserted=633 errors=0`.

## 3. Circuit breaker / consumption behavior (the critical part)

Log-verified explicit line from the fighter job:

```
Fighter window: 1367 ids unresolved during an unhealthy fetch (system signals
detected) — left queued for retry, NOT consumed
```

- **Only successfully-upserted IDs were consumed** (633) — `consumed` markers are set only after `FighterUpsert` persistence.
- **1,367 unresolved IDs remained pending** — no dead-end consumption occurred under an open breaker.
- DB verification: after run 1, consumed = 5,988 == fighters = 5,988 (consumption ⇔ persistence, exact).

## 4. Resume / retry

- Retry (`7eec7396`, 17:28:10 → 17:50:27 UTC, 1,337 s): picked up the next 2,000 unconsumed IDs = **1,367 leftovers + 633 next-in-line**.
- Result: **2000/2000 resolved**, `inserted=3933` (= 2,000 fighters + 1,933 records), **0 errors, 0×429, 0×5xx**.
- No duplicates; the 633 from run 1 were naturally skipped via the consumed filter (idempotency).

## 5. Retry results / combined W005 effect

| Metric | After | Δ |
|---|---|---|
| fighters | **7,988** | +2,633 |
| fighter_records | 6,995 | +1,933 |
| external_ids | 8,341 | +2,635 |
| registry consumed | **7,988** | +2,633 |
| registry pending | **30,023** | −2,633 |
| sync_runs | 16 | +2 (both COMPLETED) |
| rankings / statistics | 142 / 399 | unchanged |

## 6. Final DB state + integrity (post-audit re-verification, read-only)

Counts match the W005 after-capture exactly (fighters 7,988 · records 6,995 · ext_ids 8,341 · registry 38,011 total / 7,988 consumed / 30,023 pending · sync_runs 16 · alembic 008).

| Check | Result |
|---|---|
| Duplicate fighters / registry / external_ids | 0 / 0 / 0 |
| Orphan fighter_records / rankings / statistics / competitors / external_ids | 0 / 0 / 0 / 0 / 0 |
| NULL provider/external_id | 0 |
| Unresolved ranking references | 0 |
| Checkpoints | fighter COMPLETED, ranking COMPLETED, 7/7 discovery COMPLETED |
| Stale RUNNING sync_runs | 2 (pre-existing killed-process artifacts — NOT from W005) |

## 7. W005 classification

| Mechanism | Verdict | Evidence |
|---|---|---|
| Circuit breaker | **PASS** | tripped on 5 consecutive 503s; blocked further hammering |
| Registry consumption | **PASS** | only persisted IDs consumed; consumed == fighters exactly |
| Checkpoint/resume | **PASS** | run 2 resumed from the unconsumed queue, no rework |
| Retry behavior | **PASS** | 1,367 leftovers + 633 next, 2000/2000, 0 errors |
| Idempotency | **PASS** | zero duplicate fighter/registry rows across both runs |
| Data integrity | **PASS** | 0 dupes, 0 orphans, 0 NULLs, 0 unresolved rankings |

## 8. Performance (W001–W005)

| Window | LIMIT | Requests | Duration | req/fighter | rps |
|---|---|---|---|---|---|
| W001 | 1000 | ~2,000 | ~11.2 min | 2.0 | ~3.0 |
| W002 | 2000 | ~4,000 | ~22 min | 2.0 | ~3.0 |
| W003 | 1000 (+rankings 110) | ~2,200 | ~11 min | 2.0 | ~3.0 |
| W004 | 2000 | 4,000 | 22.3 min | 2.0 | ~3.0 |
| W005 run 2 | 2000 | 4,000 | 22.3 min | 2.0 | ~3.0 |

Constants: **~2.0 API requests per fighter** (profile + records; 0 discovery — census sources completed), **~11.1 min per 1,000 consumed IDs** at ~3.0 rps, **0 discovery requests** on every window since the census walk completed. All runs inside the validated 2–5 rps envelope.

## 9. Environment / toolchain incident (operational, not ESPN code)

- The venv's site-packages had lost a broad set of `.py` files (asyncpg, SQLAlchemy, pydantic, greenlet, numpy, scipy, pip, …).
- **7,118 missing files across 70 packages** restored from exact-version PyPI wheels — **add-missing-only, compiled binaries preserved, versions unchanged**.
- Import chain + DB roundtrip verified before launch; sync then ran identically to prior windows.
- **No project source code was intentionally modified.** Treated as an operational incident, not an ESPN change.

## 10. Coverage / data quality (frozen census cross-check, read-only)

| Classification | Total | Synced | Missing | Missing pending in registry? |
|---|---|---|---|---|
| confirmed_mma | 2,763 | **846 (30.6%)** | 1,917 | **YES — all 1,917** |
| mma_likely | 33,352 | 6,547 | — | — |

- Missing confirmed-MMA by ID band: 2.6–3.1M: 142 · 3.1–4M: 257 · 4–5M: 795 · >5M: 723.
- Remaining-census yield: **1,917 / 30,023 = 6.4%** confirmed MMA (unchanged rate — consecutive-ID bands remain mostly inactive/likely).
- Ranking injection: 142/142 rankings resolve; current ranked universe fully covered.
- Representatives re-verified: Makhachev, Ngannou, Rousey, Gracie, Shamrock, DJ all synced. No identity-collision or representative regression reappeared.

## 11. Risks (still open)

1. Remaining census is low-yield (6.4% confirmed); ordering deterministic but slow to reach the 1,917 confirmed.
2. Transient ESPN 503s recurred once (handled cleanly) — larger windows enlarge the blast radius if they recur, but the breaker/resume mechanism is now production-proven.
3. `ESPN_FIGHTER_SYNC_LIMIT` default 0 = unbounded — always explicit.
4. 2 stale RUNNING sync_runs rows (cosmetic).
5. Statistics and historical-event coverage remain sparse for individual athletes (out of scope for fighter windows).

## 12. Decision gate

**B — W006 LIMIT=5000 is justified.**

Evidence: (1) ~3.0 rps observed across all windows, comfortably inside the validated 2–5 rps envelope; (2) 6 consecutive production windows with 0 errors/0 429s and the only incident (503s) fully contained by the breaker + resume path; (3) crash-safe resume is now proven at scale in production (W005), de-risking longer single runs; (4) 10,000 requests ≈ 55 min is a reasonable operational duration; (5) same 6.4% yield per ID, so a larger window adds no quality risk — only fewer launches.

## 13. Recommended W006 configuration

```
PYTHONIOENCODING=utf-8 ESPN_FIGHTER_SYNC_LIMIT=5000 python sync.py --full --entity fighter
```

- Expected: **+~5,000 fighters** (~320 confirmed MMA), ~10,000 API requests, **~55 min** at 3 rps, 0 discovery requests.
- Expected end state: fighters 7,988 → ~12,988; pending 30,023 → ~25,023; consumed 7,988 → ~12,988.
- Pre/post DB captures + integrity sweep per standing practice; rankings refresh not required (142/142 already).
- Mitigation if 503s recur mid-run: rerun the same command — the unconsumed queue resumes exactly (W005-proven).

---

**Audit statement:** observation-only. No W006 executed; no code/migration/test/mobile/research/planning changes; no commits/pushes; no DB writes beyond the audited W005 sync itself.
