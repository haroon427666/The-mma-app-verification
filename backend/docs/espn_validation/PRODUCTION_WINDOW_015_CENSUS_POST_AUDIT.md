# POST-AUDIT — PRODUCTION WINDOW 015 (Census Window 8)

**Run:** `24f66550-18ff-4b18-b990-7c55b60ac3e0` · COMPLETED · 2026-08-11 15:17:48 → 15:40:03 UTC · 1,334,775 ms
**Executed:** 2026-08-11 20:17:47 → 20:40:05 local · exit code 0 · log 8,066 lines

---

## 1. Scope
Independent read-only verification of the window-8 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma` (PostgreSQL 18, service `postgresql-x64-18`). `backend/mma_stats.db` is a 0-byte forensic-probe placeholder — verified untouched (size 0, LastWriteTime unchanged).

## 2. Run record
| field | value |
|---|---|
| id | 24f66550-18ff-4b18-b990-7c55b60ac3e0 |
| status | COMPLETED |
| total_inserted | 3,995 (2,000 fighters + 1,995 records) |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_015_CENSUS_SYNC_LOG.txt`, UTF-16 LE)
- **HTTP 200 OK lines: 4,000** — of which 2,000 athlete-profile GETs and 2,000 `/records` GETs
- **Non-200 HTTP lines: 0** — zero matches for any status other than 200
- **Retries: 0 · breaker/circuit lines: 0 · Traceback: 0 · [ERROR] lines: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3995 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1334775ms`
- Rate: 4,000 requests / 1,334.8 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental reason=Recent sync (0h ago)` — heuristic only; fighter job is registry-window-based, mode has no behavioral impact (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 28,988 / pending 9,023**.

| entity | rows |
|---|---|
| fighters | 28,988 |
| fighter_records | 28,311 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 29,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **28,988 / 28,988 = 100%** (consumed_no_fighter = 0; fighter_not_in_registry = 0)
- W8 cohort (created 15:40:00–15:40:03 UTC): **exactly 2,000 fighters; 1,995 (99.75%) have fighter_records** — top band; 5 missing are genuine absences (Chris Crail 4915531 · Marcel Valera 4915532 · Ivan Guzman 4920440 · Chad Trukovich 5002957 · Todd Schwarz 5003753)
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 27 COMPLETED + 2 stale RUNNING (pre-existing)
- created_at bulk-stamp pattern (all rows stamped 15:40:00–15:40:03) matches W014's identical pattern (14:50:46–14:50:48) — normal flush behavior, not an anomaly

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 5007659 Varadi Akos 0-1-0/1 · 5007657 Marjanski 0-1-0/1 · 5007658 Mokry 0-1-0/1 · 5007664 Koziorzebski 0-3-0/3 · 5007654 Zukowski 0-1-0/1.
- Next-window IDs verified ascending beyond this window (5007665…).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push. `backend/mma_stats.db` untouched (0 bytes).

## 7. Verdict: **PASS** — window 8 fully consistent with W008–W014 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests; record yield 99.75% (top band; W013 dip remains a confirmed one-off artifact).
