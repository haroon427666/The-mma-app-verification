# POST-AUDIT — PRODUCTION WINDOW 014 (Census Window 7)

**Run:** `200a3500-21ba-4a46-bcba-49994d471122` · COMPLETED · 2026-08-11 14:28:33 → 14:50:48 UTC · 1,334,418 ms
**Executed:** 2026-08-11 19:28:32 → 19:50:50 local · exit code 0 · log 8,062 lines

---

## 1. Scope
Independent read-only verification of the window-7 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma`.

## 2. Run record
| field | value |
|---|---|
| id | 200a3500-21ba-4a46-bcba-49994d471122 |
| status | COMPLETED |
| total_inserted | 3,991 |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_014_CENSUS_SYNC_LOG.txt`)
- **Profiles fetched: 2,000** — `GET .../v2/sports/mma/athletes/<digits>` lines excluding `/records`
- **Records fetched: 2,000** — all `"/records \"HTTP/1.1 200 OK\""`
- **Non-200 HTTP lines: 0** — zero `HTTP/1.1 (?!200)` matches
- **Error lines / Traceback / breaker: 0**
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3991 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1334418ms`
- Rate: 4,000 requests / 1,334.4 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental reason=Recent sync (0h ago)` — heuristic only; fighter job is registry-window-based, mode has no behavioral impact (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 26,988 / pending 11,023**.

| entity | rows |
|---|---|
| fighters | 26,988 |
| fighter_records | 26,316 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 27,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0** (142/142 resolve)
- consumed↔fighter: **26,988 / 26,988 = 100%**
- W7 cohort (created ≥ 14:28:33 UTC): **exactly 2,000 fighters; 1,991 (99.55%) have fighter_records** — yield recovered from W013's 96.05% placeholder-band dip
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**; sync_runs 26 COMPLETED + 2 stale RUNNING

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 4683575 Zea 0-2-0/2 · 4683580 Fischer 10-4-0/14 · 4868779 Prado 12-4-0/16 · 4868785 de Oliveira 0-1-0/1. Notable real fighter in cohort: Darnell Pettis (4683576).
- Next-window IDs verified ascending beyond this window (4869216…).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push.

## 7. Verdict: **PASS** — window 7 fully consistent with W008–W013 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests; record yield fully recovered to the normal band.
