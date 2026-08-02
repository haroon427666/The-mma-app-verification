# Production Benchmark — Phase 5.5

**Expected measurements for a full ESPN sync.**

---

## Full Sync — Target Metrics

| Metric | Target | Target Range | Verification |
|---|---|---|---|
| Total runtime | 180s | 120-300s | Clock from `sync.py --full` start to finish |
| API requests made | 3,500 | 2,500-5,000 | Sum of `api_calls` across all `sync_jobs` |
| Retries | 15 | 5-50 | Transient HTTP errors recovered via retry |
| Permanent failures | 0 | 0-5 | If >0, investigate dead letters |
| Rate limit hits | 0 | 0-3 | 429 responses registered |
| Circuit breaker trips | 0 | 0-1 | Should not trip under normal operation |
| Memory peak | 200MB | 100-500MB | Monitor via `tracemalloc` during sync |

## Entity Counts — Expected

| Entity | Expected Count | Notes |
|---|---|---|
| Promotions | 1 (UFC) | Primary focus |
| Weight Classes | 12 | 8 men's + 4 women's |
| Fighters | 1,809 | All-time UFC roster |
| Active Fighters | ~800 | `is_active = true` |
| Events (2026) | ~40 | Current year |
| Competitions | ~520 | ~13 fights/event × 40 events |
| Ranking Entries | ~360 | 24 categories × ~15 ranks |
| Statistics (fighter) | ~1,000 | Only fighters with career stats |
| Broadcasts | ~120 | ~3 networks/event |
| Venues | ~30 | Unique venues in 2026 |

## Query Response Times — Targets

| Query | Expected (ms) | Index Strategy |
|---|---|---|
| `GET /fighters?weight_class=lightweight` | <50ms | Index on `weight_class_name` |
| `GET /fighters?active=true` | <50ms | Index on `is_active` |
| `GET /events?status=SCHEDULED` | <50ms | Index on `status` |
| `GET /events?date_utc >= '2026-01-01'` | <80ms | Index on `date_utc` |
| `GET /rankings?category=flyweight` | <50ms | Index on `promotion_id + category_name` |
| Fighter detail (with joins) | <100ms | FK indices on all relations |
| Event detail (with competitions) | <150ms | FK on `competitions.event_id` |

## Index Strategy

```sql
-- Primary query patterns
CREATE INDEX ix_events_date ON events(date_utc);
CREATE INDEX ix_events_status ON events(status);
CREATE INDEX ix_fighters_is_active ON fighters(is_active);
CREATE INDEX ix_rankings_category ON rankings(promotion_id, category_name);
CREATE INDEX ix_sync_jobs_run ON sync_jobs(sync_run_id);
CREATE INDEX ix_dead_letters_replayed ON dead_letters(replayed);
CREATE INDEX ix_external_ids_lookup ON external_ids(entity_type, provider, external_id);

-- All enforced by 001_initial_schema.py migration
```

## Sync Throughput — Per Entity

| Entity | Records/Sec | API Calls | Dominant Factor |
|---|---|---|---|
| Promotions | 1 | 1 | Single endpoint |
| Weight Classes | 12 | 0 | Extracted inline |
| Fighters | 8/s | ~1,820 | $ref resolution: 1 list call + 1,809 individual resolves |
| Events | 4/s | ~42 | $ref resolution: 1 list + ~40 individual resolves |
| Competitions | — | 0 | Embedded in events response |
| Rankings | 24/s | 25 | 1 list + 24 category resolves |
| Broadcasts | — | ~120 | Resolved from competition $refs |
| Statistics | 3/s | ~800 | 1 per fighter with stats |
| Records | 3/s | ~800 | 1 per fighter |

## Bottleneck Analysis

| Bottleneck | Impact | Mitigation |
|---|---|---|
| $ref resolution | Each fighter requires 1 extra API call | `RefResolver` caches within run |
| Rate limiter (8 req/s) | Cap on throughput | TokenBucket with burst=16 |
| Statistics fetching | 800 extra calls for career stats | Only fetch for active fighters |
| No pagination parallelism | Sequential page fetches | Acceptable for 8 req/s rate |

## How to Run

```bash
# Full benchmark
time python sync.py --full 2>&1 | tee sync_benchmark_$(date +%Y%m%d).log

# Extract metrics
grep "Sync completed" sync_benchmark_*.log
grep -c "ERROR" sync_benchmark_*.log
grep "records_inserted\|records_updated\|api_calls" sync_benchmark_*.log

# Database verification
psql $DATABASE_URL -c "
SELECT 'fighters', count(*) FROM fighters UNION ALL
SELECT 'events', count(*) FROM events UNION ALL
SELECT 'competitions', count(*) FROM competitions UNION ALL
SELECT 'rankings', count(*) FROM rankings;
"
```
