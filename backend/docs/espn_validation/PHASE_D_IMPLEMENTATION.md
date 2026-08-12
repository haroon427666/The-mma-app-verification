# PHASE D — PERSISTED ESPN RECORD-ABSENCE CLASSIFICATION · IMPLEMENTATION RECORD

> **Status:** D1–D6 COMPLETE (2026-08-12) — D1–D3 (schema+provider+job+tests) · D4 (1,224-row historical backfill) · **D5 (additive `record_fetch` API field + repository helpers + contract tests) COMPLETE** · D6 (docs) · **Git HEAD:** `19a87c7` (0/0 ahead/behind, nothing staged/committed/pushed)
> **Scope:** make the proven absence of ESPN fighter records **explicit and durable**, so "no record exists" is never confused with "never checked" or "fetch failed". No census, no records sweep, no registry operation — a data-quality/state-classification feature.

---

## 1. Objective & state semantics

Before Phase D, a fighter without a `fighter_records` row was ambiguous: the single `LEFT JOIN … WHERE NULL` "missing" definition conflated *never fetched*, *fetched-and-empty*, and *fetch failed* (proven in the D1–D3 design review). Phase D persists per-provider evidence of non-available outcomes:

| State | Representation |
|---|---|
| `HAS_RECORD` | derived — `fighter_records` row exists (no status row kept) |
| `CONFIRMED_ABSENT` | status row (`status='CONFIRMED_ABSENT'`) — provider queried successfully, no usable payload |
| `FETCH_FAILED` | status row (`status='FETCH_FAILED'`) — transient (429/5xx/network/breaker), retryable within budget |
| `PERMANENT_FAILURE` | status row (`status='PERMANENT_FAILURE'`) — reserved, non-retryable |
| `NOT_CHECKED` | **no row** (implicit) |

**Critical lifecycle rule:** a persisted absence **never** blocks a future real record — persisting a record deletes the status row (`FighterUpsert._delete_record_status`). `TEMPORARILY_UNAVAILABLE` is intentionally NOT a persisted state (the final sweep had 0 transient failures; W019-era 503s were historical and re-probed).

## 2. Data model — `fighter_provider_record_status`

Sparse, provider-scoped evidence table. PK `(fighter_id, provider)` → exactly one row per fighter+provider; idempotent upserts; provider independence (an ESPN absence never suppresses a future UFCStats check).

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `fighter_id` | UUID | PK, NOT NULL, FK → fighters.id ON DELETE CASCADE | same UUID storage as `fighters.id`/`fighter_records.fighter_id` (dialect-consistent joins) |
| `provider` | VARCHAR(20) | PK, NOT NULL | `'espn'` today; multi-provider ready |
| `status` | VARCHAR(30) | NOT NULL | `CONFIRMED_ABSENT` · `FETCH_FAILED` · `PERMANENT_FAILURE` (SCREAMING_SNAKE per repo convention; no DB enum) |
| `last_checked_at` | TIMESTAMPTZ | NOT NULL | when the outcome was observed |
| `last_http_status` | INTEGER | NULLABLE | evidence (200/404/503/…) |
| `result_detail` | TEXT | NULLABLE | e.g. "http 200 — no usable record payload" |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | increment per transient failure; reset on CONFIRMED_ABSENT |
| `last_run_id` | UUID | NULLABLE, FK → sync_runs.id | run that produced the outcome |
| `provenance` | VARCHAR(30) | NULLABLE | `CENSUS_FLOOR` · `BACKFILL_BATCH` · `FINAL_SWEEP` (first-confirmation cohort) |
| `created_at` / `updated_at` | TIMESTAMPTZ | NOT NULL | TimestampMixin |

**Indexes:** `ix_fighter_provider_record_status_provider_status` on `(provider, status)` — supports the records-job selection filter.

## 3. Migration `009_fighter_provider_record_status`

- `revision 009`, `down_revision 008` — single head.
- **Upgrade:** `create_table` (PK, 2 FKs, index) — pure additive, zero impact on existing tables/data. **Applied live 008 → 009 (2026-08-12).**
- **Downgrade:** drop index + table — clean and reversible.

## 4. Provider outcome surfacing (D2)

