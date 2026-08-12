# W019 RECOVERY — RUN R1 POST-AUDIT

**Date:** 2026-08-11 · **Run:** `7e0d0a87-b74a-4244-a838-fa22f7bf5ea7` (COMPLETED, partial)
**Audited at:** 2026-08-11T18:34:54Z (read-only, live PostgreSQL)

---

## 1. Execution summary

| Item | Value |
|---|---|
| Command | `ESPN_FIGHTER_SYNC_LIMIT=2000 python sync.py --full --entity fighter` |
| Window selected | **1,347** IDs (all pending — ascending unconsumed filter) |
| Resolved | **904** profiles (HTTP 200) |
| Left queued | **443** (breaker OPEN after connection-error burst) |
| Records phase | **NOT executed** (0 /records requests) |
| Inserted / updated / skipped / errors | 904 / 0 / 0 / **0** |
| Duration | 337,626 ms (~5.6 min) · ~2.68 req/s |
| Exit | 0 · status COMPLETED |

## 2. Registry movement

| Metric | Before R1 | After R1 | Δ |
|---|---|---|---|
| registry total | 38,011 | 38,011 | 0 |
| registry consumed | 36,664 | **37,568** | +904 |
| registry pending | 1,347 | **443** | −904 |
| fighters | 36,664 | **37,568** | +904 |
| consumed↔fighter | 100% | **100% (37,568/37,568)** | ✓ |

**Deferred W019 IDs (324) — ALL RECOVERED.** `next_pending` moved from 5310951 → **5362434**, confirming the entire 5310951–5311xxx deferred band was consumed. The first now-unconsumed IDs (5362434, 5362444, 5362446, …) are the residual beyond-W019 tail.

## 3. Network forensics (from the preserved sync log, 2,339 lines)

| Metric | Count |
|---|---|
| Total HTTP requests | 904 |
| HTTP 200 | 904 (100%) |
| HTTP 404 / 429 / 5xx / 503 | 0 / 0 / 0 / 0 |
| Connection-level errors (`ESPN connection error`) | **40** |
| Retry warnings | 40 (1s/2s/4s backoff via client exception path) |
| Breaker transitions | 1× `CLOSED → OPEN (5 consecutive failures)` @ 18:28:47 UTC |
| Breaker-OPEN rejections logged | 1,336 |
| `Athlete profile failed … Circuit breaker is OPEN` | 443 |
| `Fighter window: … left queued, NOT consumed` | 1 (443 ids) |
| Discovery requests / skips | 0 / 14 (7/7 walks skipped) |
| `[ERROR]` lines / Tracebacks | 0 / 0 |

**Root cause:** a ~24-second burst of connection-level failures (keep-alive/reset-class, empty exception messages) at 18:28:23–18:28:47 UTC. The wire stayed clean (no HTTP 5xx) — this is a *different* failure signature from W019's 44× HTTP 503. The client's exception-retry path correctly applied backoff, and 5 consecutive failures opened the breaker per design. The healthy-gate then preserved the 443 unresolved IDs.

**Post-run re-probe (18:34 UTC, read-only):** all 200 again on deferred IDs, records endpoints, control 3332412, and `/leagues` — ESPN connection health recovered at low volume. The instability is **bursty under sustained ~3 rps load**, not a persistent outage.

## 4. Integrity (fresh live audit)

duplicates: fighters **0** · fighter_records **0** · registry **0** · external_ids **0**
orphans: fighter_records **0** · rankings **0** · statistics **0** · competitors **0** · external_ids **0**
NULL provider/external_id **0** · unresolved rankings **0** (142/142) · alembic **008**
checkpoints fighter/ranking/records **3/3 COMPLETED** · discovery **7/7 COMPLETED** · sync_runs 34 (32 COMPLETED + 2 stale RUNNING)

## 5. Representatives

Makhachev **28-1-0** · Ngannou **19-3-0** · DJ **25-4-1** · Rousey **13-2-0** · Gracie **15-2-2** · Shamrock **29-17-2** — all present, unchanged.

## 6. Current state after R1

| State | Value |
|---|---|
| Registry | 37,568 consumed / **443 pending** / 38,011 total |
| Next pending ID | **5362434** |
| Fighters | 37,568 |
| fighter_records | 34,183 |
| Fighters missing records | **3,385** (805 genuine floor + 1,676 W019 deferred + 904 R1 deferred) |
| Census completion | **NOT complete** (443 IDs remain) |
| Records completion (R2) | **NOT executed** |

## 7. What was NOT done (deliberately)

- **No auto-rerun** of the 443 queued IDs — protocol stop condition after breaker trip.
- **No R2** (records backfill for the 2,580 deferred record-fighters) — stopped pending a new gate.
- No discovery, no migration, no records fabrication, no manual DB edits, no commit/push.
- No deletion/reset of any existing data; W019 historical artifacts preserved.

## 8. Risks / notes for the next gate

1. **Bursty connection-level ESPN instability** under sustained load is the recurring theme (W019 HTTP 503s; R1 connection errors). The breaker + healthy-gate absorb it safely — partial consumption, zero integrity impact.
2. **443 census IDs remain** (next 5362434) — a single bounded `--entity fighter` run when ESPN is stable will finish the census.
3. **2,580 fighters lack records** (1,676 W019 + 904 R1) — R2 (`--entity records`, registry-neutral) is the prescribed completion path; the 805 genuine-absence floor will remain and must not be counted as failure.
4. Options for the next gate: (a) one fighter run to finish the 443, then R2; (b) R2 first, then finish the 443; (c) lower per-run rate to reduce burst risk — all require explicit user approval.
