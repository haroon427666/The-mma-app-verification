# POST-AUDIT — PRODUCTION WINDOW 011 (Census Window 4)

**Run:** `6b6b0bb5-38ff-49a5-8ecc-8d6bd8a929f7` · COMPLETED · 2026-08-11 12:50:13 → 13:12:28 UTC · 1,334,852 ms
**Executed:** 2026-08-11 17:50:12 → 18:12:30 local · exit code 0 · log 8,062 lines

---

## 1. Scope
Independent read-only verification of the window-4 census expansion (approved LIMIT=2000). Ran after completion; no production writes. Live DB: `postgresql://mma:mma@localhost:5432/mma`.

## 2. Run record
| field | value |
|---|---|
| id | 6b6b0bb5-38ff-49a5-8ecc-8d6bd8a929f7 |
| status | COMPLETED |
| total_inserted | 3,967 |
| total_updated / skipped / errors | 0 / 0 / 0 |
| error | null |
| api_calls | 0 (tracked counter; actual requests = 4,000, verified from log) |

## 3. Log forensics (`PRODUCTION_WINDOW_011_CENSUS_SYNC_LOG.txt`)
- **Profiles fetched: 2,000** — `GET .../v2/sports/mma/athletes/<digits>` lines excluding `/records`
- **Records fetched: 2,000** — all `"/records \"HTTP/1.1 200 OK\""`
- **Non-200 HTTP lines: 0** — zero `HTTP/1.1 (?!200)` matches
- **Errors/retries/breaker: 0** (the only "NativeCommandError" line is the PowerShell stderr-capture wrapper artifact; regex hits on `429`/`503` are athlete-ID digits, e.g. `4252429`, in INFO-level httpx lines)
- **Discovery: 7/7 "already completed — skipping"** — no discovery requests made
- **End banner:** `✓ fighter inserted=3967 updated=0 skipped=0 errors=0` / `Status: COMPLETED | 1334852ms`
- Rate: 4,000 requests / 1,334.9 s ≈ **3.0 req/s** (inside validated envelope)
- Mode note: `fighter: mode=incremental reason=Recent sync (0h ago)` — heuristic only; fighter job is registry-window-based, mode has no behavioral impact (confirmed in code)

## 4. Database audit (after-state)
All integrity checks **0**; registry total **38,011** unchanged; **consumed 20,988 / pending 17,023**.

| entity | rows |
|---|---|
| fighters | 20,988 |
| fighter_records | 20,440 |
| statistics | 399 |
| rankings | 142 |
| competitors | 47 |
| external_ids | 21,345 |
| events / competitions / promotions | 24 / 260 / 48 |
| weight_classes | 25 |

- duplicate fighters / fighter_records / external_ids / registry: **0 / 0 / 0 / 0**
- orphans (fighter_records, rankings, statistics, competitors, external_ids): **0**
- NULL provider/external_id: **0** · unresolved rankings: **0**
- consumed↔fighter: **20,988 / 20,988 = 100%**
- W4 cohort (created ≥ 12:50:13 UTC): **exactly 2,000 fighters; 1,967 (98.35%) have fighter_records**
- external_ids Δ+2,001 explained: 2,000 fighters + 1 weight_class
- weight_classes Δ+1: "Women's Catch Weight" (external_id 1009), created 13:12:27 UTC — inline enrichment for a new fighter; benign (W010 created "Featherweight - DREAM (65kg)" the same way)
- checkpoints 3/3 COMPLETED; discovery 7/7 COMPLETED; alembic **008**

## 5. Spot checks
- Representatives (6/6): Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2 — all unchanged, records internally consistent.
- Fresh cohort samples consistent (summary ↔ W/L/D ↔ fights): 4294861 Sakamoto 0-1-0/1 · 4294862 Kim 0-2-0/2 · 4294864 Almeida Vilela 0-2-0/2 · 4294866 Mike Pope 7-3-0/10.
- Notable real fighters in cohort: Sean O'Malley 20-3-0/24 · Alexander Shabliy 25-4-0/29 · Naoki Inoue 21-5-0/26 — all internally consistent.
- Next-window IDs verified ascending beyond this window (4294867…).

## 6. Consent / change review
No code, schema, migration, or config change. Only data growth from the approved bounded run plus the two doc files expected to change. Git: HEAD `19a87c7` unchanged; nothing staged; no commit/push.

## 7. Verdict: **PASS** — window 4 fully consistent with W008–W010 behavior; window consumed exactly its budget; no drift, no anomalies, 0 dead-ends, 0 failed requests.
