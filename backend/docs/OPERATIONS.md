# OPERATIONS.md — MMA Backend Operations Guide

## Deployment

### Requirements
- **Python** 3.12+
- **PostgreSQL** 15+ (production)
- **Redis** 7+ (production, optional for dev)
- **4 GB RAM** minimum, 8 GB recommended

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | `postgresql://user:pass@host:5432/mma` |
| `REDIS_URL` | Prod | — | `redis://host:6379` |
| `JWT_SECRET` | Yes | — | Generate: `python -c 'import secrets; print(secrets.token_hex(32))'` |
| `TZ` | No | UTC | IANA timezone (e.g., `America/New_York`) |
| `ENVIRONMENT` | No | development | `development` / `staging` / `production` |
| `DISCORD_WEBHOOK_URL` | No | — | Discord webhook for alerts |
| `ALERT_EMAIL` | No | — | Email for critical alerts |
| `PORT` | No | 8000 | HTTP server port |

### Starting the Service

```bash
# Development
uvicorn src.api.main:app --reload --port 8000

# Production (with Gunicorn + Uvicorn workers)
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# With Docker
docker build -t mma-backend .
docker run -p 8000:8000 --env-file .env mma-backend
```

### Health Checks

```bash
# Kubernetes liveness probe
GET /health           → {"status": "healthy", "uptime_seconds": 12345}

# Kubernetes readiness probe
GET /health/ready     → {"status": "healthy", "checks": {...}}

# Full health report
GET /health/database  → {"status": "healthy"}
GET /health/redis     → {"status": "healthy"}
GET /health/providers → {"status": "healthy", "checks": {"espn": {...}, ...}}
```

### Metrics

Prometheus metrics at `GET /api/scheduler/metrics`.

Grafana dashboards in `grafana/` directory.

### Logs

All logs are structured JSON. Use `jq` to query:

```bash
# Filter errors
tail -f app.log | jq 'select(.level == "ERROR")'

# Slow requests (> 500ms)
tail -f app.log | jq 'select(.duration_ms > 500)'

# Provider failures
tail -f app.log | jq 'select(.provider == "espn" and .level == "ERROR")'
```

### Sync Management

```bash
# Full sync
curl -X POST http://localhost:8000/api/sync/full \
  -H "Authorization: Bearer $TOKEN"

# Entity-specific sync
curl -X POST http://localhost:8000/api/sync/fighter \
  -H "Authorization: Bearer $TOKEN"

# View sync status
curl http://localhost:8000/api/scheduler/status \
  -H "Authorization: Bearer $TOKEN"
```

## Maintenance

### Daily Checks
- [ ] All providers healthy (`GET /health/providers`)
- [ ] Last sync completed successfully (`GET /api/scheduler/status`)
- [ ] No dead letters accumulating
- [ ] Disk usage < 80%
- [ ] No alerts fired in last 24 hours

### Weekly Checks
- [ ] Database vacuum ran successfully
- [ ] Payload archive within size limits
- [ ] Checkpoint table not bloated
- [ ] Index usage statistics healthy

### Monthly Checks
- [ ] Review and rotate API keys
- [ ] Review alert thresholds
- [ ] Load test at expected peak traffic + 20%
- [ ] Review and prune audit logs
