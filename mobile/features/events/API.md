# Events Module — API Reference

## Endpoints

### Events
| Method | Path | Params | Returns |
|---|---|---|---|
| GET | `/v1/events` | status, promotion, page, limit | `ExtendedEvent[]` |
| GET | `/v1/events/:id` | | `ExtendedEvent` |
| GET | `/v1/events/live` | | `ExtendedEvent[]` |
| GET | `/v1/events/upcoming` | limit | `ExtendedEvent[]` |
| GET | `/v1/events/past` | page, limit | `ExtendedEvent[]` |

### Fights
| Method | Path | Returns |
|---|---|---|
| GET | `/v1/events/:id/fights` | `FightCardEntry[]` |
| GET | `/v1/events/:id/results` | `FightResult[]` |
| GET | `/v1/events/:id/statistics` | `EventStatistics` |

### Predictions
| Method | Path | Returns |
|---|---|---|
| GET | `/v1/predictions/event/:id` | `Record<string, FightPrediction>` |
| GET | `/v1/predictions/fight/:id` | `FightPrediction` |

### Watchlist
| Method | Path |
|---|---|
| GET | `/v1/watchlist/events` |
| POST | `/v1/watchlist/events/:id` |
| DELETE | `/v1/watchlist/events/:id` |

### Reminders
| Method | Path |
|---|---|
| GET | `/v1/reminders` |
| POST | `/v1/reminders` ({ event_id, remind_at, type }) |
| DELETE | `/v1/reminders/:id` |

## Error Codes
- 404: Event not found → `EventNotFound`
- 503: Prediction service unavailable → `PredictionUnavailable`
- Network failure → `NetworkError`
