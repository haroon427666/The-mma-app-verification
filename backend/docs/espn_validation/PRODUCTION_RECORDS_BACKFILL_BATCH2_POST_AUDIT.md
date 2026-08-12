# RECORDS BACKFILL — BATCH 2 POST-AUDIT

> **Audit time (UTC):** 2026-08-11 20:06:57 · read-only against live PostgreSQL `localhost:5432/mma` · git HEAD `19a87c7`

## Scope
Post-run verification of Batch 2 (`66dc4dfa`, `ESPN_RECORDS_BACKFILL_LIMIT=3000`, `--entity records`).

## 1. Registry side-effect check — INVARIANT HELD
| Metric | Value |
|---|---|
| registry total | **38,011** (unchanged) |
| registry consumed | **38,011** (unchanged) |
| registry pending | **0** (unchanged) |
| consumed-without-fighter | 0 |

Records backfill is **registry-neutral in practice (6th production confirmation)** — the discovery registry was never read, written, or advanced.

## 2. Table-mutation audit (intentional deltas only)
| Table | Δ | Expected? |
|---|---|---|
| fighter_records | **+1,781** | ✓ intended (records backfill) |
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

## 4. Yield forensics — explained
- Requests: 3,000 (all `/athletes/{id}/records`)
- Real payloads: **1,781** · empty/unavailable: 1,219 · overall yield 59.4% · **deferred-portion yield 81.1%**
- **Why the overall number is lower:** the ascending sweep re-probes the **805-ID genuine-absence floor first (0% yield by design)**; the deferred band additionally contains the **Mongi Zitouni/Ludovic Dandine placeholder cluster** (W019-band extension of the W018 placeholder pattern, IDs 5238639+ — genuine empty payloads). **No fabrication, no error.**
- **Coverage caveat:** because the floor re-sorts first, the 3,000-ID window reached only **2,195 of the 2,488 deferred** — **293 deferred (highest-ID tail, to 5386479) remain unprobed**. A final small sweep (LIMIT≈300) would close them; NOT authorized this session.

## 5. HTTP / breaker / retry forensics
| Metric | Value |
|---|---|
| HTTP 200 | 3000 |
| HTTP 404 / 429 / 503 / other 5xx | 0 / 0 / 0 / 0 |
| connection errors | 0 |
| retries | 0 |
| breaker events | 0 |
| errors / tracebacks | 0 / 0 |
| discovery requests | 0 |
| request rate | ~2.98 rps |

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

## 9. Cumulative Task 2 status
| Metric | Value |
|---|---|
| Batch 1 | +95 records |
| Batch 2 | +1,781 records |
| **Task 2 cumulative** | **+1,876 records** (34,623 → 36,499) |
| missing before Task 2 / after | 3,388 → **1,512** |
| deferred backlog before / after | 2,580 → **293 unprobed tail** (+414 confirmed genuine empties) |

## 10. Conclusion
**Batch 2 PASS.** All invariants held; no anomalies. Remaining: **1,512 missing** = 805 permanent floor + 707 post-W019 (414 genuine empties + 293 unprobed tail). Awaiting explicit approval for a final small sweep (LIMIT≈300) if desired.
