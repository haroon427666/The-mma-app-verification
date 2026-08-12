# POST-AUDIT — PRODUCTION WINDOW 016 (Census Window 9)

**Run:** `398180f2-5e26-4822-ab72-c8a20964c5d9` · COMPLETED · 2026-08-11 15:58:35 → 16:20:55 UTC · 1,340,414 ms
**Executed:** 2026-08-11 20:58:35 → 21:20:55 local · exit code 0 · log 8,080 lines

---

## 1. Scope
Independent read-only verification of the window-9 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma` (PostgreSQL 18, service `postgresql-x64-18`). `backend/mma_stats.db` is a 0-byte forensic-probe placeholder — verified untouched (size 0, LastWriteTime unchanged).

## 2. Run record
| field | value |
|---|---|
| id | 398180f2-5e26-4822-ab72-c8a20964c5d9 |
| status | COMPLETED |
| total_inserted | 3,990 (2,000 fighters + 1,990 records) |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,006, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_016_CENSUS_SYNC_LOG.txt`, UTF-16 LE)
- **HTTP 200 OK lines: 4,000** — 2,000 athlete-profile GETs + 2,000 `/records` GETs
- **HTTP 503 lines: 6** — transient "Backend fetch failed" on TWO athletes only:
  - athlete **5100131** profile: 503 at 21:08:05, 21:08:06, 21:08:09 → **200 at 21:08:14**
  - athlete **5099363** /records: 503 at 21:19:05, 21:19:06, 21:19:09 → **200 at 21:19:14**
  - Retry backoff 1s → 2s → 4s (6 `Retrying` warnings = attempts 1–3 per athlete)
- **HTTP 404: 0 · HTTP 429: 0 · other 5xx: 0**
- **Retries exhausted: 0 · breaker/circuit lines: 0 · Traceback: 0 · [ERROR] lines: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3990 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1340414ms` / `Total: 3990 inserted, 0 updated, 0 errors`
- Total requests 4,006 = 4,000 nominal + 6 retries; rate = 4,006 / 1,340.4 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental` (recent-sync heuristic) — registry-window job ignores mode (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 30,988 / pending 7,023**.

| entity | rows |
|---|---|
| fighters | 30,988 |
| fighter_records | 30,301 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 31,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **30,988 / 30,988 = 100%** (consumed_no_fighter = 0; fighter_not_in_registry = 0)
- W9 cohort (created 16:20:52–16:20:55 UTC): **exactly 2,000 fighters; 1,990 (99.5%) have fighter_records** — top band (W014 99.55% · W015 99.75% · W016 99.5%); 10 missing are genuine empty-payload absences (Larry Folsom 5025548 · Eric Curcio 5058264 · Joel Ojeda 5077133 · Jason Stafin 5077173 · Seth Fuller 5085178 · Aaron Menard 5085202 · Eliot Kelly 5088615 · Tyler Tomlinson 5092412 · Steve Faragher 5092485 · Loic Pora 5098329)
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 28 COMPLETED + 2 stale RUNNING (pre-existing, cosmetic)
- created_at bulk-stamp pattern matches W014/W015 (all cohort rows stamped 16:20:52–16:20:55) — normal flush behavior, not an anomaly

## 5. Spot checks
- **Recovered athletes verified in DB:** 5100131 (Marcio Candido da Silva) fighter + records both persisted (records created 16:20:55Z); 5099363 (Adel Atama) record 0-1-0/1 persisted (created 16:20:54Z). **No data lost to the 503s.**
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 5110480 Terra Nova 0-1-0/1 · 5110486 Silva 0-1-0/1 · 5110488 da Silva Caldas 0-1-0/1 · 5110472 Gonzalez 3-3-0/6 · 5110487 Martins 0-1-0/1.
- Next-window IDs verified ascending beyond this window (5110554…); window band consumed = exactly 5007665 → 5110553 (2,000 IDs).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push. `backend/mma_stats.db` untouched (0 bytes).

## 7. Verdict: **PASS** — window 9 fully consistent with W008–W015 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 lost payloads (both transient 503 episodes recovered by the built-in retry logic); record yield 99.5% (top band); no side effects.
