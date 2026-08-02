# Fighters Module — Testing

## Unit tests
- `repository/*.test.ts` — Data layer
- `utils/*.test.ts` — Sorters and formatters
- `store/*.test.ts` — Zustand actions

## Component tests
- `FighterCard.test.tsx`
- `FighterHeader.test.tsx`
- `FighterStats.test.tsx`
- `SimilarityCard.test.tsx`

## Integration tests
- `useFighter.test.tsx` — Query composition
- `useFavoriteFighter.test.tsx` — Optimistic mutation

## E2E
- `fighter.e2e.ts` — Full profile flow
- `comparison.e2e.ts` — Compare two fighters

Run: `npm test -- features/fighters/`
