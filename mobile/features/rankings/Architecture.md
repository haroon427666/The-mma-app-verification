# Rankings Architecture

## Layer Diagram
```
Navigation (10 screens)
  ↓
Screens (P4P, Division, GOAT, Prospects, Movement, History, Champions)
  ↓
Hooks (useP4P, useDivisionRankings, useGOAT, etc.)
  ↓
Repository (rankingsRepo → 13 functions)
  ↓
API (rankingsApi → 13 endpoints)
```

## State Ownership
| Store | Responsibility |
|---|---|
| `rankingsStore` | View, division, sort, movement direction, pinned divisions |
| `rankingsMutations` | Favorited fighters set |
| `rankingsOffline` | Last sync time, staleness |
| TanStack Query | All server data |

## Intelligence Integration
Composite scores are computed by the `intelligence/` package:
- ELO rating (60%)
- Glicko rating (10%)
- Momentum (10%)
- Win Quality (10%)
- Strength of Schedule (5%)
- Championship weight (5%)
- Age curve adjustment
- Activity penalty
