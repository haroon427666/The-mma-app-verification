# POST-AUDIT — PRODUCTION WINDOW 012 (Census Window 5)

**Run:** `6c2ba67f-2fb9-466f-8a37-0f76a2d76065` · COMPLETED · 2026-08-11 13:18:40 → 13:40:56 UTC · 1,336,349 ms
**Executed:** 2026-08-11 18:18:38 → 18:40:58 local · exit code 0 · log 8,068 lines

---

## 1. Scope
Independent read-only verification of the window-5 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma`.

## 2. Run record
| field | value |
|---|---|
| id | 6c2ba67f-2fb9-466f-8a37-0f76a2d76065 |
| status | COMPLETED |
| total_inserted | 3,964 |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_012_CENSUS_SYNC_LOG.txt`)
- **Profiles fetched: 2,000** — `GET .../v2/sports/mma/athletes/<digits>` lines excluding `/records`
- **Records fetched: 2,000** — all `"/records \"HTTP/1.1 200 OK\""`
- **Non-200 HTTP lines: 0** — zero `HTTP/1.1 (?!200)` matches
- **Errors/retries/breaker: 0** (no error lines beyond the PowerShell stderr-capture wrapper artifact)
- **Discovery: 7/7 "already completed — skipping"** (14 skip lines incl. the fighter-job repeats) — no discovery requests made
- **End banner:** `✓ fighter inserted=3964 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1336349ms`
- Rate: 4,000 requests / 1,336.3 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: strategy logged `mode=incremental` (heuristic only; fighter job is registry-window-based — no behavioral impact, confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 22,988 / pending 15,023**.

| entity | rows |
|---|---|
| fighters | 22,988 |
| fighter_records | 22,404 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 23,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0**
- consumed↔fighter: **22,988 / 22,988 = 100%**
- W5 cohort (created ≥ 13:18:40 UTC): **exactly 2,000 fighters; 1,964 (98.2%) have fighter_records**
- external_ids Δ+2,000 explained: exactly 2,000 fighters, **0 weight classes** (weight_classes unchanged 25)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 4294867 Yamaji 0-1-0/1 · 4294870 Alibekov 9-1-0/10 · 4294871 Abbasov 28-4-0/32 · 4410116 Damiani 11-7-1/19.
- Next-window IDs verified ascending beyond this window (4410531…).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push.

## 7. Verdict: **PASS** — window 5 fully consistent with W008–W011 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests.
