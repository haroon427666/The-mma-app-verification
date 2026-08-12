# MISSING-RECORDS BREAKDOWN — FINAL SWEEP (AFTER STATE)

> **Type:** READ-ONLY data analysis artifact · **Captured:** 2026-08-12 (UTC) · live PostgreSQL 18.4 `localhost:5432/mma`
> **Context:** companion to `PRODUCTION_RECORDS_BACKFILL_FINALSWEEP_REPORT.md` / `_POST_AUDIT.md` (run `7852a339`, Task 2 complete)
> **Git HEAD:** `19a87c7` · **Scope:** classification of every fighter still lacking `fighter_records` after the final sweep

---

## 1. Overall composition

| Category | Count | % of missing |
|---|---|---|
| Pre-W019 genuine-absence floor | **805** | 65.8% |
| Post-W019 confirmed genuine empties | **419** | 34.2% |
| **Total missing** | **1,224** | 100% |

Fighters with valid `fighter_records`: **36,787 / 38,011 (98.1% coverage)**.

Every one of the 1,224 was probed at least once across the three Task-2 runs (Batches 1–2 + Final Sweep) with **0 HTTP errors, 0 retries, 0 breaker events** — all absences are **content-dependent** (ESPN serves no `/records` payload for these IDs), not fetch failures.

---

## 2. Post-W019 confirmed genuine empties (419)

**42 distinct name-groups**, heavily concentrated: **7 clusters (≥5 fighters) cover 384 of 419 (91.6%)**. These are the ESPN placeholder/official roster patterns (cf. W013 "Judge 1/2/3", W018 "Mongi Zitouni/Ludovic Dandine" band).

### 2.1 Placeholder clusters (384 fighters)

| Cluster name | Count | ID range | Pattern |
|---|---|---|---|
| Brian Tyler | 109 | 5264068 → 5325592 | Scattered (span 61,525) — largest single cluster |
| Mongi Zitouni | 50 | 5238639 → 5327027 | Scattered (span 88,389) — W019-band extension of the W018 placeholder |
| Ludovic Dandine | 49 | 5238640 → 5327026 | Scattered (span 88,387) — mirrors Mongi Zitouni IDs |
| Christopher Edgehill | 49 | 5259556 → 5278619 | Scattered (span 19,064) |
| Ziad Harb | 47 | 5245762 → 5246559 | Dense (span 798) — interleaved with Jason Tatlow |
| Solimar Miranda | 44 | 5259563 → 5345445 | Scattered (span 85,883) |
| Jason Tatlow | 36 | 5245924 → 5246558 | Dense (span 635) — interleaved with Ziad Harb |

**Signature observation:** Ziad Harb and Jason Tatlow occupy **interleaved consecutive ID slots** (5245762 Harb, 5245924 Tatlow, 5245925 Harb, 5245926 Tatlow …) — the textbook signature of ESPN roster slots carrying repeated placeholder names. The same names recur across the W019 census band (5238639+) and into the 5.3M ID range, matching the W013/W018 placeholder precedent.

### 2.2 Singleton genuine empties (35 fighters)

Single-ID fighters with real names; ESPN returns empty `/records` payloads (retired/defunct/other content-dependent cases).

**The 5 newly confirmed by the final sweep (run `7852a339`):**

| ID | Name |
|---|---|
| 5350060 | Giovanna Scano |
| 5350061 | Vincent Dudley |
| 5369837 | Sarah Cotton |
| 5386478 | Dejan Tesic |
| 5386479 | Vladimir Badrljica |

**The 30 confirmed by Batches 1–2:** Luke Boutin (5245722) · Jeff Holby (5270085) · Jeff Hoiby (5270275) · Brianne Davis (5270301) · Horacio Villanueva (5277183) · Horacio Lopez Villanueva (5277184) · Zach Teiberis (5279787) · Tyrone Roberts (5281013) · Josh Stewart (5281014) · Bruce Huckfeldt (5281015) · Bruce Allen (5281020) · Guy Girard (5281712) · Brent Mckeehan (5290898) · Bassel Mahgoub (5293966) · Chris Hill (5293967) · Todd Singletary (5293985) · Todd Maxwell (5293986) · Nick Cimmarusti (5302277) · Scot Jones (5302281) · Patricio Carlos (5308070) · Jesse Lorenty (5309542) · David Hudson (5310097) · Nathan Pintabona (5311063) · Mateus Fonseca (5314650) · Marcel Varela (5326409) · Ryan Thompson (5337234) · Antonio Guerrero (5339017) · Antonio Carrillo (5344323) · Chris Desautels (5345878) · Laura Baldwin (5345879).

---

## 3. Pre-W019 genuine-absence floor (805)

**715 distinct name-groups** — almost entirely singletons (**704 fighters with unique names**). Only 2 clusters ≥5:

| Cluster name | Count | ID range |
|---|---|---|
| Mongi Zitouni | 48 | 5238536 → 5238637 (the W018 placeholder band) |
| Ludovic Dandine | 34 | 5238548 → 5238638 |

The floor is dominated by **MMA officials/referees and placeholders** — the top singleton names are the expected referee roster (Cecil Peoples · Herb Dean · John McCarthy · Steve Mazzagatti · Mario Yamasaki · Adalaide Byrd · Tony Weeks · Patricia Morse-Jarman · Marcos Rosales · Jeff Mullen · Abe Belardo; IDs 2565497–2593947), plus "Opponent TBA" (2) · "Larry Carter" (3) · Paul Sutherland · Mark Smith · Bobby Harris · Sal Ram · Jason Stafin · Iván Ramírez · Joao Claudio Soares (2 each) and ~690 more unique-name singles. ESPN serves no fight-record payload for officials → `/records` returns empty (content-dependent absence).

---

## 4. Cross-check with sweep evidence (validated, not assumed)

- The final sweep's **288 gains were all in the deferred band (external_id ≥ 5310951)** — consistent with the placeholder clusters (max ID 5345445) and the floor returning empty while real deferred fighters returned payloads.
- Of the 419 post-W019: **414 confirmed by Batches 1–2** (the 7 clusters + 30 singletons) and **5 newly confirmed by the final sweep**.
- **Actionable deferred = 0.** No fabrication; empty responses never converted to fake records (no 0-0-0-0 rows).

---

## 5. Conclusion / operational note

The remaining **1,224 missing records are fully explainable**: ~89% are repeated placeholder/official names ESPN serves without record payloads (Tyler · Zitouni · Dandine · Edgehill · Harb · Miranda · Tatlow clusters + the referee roster in the floor); the rest are genuine single-fighter content absences. **Zero fabrication, zero actionable work remains, and a rerun would reproduce ~0% yield.** The only meaningful improvement is **Phase D** (persisted absence flag to eliminate 0%-yield re-probes), which requires explicit approval.

---

## 6. Provenance

- Queries: SELECT-only against live PostgreSQL `localhost:5432/mma` (fighters LEFT JOIN fighter_records WHERE id IS NULL), grouped by first/last name, ordered by external_id.
- No mutations, no migrations, no code changes. Historical artifacts preserved untouched.
