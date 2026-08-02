/** README — Events module overview */

# Events Module

Complete, production-ready events feature for MMA Intelligence.

## Quick Start

```typescript
import { EventsStack } from '@/features/events';

// In your navigator:
<Stack.Screen name="Events" component={EventsStack} />
```

## Features

- **Live events** — 30s polling + WebSocket fallback
- **Upcoming/Past** — Infinite scroll, promotion filters
- **Event detail** — Countdown, venue, broadcast, full fight card
- **Fight card** — Sorted by segment, predictions inline
- **Live mode** — Auto-switches UI when event goes live
- **Watchlist** — Optimistic add/remove with rollback
- **Reminders** — 4 preset times, computed remind_at
- **Predictions** — Confidence, finish probability, key factors
- **Results** — Full results with bonuses
- **Statistics** — Event-level analytics

## Architecture

```
Screen → Hook → Repository → API
```

100+ symbols exported via barrel.
