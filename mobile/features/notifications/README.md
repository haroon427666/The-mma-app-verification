# Notifications Feature

## API Endpoints
- `GET /v1/notifications?limit=50`
- `PATCH /v1/notifications/:id/read`
- `PATCH /v1/notifications/read-all`

## Cache Strategy
- 60s stale, optimistic updates on mark-read

## State Ownership
- `notificationStore`: filter (all/unread)
- Optimistic mutations: mark-read flips locally, rolls back on error
