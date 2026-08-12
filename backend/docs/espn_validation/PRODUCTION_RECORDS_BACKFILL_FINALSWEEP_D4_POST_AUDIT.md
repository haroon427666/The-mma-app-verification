# PHASE D D4 — POST-AUDIT

> **Audit time (UTC):** 2026-08-12 (immediately after D4 write) · read-only against live PostgreSQL 18.4 `localhost:5432/mma` · git HEAD `19a87c7`

## 1. Table-mutation audit — ONLY `fighter_provider_record_status` changed
| Table | Δ |
|---|---|
| fighter_provider_record_status | **+1,224** (0 → 1,224; intended) |
| fighter_records | 0 |
| fighters | 0 |
| external_ids / weight_classes / rankings / statistics / competitors / events / competitions / promotions | 0 |
| sync_discovered_athletes (registry) | 0 |

**No unrelated mutations.** No `fighter_records` rows created or modified. No `fighters` rows changed.

## 2. Status-table integrity — ALL GREEN
- rows = **1,224** · provider=`espn` AND status=`CONFIRMED_ABSENT` = **1,224**
- duplicate identities `(fighter_id, provider)` = **0**
- orphan rows (fighter_id not in `fighters`) = **0**
- NULL required fields (provider / status / last_checked_at / retry_count) = **0**
- provenance: CENSUS_FLOOR **805** · BACKFILL_BATCH **414** · FINAL_SWEEP **5**

## 3. Scope invariants — ALL HELD
- registry total **38,011** / consumed **38,011** / pending **0** (unchanged)
- fighters **38,011** · fighter_records **36,787** · missing **1,224** (unchanged)
- external_ids **38,368** · weight_classes **25** · rankings **142** · statistics **399** · competitors **47** · events **24** · competitions **260** · promotions **48** (unchanged)
- alembic **009** (unchanged)

## 4. Representatives — 6/6 unchanged
Makhachev **28-1-0** · Ngannou **19-3-0** · DJ **25-4-1** · Rousey **13-2-0** · Gracie **15-2-2** · Shamrock **29-17-2**.

## 5. Evidence provenance
- `last_checked_at` = final-sweep completion **2026-08-12 08:47:45 UTC** (all 1,224 re-probed by run `7852a339`, log-verified — FINALSWEEP POST_AUDIT §8).
- `last_run_id` = `7852a339-2a20-4ceb-868e-c9888d3a22cd` (found COMPLETED in `sync_runs`).
- `last_http_status` = **200** for all rows (final sweep: 1512×HTTP 200, 0 errors/retries/breaker).
- No timestamps or run IDs invented.

## 6. Idempotency
Rerun of the D4 insert (`ON CONFLICT (fighter_id, provider) DO NOTHING`) inserted **0 new rows** and re-passed every check — duplicate status rows are impossible (PK identity).

## 7. Semantic guardrails re-confirmed
- Empty-payload evidence **never** fabricated `fighter_records` (still 36,787).
- `CONFIRMED_ABSENT` rows **cannot** block a future real record — persisting a record deletes the status row (`FighterUpsert._delete_record_status`, tested).
- No ESPN contact during D4; no `sync.py`; no discovery; no registry consumption.

## 8. Conclusion
**D4 PASS.** All 1,224 historically confirmed absences are now explicit, durable, provider-scoped state; the database is internally consistent; every invariant holds; the operation is fully reversible (DELETE of the 1,224 rows restores the pre-D4 state). **D5 (API exposure) and D6 (full docs/closeout) remain unexecuted and require explicit approval.**
