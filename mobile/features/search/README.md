# Search Feature

## API Endpoints
- `GET /v1/search?q=`

## Cache Strategy
- 1 min stale, only queries when ≥ 2 chars

## State Ownership
- `searchStore`: current query, recent searches (10), search active state
