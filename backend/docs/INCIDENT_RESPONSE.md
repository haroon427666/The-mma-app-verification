# INCIDENT_RESPONSE.md — Incident Management

## Severity Levels

| Level | Definition | Response SLA | Notification |
|---|---|---|---|
| **P0 — Critical** | Service unavailable. 0% of users can access. | 15 min | Discord + Email + Phone |
| **P1 — High** | Major feature broken. > 50% users affected. | 30 min | Discord + Email |
| **P2 — Medium** | Minor feature broken. < 50% users affected. | 2 hours | Discord |
| **P3 — Low** | Cosmetic issue. Workaround available. | Next business day | Log only |

## Incident Lifecycle

```
[Detect] → [Acknowledge] → [Investigate] → [Mitigate] → [Resolve] → [Postmortem]
```

### 1. Detect
- Alert fires (Discord, email, log)
- User report
- Monitoring dashboard shows anomaly

### 2. Acknowledge
- Respond in alert channel with "Acknowledged — investigating"
- Assign incident commander
- Start incident timer

### 3. Investigate
- Check logs: `jq 'select(.level == "ERROR")' app.log | tail -50`
- Check health: `GET /health/providers`, `GET /health/database`
- Check metrics: Grafana dashboard for anomaly
- Reproduce if possible

### 4. Mitigate
- Apply fix or workaround
- Document what was changed
- Communicate status to stakeholders

### 5. Resolve
- Confirm issue is resolved via health checks
- Notify stakeholders
- Stop incident timer

### 6. Postmortem
Within 48 hours:
- What happened? (timeline)
- Root cause
- What went well?
- What went wrong?
- Action items (with owners + deadlines)

## Emergency Contacts

| Role | Name | Method |
|---|---|---|
| Backend Lead | — | Discord / Email |
| DevOps | — | Discord / Email |
| DBA | — | Discord / Email |

## Recovery Commands

```bash
# Restart backend
sudo systemctl restart mma-backend

# Check database
psql $DATABASE_URL -c "SELECT 1"

# Check Redis
redis-cli -h $REDIS_HOST ping

# View recent errors
tail -100 /var/log/mma-backend/app.log | jq 'select(.level == "ERROR")'

# Check sync status
curl -s http://localhost:8000/api/scheduler/status -H "Authorization: Bearer $TOKEN" | jq .
```
