# Events Module — Testing Guide

## Test Categories

### Unit tests
- `utils/fightSorter.test.ts` — card sorting by segment
- `utils/eventStatus.test.ts` — status detection
- `utils/formatter.test.ts` — date/venue formatting
- `utils/timezone.test.ts` — timezone conversion
- `store/*.test.ts` — Zustand store actions

### Component tests
- `components/EventCard.test.tsx`
- `components/FightRow.test.tsx`
- `components/Countdown.test.tsx`
- `components/WatchlistButton.test.tsx`

### Integration tests
- `hooks/useEvents.test.tsx` — query composition
- `hooks/useCountdown.test.tsx` — timer behavior
- `hooks/useWatchlist.test.tsx` — optimistic updates

### E2E tests (Detox)
- `events.e2e.ts` — full event browsing flow
- `fight.e2e.ts` — fight card interaction
- `watchlist.e2e.ts` — add/remove watchlist

## Running Tests
```bash
# Unit + component
npm test -- events/

# E2E
detox test -- configuration e2e/events
```
