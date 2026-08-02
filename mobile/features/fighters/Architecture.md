# Fighters Module — Architecture

## Layer Diagram

```
Navigation (7 screens)
     ↓
  Screens (compose components + hooks)
     ↓
  Hooks (compose repository + stores)
     ↓
  Repository (API → typed domain objects)
     ↓
  API (Axios HTTP calls)
```

## State Ownership

| Store | Owns |
|---|---|
| `fightersStore` | filter, sort, weightClass, search, active tab |
| `compareStore` | fighterA, fighterB for comparison |
| `favoritesStore` | favorite IDs set |
| TanStack Query | All server data (fighters, stats, history, etc.) |

## Cache TTLs

| Data | Stale |
|---|---|
| Fighter list | 10 min |
| Fighter detail | 10 min |
| Stats | 30 min |
| History | 30 min |
| Similar | 60 min |
| Predictions | 30 min |
| Favorites | 60s |
