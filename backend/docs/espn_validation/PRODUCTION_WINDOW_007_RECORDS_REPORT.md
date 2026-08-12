# PRODUCTION WINDOW 007 — Records Backfill Report

**Date:** 2026-08-11 (UTC) · **Type:** bounded records-only backfill (batch 1)
**Command:** `PYTHONIOENCODING=utf-8 ESPN_RECORDS_BACKFILL_LIMIT=1000 python sync.py --full --entity records`

---

## 1. Verdict: **PASS**

Batch 1 completed cleanly: `COMPLETED, inserted=638, updated=0, skipped=362, errors=0`, 341,651 ms (~5.7 min), 0×HTTP 429, contained transient 503s (breaker never opened; retries absorbed them). The census discovery registry was **not touched** — consumed/pending stayed exactly 12,988 / 25,023.

## 2. Architecture finding (Phase 1)

**No safe records-only mechanism existed.** Records are coupled to the fighter job (`_attach_records` → `FighterUpsert.upsert_batch`); `EntityType` had no `records` entity; `--entity fighter` runs the next census window (would consume 25,023 pending registry IDs) — NOT a records backfill. Additionally, routing a records-only DTO through `upsert_batch` is unsafe: `BaseUpsert._changed_fields` treats every stored profile value as changed when the DTO field is None (`None != value`), clobbering fighter profile columns to NULL.

**Minimal isolated change required (documented, per W007 Phase 4):**
1. `backend/src/sync/types.py` — added `EntityType.RECORDS = "records"`.
2. `backend/src/sync/upserts/fighter.py` — added public `FighterUpsert.upsert_records(dtos)`: writes **only** `fighter_records` via the existing idempotent `_upsert_record`; resolves fighter UUIDs from existing fighters only (no speculative creation); registry-neutral.
3. `backend/src/providers/espn/jobs/records.py` (new) — `ESPN_RecordsBackfillJob`: DB-selects existing fighters missing `fighter_records` (deterministic external-ID order, bounded by `ESPN_RECORDS_BACKFILL_LIMIT`), fetches `/athletes/{id}/records` with bounded concurrency (breaker/rate-limiter protected), writes via `upsert_records`. Never reads/writes the discovery registry, never runs discovery walks.
4. `backend/src/providers/espn/jobs/__init__.py` — export the new job.
5. `backend/sync.py` — registered the job under `EntityType.RECORDS` in `build_engine`.

Quality gates before execution: ruff ✓, mypy ✓ (4 files), import chain ✓, focused pytest **49/49 passed** (discovery/ranking-injection/state-store/records/stats/resume).

## 3. Target (Phase 2) — exact classification

- Fighters total: **12,988** · with records: 7,387 · **without records: 5,601**
- Missing band: external IDs 2,431,356 → 3,142,694
- Cohort split: **~993 pre-existing** (before W006) + **~4,608 from W006** (records phase interrupted by 44×503 / breaker open)
- Notable data-quality observation: the low-ID missing band is dominated by **non-MMA athletes from the census** — referees/officials ("Herb Dean", "John McCarthy", "Steve Mazzagatti", "Mario Yamasaki"…) and placeholder rows ("Opponent TBA", ID 2431356). These are expected to return empty records (content-dependent absence) — documented, not silently fixed.
- Duplicate `fighter_records` rows: 0 (pre-batch).

## 4. Baseline (Phase 3)

`PRODUCTION_WINDOW_007_RECORDS_BASELINE.json` — fighters 12,988 · records 7,387 · missing 5,601 · registry 38,011 (12,988 consumed / 25,023 pending) · alembic 008 · HEAD `19a87c7`. All integrity checks 0.

## 5. Execution (Phase 5) — batch 1, bounded to 1,000

