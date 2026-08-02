# API Versioning Strategy

**Last Updated:** 2026-08-01 | **Current Version:** v1

---

## Versioning Scheme

**URL-prefix versioning:** `/api/v1/`, `/api/v2/`, etc.

Chosen over header-based or query-param versioning because:
- Visible in logs, curl commands, browser dev tools
- No ambiguity about which version a client is using
- Works with all HTTP clients and proxies
- Clean REST semantics

## Current Status

| Version | Status | Endpoints | Notes |
|---------|--------|-----------|-------|
| `v1` | **Active** | 35 | Primary consumer API. All features target v1. |
| `v2` | **Future** | 0 | Reserved for breaking changes only. |

## When to Create v2

**Breaking changes that warrant v2:**
- Renaming response fields visible to clients
- Changing pagination format (e.g., offset → cursor)
- Removing or restructuring major endpoints
- Changing auth token format
- Adding required query parameters to existing endpoints

**Changes that do NOT warrant v2:**
- Adding new optional fields to responses
- Adding new endpoints
- Bug fixes
- Performance improvements
- Adding optional query parameters

## Deprecation Policy

1. **Announce:** Deprecated endpoints return `Deprecation: true` header + `Sunset: <date>` for 6 months before removal
2. **Monitor:** Track usage of deprecated endpoints via analytics
3. **Remove:** After 6 months, deprecated endpoint returns `410 Gone`

### V1 Deprecation Cadence

| Endpoint | Status | Sunset | Replacement |
|----------|--------|--------|-------------|
| None currently deprecated | — | — | — |

## Backward Compatibility

**v1 guarantees until v2 is released:**
- No existing response field will be removed
- No existing response field will change type
- Optional fields may be added at any time
- New endpoints may be added at any time
- Sort order of array fields is guaranteed for the first 100 items

## Migration Path v1 → v2

When v2 is created:
1. All v1 endpoints remain functional for 12 months
2. Both v1 and v2 served simultaneously under different prefixes
3. Clients migrate at their own pace
4. After 12-month sunset, v1 returns `410 Gone` with upgrade link

## Implementation

```python
# src/api/v1/ — current active version
from src.api.v1 import routers as v1_routers
for router in v1_routers:
    app.include_router(router, prefix="/api")

# src/api/v2/ — future (reserved directory)
# from src.api.v2 import routers as v2_routers
# for router in v2_routers:
#     app.include_router(router, prefix="/api")
```

## DTO Versioning

Schemas live in `src/schemas/` — currently shared across v1.
When v2 is created, duplicate schemas into `src/schemas/v2/` to allow independent evolution.

## WebSocket Version Compatibility

WebSocket connections use the same version prefix path.
No WebSocket versioning needed until breaking message format changes.