`src/providers/espn/provider.py`:
- `fetch_fighter_record(external_id)` — **unchanged contract** (`FighterRecord | None`); delegates to the new method.
- `fetch_fighter_record_with_outcome(external_id)` → `(record, RecordFetchOutcome, http_status)`:
  - 200 + real payload → `AVAILABLE`, 200
  - 200 empty body / content-dependent **404** → `EMPTY` (NORMAL provider behavior — client never retries 4xx, breaker untouched)
  - 429-exhausted / 5xx-exhausted / other HTTP errors → `FAILED` (+ warning log)
  - network/connection/breaker-open → `FAILED`, status `None`

`client.py` breaker/retry/rate-limiter: **unchanged.**

## 5. Sync behavior (D3)

`src/providers/espn/jobs/records.py` (`ESPN_RecordsBackfillJob`):
- **Selection** now LEFT-JOINs the status table and excludes fighters whose absence is established evidence: `CONFIRMED_ABSENT`, `PERMANENT_FAILURE`, or `FETCH_FAILED` with `retry_count >= MAX_RECORD_FETCH_RETRIES (3)`. Ascending `external_id` order and `ESPN_RECORDS_BACKFILL_LIMIT` preserved — registry-neutral by construction.
- `_fetch` returns `(FighterDTO, outcome, http_status)` tuples; summary line reports real/empty/failed counts.
- `_upsert` persists status rows and logs aggregate counts (`status_absent` / `status_failed` / `status_cleared`).

`src/sync/upserts/fighter.py` (`FighterUpsert`):
- `apply_record_fetch_outcomes(dtos, run_id)` — portable `ON CONFLICT (fighter_id, provider)` upsert (same idiom as `CheckpointManager`): `EMPTY → CONFIRMED_ABSENT` (retry reset), `FAILED → FETCH_FAILED` (retry_count + 1), `AVAILABLE →` clears the row. Race-free, idempotent.
- `_delete_record_status` fires inside `_upsert_record` on **every** real record persist (records job + fighter job shared path) — the "absence never blocks a record" invariant.

`src/sync/types.py` — `RecordFetchOutcome` (`AVAILABLE`/`EMPTY`/`FAILED`) and `RecordFetchStatus` (`CONFIRMED_ABSENT`/`FETCH_FAILED`/`PERMANENT_FAILURE`), matching the repo's string-constant/SCREAMING_SNAKE convention (no SQL enum types).

## 6. D4 — historical classification backfill (executed 2026-08-12)

One-time **DB-only** write (zero ESPN requests, zero `sync.py` runs). Read-only reconciliation derived **exactly 1,224 fighters missing `fighter_records`** (abort-on-mismatch gates) and split by documented evidence:

| Provenance | Count | Basis |
|---|---|---|
| `CENSUS_FLOOR` | 805 | pre-W019 floor (`external_id` < 5238639); officials/referees/placeholders; 0% yield in every sweep |
| `BACKFILL_BATCH` | 414 | post-W019 empties probed by records-backfill Batches 1–2 (`0f8d2a74`, `66dc4dfa`); placeholder clusters + singletons |
| `FINAL_SWEEP` | 5 | 5350060 Scano · 5350061 Dudley · 5369837 Cotton · 5386478 Tesic · 5386479 Badrljica (run `7852a339`) |

All rows: `provider='espn'`, `status='CONFIRMED_ABSENT'`, `last_checked_at` = final-sweep completion **2026-08-12 08:47:45 UTC**, `last_run_id` = **`7852a339-2a20-4ceb-868e-c9888d3a22cd`** (verified COMPLETED in `sync_runs`), `last_http_status=200` (all 1,224 re-probed by the final sweep with HTTP 200 — log-verified). Single transaction, `ON CONFLICT DO NOTHING`; **rerun inserted 0 new rows (idempotency proven)**. No `fighter_records` rows created; no fighters/external_ids/registry changed.

## 7. Multi-provider semantics

Status is per `(fighter_id, provider)` — mirroring the architecture's existing provider scoping (`external_ids.provider`, `sync_checkpoints` per entity+provider, `sync_discovered_athletes` per provider+external_id). A `CONFIRMED_ABSENT` for `espn` does not suppress a future `ufcstats` check; adding a provider requires zero schema change (new rows only).

## 8. API impact — D5 additive exposure (COMPLETE 2026-08-12)

D5 exposed the persisted outcome through the existing fighter-profile endpoint as a strictly evidence-backed, **additive** field:

