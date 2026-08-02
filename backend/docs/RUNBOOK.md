# RUNBOOK.md — Common Incident Responses

## Incident: Provider Down (ESPN/TSDB/Octagon)

**Symptoms:** Alert "provider_down" fires. Sync jobs fail with connection errors.

**Response:**
1. Check provider status: `GET /health/providers`
2. Check provider's public status page (e.g., ESPN API status)
3. If provider is down:
   - No action needed — sync will resume when provider recovers
   - Health monitor tracks recovery automatically
4. If provider is up but errors persist:
   - Check rate limit: `ProviderMetrics.rate_limit_hits`
   - Verify API keys / IP whitelisting
   - Check network connectivity: `curl https://sports.core.api.espn.com/v2/sports/mma/leagues/ufc`

**Recovery time:** Automatic within 15 minutes of provider recovery.

---

## Incident: Database Unavailable

**Symptoms:** `/health/ready` returns `FAILED`. All API requests return 500.

**Response:**
1. Check database connectivity: `psql $DATABASE_URL -c "SELECT 1"`
2. Check connection pool: `SELECT count(*) FROM pg_stat_activity`
3. Check for long-running queries: `SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state != 'idle' ORDER BY duration DESC`
4. If connections exhausted: Restart backend workers
5. If database is down: Contact DBA / cloud provider

**Recovery time:** Immediate after database is reachable (reconnection is automatic).

---

## Incident: Sync Job Stuck or Failing

**Symptoms:** Consecutive failures > 3. `GET /api/scheduler/status` shows unhealthy jobs.

**Response:**
1. Check which job is stuck: `GET /api/scheduler/jobs`
2. Check latest error: `GET /api/scheduler/status` → `jobs.{name}.status`
3. Cancel stuck job: `POST /api/scheduler/sync/cancel/{job_name}`
4. Retry manually: `POST /api/scheduler/sync/retry/{job_name}`
5. If retry fails, run `python verify_espn.py` to check ESPN API changes
6. Check dead letters: `SELECT * FROM dead_letters WHERE replayed = false ORDER BY created_at DESC LIMIT 20`

**Recovery time:** Manual intervention (5-15 minutes).

---

## Incident: Token Reuse Attack Detected

**Symptoms:** Log shows `TOKEN REUSE ATTACK`. All user sessions revoked.

**Response:**
1. This is an automatic security response — no immediate action needed
2. Investigate source IP from audit logs
3. Check if the user's credentials were compromised
4. Contact the affected user to reset their password
5. If widespread: consider invalidating all refresh tokens

**Recovery time:** Automatic (sessions already revoked). User impact: forced re-login.

---

## Incident: High API Latency

**Symptoms:** Alert "high_latency" fires. P95 > 1 second.

**Response:**
1. Check database query performance: `SELECT query, calls, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10`
2. Check Redis hit rate: Cache stats from `/api/scheduler/metrics`
3. Check concurrent request count
4. If DB is the bottleneck:
   - Run `ANALYZE` on hot tables
   - Check for missing indexes
   - Consider read replica for search-heavy endpoints
5. If Redis is the bottleneck:
   - Check memory usage
   - Increase cache TTL for rankings/events

**Recovery time:** 15-60 minutes depending on root cause.

---

## Incident: Login Storm / Brute Force

**Symptoms:** Alert "login_storm" fires. > 20 failed logins in 5 minutes.

**Response:**
1. The brute-force middleware automatically locks out offending IPs for 15 minutes
2. Check affected IPs: search logs for "Account locked"
3. If distributed attack (multiple IPs): consider enabling Cloudflare / WAF
4. No manual intervention needed for individual lockouts

**Recovery time:** Automatic (15-minute lockout per IP).
