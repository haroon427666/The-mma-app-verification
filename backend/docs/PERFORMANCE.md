# PERFORMANCE.md — Benchmark Targets & Results

## API Performance Targets

| Endpoint | P50 | P95 | P99 | Notes |
|---|---|---|---|---|
| `GET /health` | <5ms | <10ms | <20ms | No DB/Redis required |
| `GET /api/v1/fighters` | <30ms | <75ms | <150ms | With Redis cache |
| `GET /api/v1/fighters/{id}` | <20ms | <50ms | <100ms | Single row + joins |
| `GET /api/v1/events/upcoming` | <10ms | <30ms | <60ms | Cached 5min |
| `GET /api/v1/rankings` | <10ms | <20ms | <40ms | Cached 10min |
| `GET /api/v1/search?q=islam` | <50ms | <100ms | <200ms | Full-text search |
| `POST /api/v1/auth/login` | <30ms | <60ms | <100ms | Argon2id verify |
| `POST /api/v1/auth/refresh` | <10ms | <20ms | <40ms | JWT only |

## Sync Performance Targets

| Metric | Target | Measurement |
|---|---|---|
| Full sync (all entities) | <180s | `python sync.py --full` |
| 2000 fighters | <60s | Fighter batch upsert |
| 500 events | <20s | Event batch upsert |
| Fighter upsert throughput | >100/sec | Per-batch measurement |
| Sync memory peak | <200MB | `tracemalloc` during sync |
| Duplicate rate | 0% | Unique constraint enforcement |
| Failed transaction rate | 0% | Rollback rate |

## Database Performance

| Metric | Target |
|---|---|
| Connection pool size | 10 |
| Max connections | 30 |
| Query timeout | 30s |
| Slow query threshold | 250ms |
| Index hit rate | >99% |
| Cache hit rate (shared buffers) | >95% |

## Redis Performance

| Metric | Target |
|---|---|
| Hit rate | >90% |
| Memory usage | <500MB |
| Eviction rate | <1% |
| Latency P99 | <1ms |

## HTTP Caching (ETag / Conditional GET)

Cached endpoints respond with `ETag` + `Cache-Control` and answer `If-None-Match`
requests with `304 Not Modified`. ETags are content hashes — any data or schema
change invalidates them automatically. List/detail endpoints additionally use
cache-aside (memory or Redis) so a hit skips the DB query entirely.

| Endpoint | Cache-aside TTL | ETag | Cache-Control |
|---|---|---|---|
| `GET /api/v1/events/{id}` | 300s | Yes | `public, max-age=300` |
| `GET /api/v1/events` | 300s | Yes | `public, max-age=300` |
| `GET /api/v1/events/upcoming` | 300s | Yes | `public, max-age=300` |
| `GET /api/v1/events/live` | 60s | Yes | `public, max-age=60` |
| `GET /api/v1/fighters/{id}` | 3600s | Yes | `public, max-age=3600` |
| `GET /api/v1/fighters/{id}/statistics` | 3600s | Yes | `public, max-age=3600` |
| `GET /api/v1/fighters/{id}/history` | 3600s | Yes | `public, max-age=3600` |
| `GET /api/v1/fighters` | 300s | Yes | `public, max-age=300` |
| `GET /api/v1/fights/{id}` | 300s | Yes | `public, max-age=300` |
| `GET /api/v1/rankings*` | 600s | Yes | `public, max-age=600` |
| `GET /api/v1/promotions` | 86400s | Yes | `public, max-age=3600` |
| `GET /api/v1/venues` | 86400s | Yes | `public, max-age=3600` |

Implementation: `src/api/etag.py` (ETag hashing + conditional response),
`src/api/cache.py` (cache-aside helper + key building), backends in
`src/middleware/cache.py` (memory / Redis, degrade-to-serve-through).

## Cache Invalidation (sync → API)

Every sync run busts the cache prefixes of the entities it wrote
(`src/sync/cache_invalidation.py`, wired via the engine's `after_sync` event):

- Fighter / statistic jobs → `mma:api:fighters*` (detail, statistics, history, list)
- Event / competition / broadcast jobs → `mma:api:events*` (+ `fights` detail)
- Ranking jobs → `mma:api:rankings*`
- Promotion / venue jobs → `mma:api:promotions*` / `mma:api:venues*`

Only `COMPLETED`/`PARTIAL` runs invalidate; failed runs keep previously cached
data (stale-but-consistent). Invalidation failures log and never fail the sync.

## Database Indexes

Backing the hot query paths — migration `003_phase8_performance`:

| Table | Indexed columns |
|---|---|
| events | promotion_id |
| competitions | event_id |
| competitors | competition_id, fighter_id |
| rankings | fighter_id, category_name |
| statistics | fighter_id, competitor_id |
| broadcasts | event_id |
| fighters | weight_class_name, nationality, full_name |

## Load Testing Results

| Scenario | Target RPS | Result | Notes |
|---|---|---|---|
| Fighters listing | 500 | — | Cache TTL 1 hour |
| Search burst | 200 | — | PostgreSQL full-text |
| Login storm | 100 | — | Argon2id 3 iterations |
| Live event traffic | 1000 | — | Rankings + events cached |
| Full sync during load | 1 sync / 500 RPS | — | Should not degrade API |
