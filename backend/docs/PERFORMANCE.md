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

## Load Testing Results

| Scenario | Target RPS | Result | Notes |
|---|---|---|---|
| Fighters listing | 500 | — | Cache TTL 1 hour |
| Search burst | 200 | — | PostgreSQL full-text |
| Login storm | 100 | — | Argon2id 3 iterations |
| Live event traffic | 1000 | — | Rankings + events cached |
| Full sync during load | 1 sync / 500 RPS | — | Should not degrade API |