- **1,022 API requests** (1,000 initial + 22 retries) — **0 discovery requests**
- Response mix: **999× HTTP 200**, 0× HTTP 404, 23× HTTP 503 (10 distinct athlete IDs; client retries absorbed most)
- **638 records inserted** (real record payloads) · **362 skipped** (empty/200 or unresolved)
- Registry consumed/pending **unchanged** ✓ (12,988 / 25,023) — the backfill is registry-neutral by construction
- Sync run `9d04653c` COMPLETED (341,651 ms ≈ 5.7 min ≈ **3.0 req/s** — inside the validated envelope)
- `records` checkpoint row created: COMPLETED

## 6. Post-backfill audit (Phase 7) — all ✓

| Check | Result |
|---|---|
| duplicate fighter_records | **0** |
| duplicate fighters / external_ids / registry rows | **0 / 0 / 0** |
| orphan fighter_records / rankings / statistics / competitors / external_ids | **0 / 0 / 0 / 0 / 0** |
| NULL provider/external_id | **0** |
| unresolved rankings | **0 (142/142 resolve)** |
| registry consumed/pending | **12,988 / 25,023 — unchanged** |
| fighters (identity) | 12,988 — unchanged (no new/duplicated fighters) |

## 7. Quality classification (Phase 8)

- Successfully backfilled: **638**
- Legitimate absence (HTTP 200, empty payload — officials/placeholders etc.): ~**352**
- Operationally missed (503, unresolved): **≤ 10** distinct IDs (23×503 responses, retries absorbed the rest) — these remain in the missing set and are re-probed by the next batch
- Still missing after batch 1: **4,963**

## 8. Representatives (Phase 9) — all present, unchanged

Makhachev 28-1-0 · Ngannou 19-3-0 · DJ 25-4-1 · Rousey 13-2-0 · Gracie 15-2-2 · Shamrock 29-17-2. (All had records before; batch 1 targeted lower-ID fighters, so none were re-touched.)

## 9. Performance (Phase 10)

| Metric | W006 (records phase) | W007 batch 1 |
|---|---|---|
| 503s | 44 (breaker OPENED) | 23 (breaker stayed CLOSED; retries absorbed) |
| 429s | 0 | 0 |
| records inserted | 392 | **638** |
| requests | 5,437 total | 1,022 (records only) |
| rate | ~3.0 req/s | ~3.0 req/s |
| elapsed | 30.4 min (whole window) | 5.7 min (records only) |

## 10. Known limitation (documented, not a blocker)

The target query has no persisted "records absent" marker, so known-empty fighters (the ~352 officials/placeholders) are **re-probed on every bounded batch** — they lead the external-ID ordering, giving each batch a ~64% new-record yield (638/1,000). Still bounded, safe, and idempotent; a future Phase D (small migration adding a persisted absence flag) would eliminate the ~36% waste. Not required for correctness.

## 11. Files created / modified

Created: `PRODUCTION_WINDOW_007_RECORDS_BASELINE.json` · `PRODUCTION_WINDOW_007_RECORDS_AFTER.json` · `PRODUCTION_WINDOW_007_RECORDS_SYNC_LOG.txt` · this report · `PRODUCTION_WINDOW_007_RECORDS_POST_AUDIT.md`.
Code (uncommitted, required for this operation): `types.py`, `upserts/fighter.py`, `jobs/records.py` (new), `jobs/__init__.py`, `sync.py`.
Docs updated: `ESPN_PRODUCTION_JOURNEY.md` (appended §16), `ESPN_HANDOFF_STATE.md`.

## 12. Decision gate (Phase 12): **B — continue with another bounded records batch**

The backlog is the largest unresolved data-quality issue (4,963 missing). The mechanism is proven safe (registry-neutral, breaker-safe, idempotent). Recommendation: **W007 batch 2 — `ESPN_RECORDS_BACKFILL_LIMIT=1000`** (≈5.7 min, ~1,000 requests). Repeat until the backlog is ~3,600 (the officials/placeholder floor) or a Phase D absence-marker is approved. Census expansion (C) should wait until the records backlog is resolved.

## 13. Git safety (Phase 13)

No staged files · no commit · no push. The 5 code files are the documented minimal implementation change; all other working-tree changes (mobile/planning/session) untouched. Frozen research untouched. DB writes were exclusively the approved bounded backfill.