- `src/schemas/fighter.py` — new optional nested model `FighterRecordFetchStatus` (status · provider · last_checked_at · last_http_status · result_detail · retry_count · provenance) + `FighterProfileResponse.record_fetch: FighterRecordFetchStatus | None = None`.
- `src/db/repositories/fighter.py` — `get_record_fetch_status(fighter_id, provider)` + batch `get_record_fetch_statuses(fighter_ids, provider)` (single query, no N+1).
- `src/services/fighter_service.py` — `get_fighter_detail` returns `record_fetch` (provider from `fighter.source_provider`, fallback `espn`).
- `src/api/v1/fighters.py` — `_fighter_to_profile` maps it via `_record_fetch_to_schema`.

**Semantics:** `record_fetch` is present ONLY when a status row exists (`CONFIRMED_ABSENT` / `FETCH_FAILED` / `PERMANENT_FAILURE`). It is `null` when the fighter has a real record (`record` is the canonical HAS_RECORD signal) or has never been checked (NOT_CHECKED) — **no synthetic "AVAILABLE" state is fabricated**. Purely additive: no field renamed, removed, or re-typed; no endpoint added/removed; mobile untouched; contract tests prove the pre-existing profile shape is unchanged.

## 9. Tests (implemented, all green)

- `tests/unit/test_record_fetch_outcome.py` (6): empty-200 → EMPTY · real payload → AVAILABLE · 404 → EMPTY (not failure) · 503 → FAILED · network → FAILED · backward-compatible `fetch_fighter_record`.
- `tests/integration/test_record_fetch_status.py` (9): EMPTY → CONFIRMED_ABSENT without fabrication · FAILED → FETCH_FAILED with retry increments · repeated-outcome idempotency · AVAILABLE clears row · real record deletes absence · provider scoping · job selection (skips confirmed/permanent/exhausted; includes retryable) · registry untouched.
- `test_migration_coverage.py` extended for the new table.
- **D5 contract tests:** `tests/api/test_fighter_record_fetch_contract.py` (8: schema default/roundtrip + mapper omit/include/has-record semantics) and `TestRecordFetchApiAccess` in `tests/integration/test_record_fetch_status.py` (4: repository single/batch lookup + service detail + full chain to JSON).
- **Full suite: 505 passed / 2 skipped · ruff clean · mypy 0 errors** (changed surface).

## 10. Invariants & safety guarantees

- Registry-neutral: `sync_discovered_athletes` never read/written by records or status paths.
- No `fighter_records` fabrication; stored values never reset; no 0-0-0-0 placeholders.
- Status rows idempotent (PK `(fighter_id, provider)`); duplicates impossible.
- Absence never blocks a future record (record persist deletes the row).
- Failures are never absence evidence (`FAILED → FETCH_FAILED`, retry budget 3).
- Reversible: migration downgrade + `DELETE` of the 1,224 rows restore the pre-D4 state.
- Post-D4 live state: status rows **1,224** · fighters **38,011** · fighter_records **36,787** · registry **38,011/38,011/0** · alembic **009** · reps 6/6 unchanged.

## 11. Artifacts

Implementation: migration `009`, `src/db/models/support.py`, `src/sync/types.py`, `src/providers/espn/provider.py`, `src/providers/espn/jobs/records.py`, `src/sync/upserts/fighter.py`, 2 new test files, `test_migration_coverage.py`. **D5:** `src/schemas/fighter.py`, `src/db/repositories/fighter.py`, `src/services/fighter_service.py`, `src/api/v1/fighters.py`, `tests/api/test_fighter_record_fetch_contract.py`.
Evidence (this directory): `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_D4_BASELINE.json` · `..._D4_AFTER.json` · `..._D4_REPORT.md` · `..._D4_POST_AUDIT.md` · `..._D4_RECONCILIATION.json`. Design review: prior session record (Phase D design A–Q + APPROVAL GATE). Journey §39; handoff refreshed.

## 12. Decision gates

- **D1–D3** — APPROVED + COMPLETE (schema 009, provider outcome, records-job handling, tests).
- **D4** — APPROVED + COMPLETE (1,224-row historical backfill).
- **D5** (additive `record_fetch` API field + repository helpers + contract tests) — APPROVED + COMPLETE (2026-08-12).
- **D6** (docs/closeout) — COMPLETE.
- No commit/push without explicit instruction (HEAD `19a87c7`, 0/0, nothing staged).
