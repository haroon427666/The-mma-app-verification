# Design System — Architecture

## Token System

All visual values originate from `tokens/index.ts`:
- `colors` — Brand, semantic, neutral, surface, text palettes
- `typography` — 9 text styles (display → overline)
- `spacing` — 4px grid (xs=4, sm=8, md=16, lg=24, xl=32, xxl=48, xxxl=64)
- `radius` — xs=4, sm=8, md=12, lg=16, xl=24, full=9999
- `elevation` — 6 shadow levels
- `easing` — Spring and cubic-bezier curves
- `zIndex` — Layering system (0-700)

## Theme Engine

`theme/ThemeSystem.tsx`:
1. `buildTheme(mode, systemIsDark)` — Pure function, no side effects
2. `ThemeProvider` — Context provider with `useMemo` for performance
3. `useTheme()` — Hook returning `{ theme, palette, tokens, mode, setMode }`

Every component calls `useTheme()` to access the current palette.

## Component Rules

1. No component imports theme tokens directly — always via `useTheme()`
2. Every interactive element has `accessibilityRole` and `accessibilityLabel`
3. Variants controlled via props, not separate components
4. Loading/disabled states built into every actionable component
5. Styles defined inline or via StyleSheet at module level

## Performance

- Theme values memoized via `useMemo`
- Component callbacks wrapped in `useCallback`
- All animations use `useNativeDriver: true`
- No inline arrow functions in render methods
