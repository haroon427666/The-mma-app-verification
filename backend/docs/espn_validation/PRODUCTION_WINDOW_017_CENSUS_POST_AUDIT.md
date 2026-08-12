# POST-AUDIT — PRODUCTION WINDOW 017 (Census Window 10)

**Run:** `e408afbb-b902-4809-bf9e-f443fb77f629` · COMPLETED · 2026-08-11 16:49:23 → 17:11:50 UTC · 1,346,405 ms
**Executed:** 2026-08-11 22:49:23 → 23:11:50 local · exit code 0 · log 4,100 lines

---

## 1. Scope
Independent read-only verification of the window-10 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma` (PostgreSQL 18, service running). `backend/mma_stats.db` is a 0-byte forensic-probe placeholder — verified untouched (size 0, unmodified).

## 2. Run record
| field | value |
|---|---|
| id | e408afbb-b902-4809-bf9e-f443fb77f629 |
| status | COMPLETED |
| total_inserted | 3,985 (2,000 fighters + 1,985 records) |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,027, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_017_CENSUS_SYNC_LOG.txt`, UTF-8)
- **HTTP 200 OK lines: 4,000** — 2,000 athlete-profile GETs + 2,000 `/records` GETs
- **HTTP 503 lines: 27** — transient "Backend fetch failed" on **FIVE athletes' /records** during one burst (22:01:52–22:01:59 local / 17:01 UTC): 5122171, 5121866, 5122172, 5122173, 5122174
  - 27 `Retrying` warnings = retry attempts (1s → 2s → 4s backoff); every athlete recovered on a final attempt (all 2,000 records ultimately HTTP 200)
- **HTTP 404: 0 · HTTP 429: 0 · other 5xx: 0**
- **Retries exhausted: 0 · breaker/circuit lines: 0 · Traceback: 0 · [ERROR] lines: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3985 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1346405ms` / `Total: 3985 inserted, 0 updated, 0 errors` / `Sync engine shutdown complete`
- Total requests 4,027 = 4,000 nominal + 27 retries; rate = 4,027 / 1,346.4 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental` (recent-sync heuristic) — registry-window job ignores mode (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 32,988 / pending 5,023**.

| entity | rows |
|---|---|
| fighters | 32,988 |
| fighter_records | 32,286 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 33,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **32,988 / 32,988 = 100%** (consumed_no_fighter = 0; fighter_not_in_registry = 0)
- W10 cohort (created 17:11:48–17:11:50 UTC): **exactly 2,000 fighters; 1,985 (99.25%) have fighter_records** — top band (W016 99.5% · W017 99.25%); 15 missing are genuine empty-payload absences (Michael Tate 5120132 · David Tirelli 5120133 · Rafael Ferreira 5124795 · Matt Wynne 5127381 · Mick Maney 5127420 · Dwayne Bess 5141978 · Ross Swanberg 5142168 · David Huyette 5142169 · Larry Carter 5144958 · Bobby Harris 5144969 · Mitch Cadlick 5146910 · Sal Ram 5146911 · Phil Koldyk 5146912 · Jake Maxim 5146925 · Sal Ram 5146929)
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 29 COMPLETED + 2 stale RUNNING (pre-existing, cosmetic)
- created_at bulk-stamp pattern matches W014–W016 (all cohort rows stamped 17:11:48–17:11:50) — normal flush behavior, not an anomaly

## 5. Spot checks
- **Recovered athletes verified in DB (all 5):** 5121866 Greg Velasco 6-2-0 · 5122171 Mona Ftouhi 0-1-0 · 5122172 Martina Gemrani 0-1-0 · 5122173 Antonia Prifti 1-0-0 · 5122174 Oliwia Zaluska 0-1-0 — **no data lost to the transient 503s.**
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 5110554 Jairo Pacheco 7-2-0/9 · 5110557 Maria Laura Alves Fontoura 0-1-0/1 · 5110558 Anastasiya Svetkivska 1-2-0/3 · 5110828 A.J. Weber 0-1-0/1 · 5110829 Zachary Vaci 1-0-0/1.
- Next-window IDs verified ascending beyond this window (5153044…); window band consumed = exactly 5110554 → 5153043 (2,000 IDs).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push. `backend/mma_stats.db` untouched (0 bytes).

## 7. Verdict: **PASS** — window 10 fully consistent with W008–W016 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 lost payloads (the 27 transient 503s on five athletes' /records recovered by the built-in retry logic — all five records verified persisted); record yield 99.25% (top band); no side effects.
