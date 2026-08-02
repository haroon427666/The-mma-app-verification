# Events Module — Architecture

## Layers

```
Screen (renders UI, handles navigation)
  ↓
Hook (composes queries + stores + analytics)
  ↓
Repository (data access, transforms API responses)
  ↓
API (raw HTTP calls via Axios)
```

## Directory Map

| Layer | Directory | Responsibility |
|---|---|---|
| API | `api/` | Raw HTTP endpoints per domain |
| Repository | `repository/` | Type-safe data access, response normalization |
| Services | `services/` | Query keys, shared utilities |
| Socket | `socket/` | WebSocket for live fight updates |
| Store | `store/` | Zustand: filters, watchlist, reminders |
| Hooks | `hooks/` | TanStack Query composition |
| Mutations | `mutations/` | Optimistic updates for watchlist/reminders |
| Components | `components/` | One component = one file |
| Detail | `detail/` | Composed sections for EventDetailScreen |
| Images | `images/` | CachedImage, Avatar, Flag, Poster, Logo |
| Skeletons | `skeletons/` | Per-component loading states |
| Animations | `animations/` | CountdownFlip, LivePulse, Expand |
| Errors | `errors/` | Domain-specific error states |
| Theme | `theme/` | Event/fight color tokens |
| Accessibility | `accessibility/` | Screen reader labels |
| Analytics | `analytics/` | Interaction tracking |
| Offline | `offline/` | Mutation queue for offline |
| Navigation | `navigation/` | 6-screen typed stack |
| Screens | `screens/` | 6 full screens |
| Utils | `utils/` | Sorters, formatters, timezone helpers |
| Types | `types.ts` | Complete type definitions |

## Data Flow

1. User opens EventsScreen
2. `useEvents()` hook calls `eventsRepo.list()` 
3. Repository calls `eventsApi.list()` (Axios)
4. TanStack Query caches result with filter-dependent TTL
5. Zustand `eventsStore` tracks active filter, scroll position
6. User taps event → navigation to EventDetailScreen
7. `useEvent(id)` hook calls repository → parallel API requests
8. Detail sections (EventHero, FightCardSection, etc.) render
9. User taps Watchlist → `useWatchEvent` mutation → optimistic update
10. Analytics track every interaction
11. If offline → `eventsOfflineQueue` buffers mutations
12. WebSocket connects when viewing a live event (30s polling fallback)

## Cache Strategy

| Data | TTL | Polling |
|---|---|---|
| Live events | 30s | 30s interval |
| Upcoming events | 5 min | - |
| Past events | 24 hr | - |
| Fight card | 5 min | 30s when LIVE |
| Predictions | 30 min | - |
| Results | 24 hr | - |
| Watchlist | 5 min | - |
| Reminders | 60s | - |
