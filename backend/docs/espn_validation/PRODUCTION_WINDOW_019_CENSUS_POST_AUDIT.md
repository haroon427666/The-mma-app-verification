# POST-AUDIT — PRODUCTION WINDOW 019 (Census Window 12) — PARTIAL (breaker trip)

**Run:** `09d84b8d-a75b-4a8c-a8ee-8cbcb1ff0dee` · COMPLETED · 2026-08-11 17:58:10 → 18:07:50 UTC · 580,809 ms
**Executed:** 2026-08-11 23:58:10 → 00:07:50 local (next day) · exit code 0 · log 3,823 lines
**Outcome:** **PARTIAL — 1,676 of 2,000 IDs consumed; breaker trip; records phase NOT executed.**

---

## 1. Scope
Independent read-only verification of the window-12 census run (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma` (PostgreSQL 18, service running). `backend/mma_stats.db` is a 0-byte forensic-probe placeholder — verified untouched (size 0, unmodified).

## 2. Run record
| field | value |
|---|---|
| id | 09d84b8d-a75b-4a8c-a8ee-8cbcb1ff0dee |
| status | COMPLETED |
| total_inserted | **1,676 (fighters only — records phase never ran)** |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 1,720, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_019_CENSUS_SYNC_LOG.txt`, UTF-8)
- **HTTP 200 OK lines: 1,676** — all athlete-profile GETs
- **HTTP 503 lines: 44** — persistent "Backend fetch failed" on **profile** GETs in the window tail (IDs 5310951+), 23:07:25–23:07:50 local (18:07 UTC). 44 `Retrying` warnings; **0 recoveries** (unlike W016–W018).
- **Breaker: 1 trip — `CLOSED → OPEN (5 consecutive failures)` at 23:07:42**; subsequent attempts logged `Circuit breaker is OPEN. Retry in 60s`
- **Job healthy-gate warning:** `Fighter window: 324 ids unresolved during an unhealthy fetch (system signals detected) — left queued for retry, NOT consumed` and `Fighter window: 1676 resolved of 2000 ids`
- **Records requests: 0** (the records phase never executed)
- **HTTP 404: 0 · HTTP 429: 0 · other 5xx: 0 · Traceback: 0 · [ERROR] lines: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines) — 0 discovery requests
- **End banner:** `✓ fighter inserted=1676 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 580809ms` / `Total: 1676 inserted, 0 updated, 0 errors` / `Sync engine shutdown complete`
- Total requests 1,720; rate = 1,720 / 580.8 s ≈ **2.96 req/s**

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 36,664 / pending 1,347**.

| entity | rows | Δ vs W018 |
|---|---|---|
| fighters | 36,664 | +1,676 |
| fighter_records | 34,183 | 0 |
| statistics | 399 | 0 |
| rankings | 142 | 0 |
| competitors | 47 | 0 |
| external_ids | 37,021 | +1,676 |
| events / competitions / promotions | 24 / 260 / 48 | 0 |
| weight_classes | 25 | 0 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **36,664 / 36,664 = 100%** (consumed_no_fighter = 0)
- **Partial-window cohort:** exactly 1,676 fighters (created 18:07:50 UTC); **all 1,676 lack fighter_records** (records phase not executed — NOT genuine absences). Window band consumed = 5238639 → 5311038; first IDs continue the W018 placeholder cluster ("Mongi Zitouni"/"Ludovic Dandine" roster entries) — content consistent.
- **Queued/unconsumed verified:** 324 IDs from the window band left unconsumed (44 persistent-503 failures + ~280 never attempted after breaker OPEN). Spot-checked sub-band 5310951–5311500: 56 IDs confirmed still `consumed=false`; next pending = **5310951**; pending total = **1,347**.
- external_ids Δ+1,676 = 1,676 fighters, 0 weight classes (unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 31 COMPLETED + 2 stale RUNNING (pre-existing, cosmetic)

## 5. Spot checks
- **Representatives (6/6):** Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged.
- **Resolved cohort profiles consistent** (Mongi Zitouni 5238639 · Ludovic Dandine 5238640 · …). No fabricated rows; 1,676/1,676 resolved profiles → persisted rows.
- **No dead-ends, no lost payloads** in the resolved set; the 324 unresolved IDs were preserved in the registry (unconsumed) for a future run.

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run (partial) plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push. `backend/mma_stats.db` untouched (0 bytes).

## 7. Verdict: **PASS-WITH-DEVIATION (PARTIAL)** — the healthy-gate/circuit-breaker behaved exactly as designed (W005-run-1 precedent): only resolved IDs consumed, 0 integrity violations, queued IDs preserved. **However the window did NOT meet its 2,000-ID target (1,676 consumed) and the records phase did not execute** (all 1,676 new fighters lack records). **Per protocol: STOP — no automatic re-run; completing the remaining 1,347 pending IDs requires a new explicit decision gate.**
