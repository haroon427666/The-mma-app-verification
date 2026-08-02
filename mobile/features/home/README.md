# Home Feature

## Structure
```
home/
  api/         endpoints.ts, queries.ts
  hooks/       useHome.ts (composes api + store + connectivity)
  store/       homeStore.ts (Zustand: dismissedCards, scrollPosition)
  types/       HomeSection, HomeState
  screens/     HomeScreen.tsx
  constants.ts SECTION order, refresh intervals
  index.ts     Barrel export
```

## API Endpoints
- `GET /v1/home` (aggregated feed)
- `GET /v1/events?status=LIVE&limit=5`
- `GET /v1/events/upcoming?limit=5`
- `GET /v1/fighters/trending?limit=8`
- `GET /v1/recommendations/fighters`
- `GET /v1/fights?is_title=true&status=SCHEDULED`
- `GET /v1/predictions/highlights`

## Cache Strategy
- Home feed: 2 min stale, background refresh
- Live events: 30s stale, 30s polling interval
- Trending: 5 min stale
- Predictions: 10 min stale

## State Ownership
- `homeStore`: UI state only (dismissed cards, scroll position)
- TanStack Query: server state (feed data, events, fighters)
- `connectivityStore` (global): network status
