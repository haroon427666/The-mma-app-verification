# Watchlist Feature

## API Endpoints
- `GET /v1/watchlist/events`
- `GET /v1/favorites/fighters`
- `DELETE /v1/favorites/fighters/:id`

## Cache Strategy
- 5 min stale, optimistic removal

## State Ownership
- `watchlistStore`: active tab (events | fighters)
