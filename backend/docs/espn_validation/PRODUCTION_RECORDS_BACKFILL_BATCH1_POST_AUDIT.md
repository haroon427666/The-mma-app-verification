# RECORDS BACKFILL — BATCH 1 POST-AUDIT

> **Audit time (UTC):** 2026-08-11 19:41:54 · read-only against live PostgreSQL `localhost:5432/mma` · git HEAD `19a87c7`

## Scope
Post-run verification of Batch 1 (`0f8d2a74`, `ESPN_RECORDS_BACKFILL_LIMIT=1000`, `--entity records`).

## 1. Registry side-effect check — INVARIANT HELD
| Metric | Value |
|---|---|
| registry total | **38,011** (unchanged) |
| registry consumed | **38,011** (unchanged) |
| registry pending | **0** (unchanged) |
| consumed-without-fighter | 0 |

Records backfill is **registry-neutral by construction and in practice** — the discovery registry was never read, written, or advanced. This batch re-confirms the invariant (4th independent production confirmation after W007 batches 1–4).

## 2. Table-mutation audit (intentional deltas only)
| Table | Δ | Expected? |
|---|---|---|
| fighter_records | **+95** | ✓ intended (records backfill) |
| fighters | 0 | ✓ intended (backfill never creates fighters) |
| external_ids | 0 | ✓ |
| weight_classes | 0 | ✓ |
| rankings / statistics / competitors / events / competitions / promotions | 0 | ✓ stable |
| sync_discovered_athletes | 0 | ✓ registry-neutral |

**No unrelated mutations.** Stable tables unchanged.

## 3. Integrity audit — ALL GREEN
- duplicate fighters **0** · duplicate fighter_records **0** · duplicate registry **0** · duplicate external_ids **0**
- orphan fighter_records **0** · orphan rankings **0** · orphan statistics **0** · orphan competitors **0** · orphan external_ids (fighter) **0**
- NULL provider **0** · NULL external_id **0**
- unresolved rankings **0** (142/142 resolve)

## 4. Yield forensics — explained low yield
- Requests: 1,000 (all `/athletes/{id}/records`)
- Real payloads: **95** · empty/unavailable: 905 · yield 9.5%
- **Why:** the sweep is ascending by `fighters.external_id`; Batch 1's window contained the **805-member genuine-absence floor** (previously probed and exhausted — 0% yield by design) plus a **~100-ID placeholder/official band** (repeated "Mongi Zitouni"/"Ludovic Dandine" profiles, IDs 5238639–5238xxx). Both classes return genuine empty payloads. **No fabrication, no error** — matches the documented W013/W018 placeholder-band precedent.
- **Forecast:** Batch 2+ crosses into the remaining **2,488 deferred fighters** (5238739+) with materially higher yield.

## 5. HTTP / breaker / retry forensics
| Metric | Value |
|---|---|
| HTTP 200 | 1000 |
| HTTP 404 / 429 / 503 / other 5xx | 0 / 0 / 0 / 0 |
| connection errors | 0 |
| retries | 0 |
| breaker events | 0 |
| errors / tracebacks | 0 / 0 |
| discovery requests | 0 |
| request rate | ~3.0 rps |

Breaker stayed CLOSED the entire run. No healthy-gate intervention.

## 6. Representative verification (6/6 — untouched)
Makhachev **28-1-0** · Ngannou **19-3-0** · DJ **25-4-1** · Rousey **13-2-0** · Gracie **15-2-2** · Shamrock **29-17-2**.

## 7. Checkpoint / discovery / migration
- sync checkpoints **3/3 COMPLETED** (fighter · ranking · records) — unchanged
- discovery **7/7 COMPLETED** — unchanged, no re-walk
- alembic **008** — no migration

## 8. Data-quality guarantees re-confirmed
- Empty ESPN payload → **no row** (never a fake 0-0-0-0)
- Existing valid records **never reset/overwritten**
- Failed/unavailable fetches keep the fighter in the missing set (crash-safe rerun re-probes exactly the remainder)

## 9. Conclusion
**Batch 1 PASS.** All invariants held; no anomalies. Remaining work: **2,488 deferred fighters** (post-W019) + 805 floor (permanent, 0% yield) = 3,293 missing. Awaiting explicit approval for Batch 2.
