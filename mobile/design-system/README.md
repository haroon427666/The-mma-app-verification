# Design System — MMA Intelligence Mobile

A production-grade design system built for the MMA Intelligence mobile application. Designed with the quality standards of Linear, Notion Mobile, Arc Search, and Apple Fitness.

## Architecture

```
design-system/
├── tokens/           → Design tokens (single source of truth)
├── theme/            → Theme context, provider, and builder
├── components/       → 40+ reusable UI components
├── stories/          → Storybook component stories
├── playground/       → Interactive component playground
└── __tests__/        → Unit and snapshot tests
```

## Quick Start

```tsx
import { ThemeProvider, Button, Card, TextField } from '@/design-system';

function App() {
  return (
    <ThemeProvider initialMode="dark">
      <Card>
        <Button variant="primary" label="Get Started" onPress={() => {}} />
      </Card>
    </ThemeProvider>
  );
}
```

## Theme Modes

- **Light** — Clean white interface
- **Dark** — Deep navy/gray interface (default)
- **AMOLED** — True black for OLED displays
- **System** — Follows device preference

## Component Categories

| Category | Components |
|---|---|
| **Buttons** | Primary, Secondary, Ghost, Outline, Danger, Success, Loading, Icon, FAB |
| **Cards** | Elevated, Glass, Outlined, Metric, Stats |
| **Inputs** | TextField, SearchField |
| **Feedback** | Dialog, BottomSheet, Toast |
| **Display** | Badge, Chip, Avatar, Divider, Tabs, ListItem |
| **States** | Skeleton, EmptyState, ErrorState |
| **Progress** | ProgressBar, ProgressRing |
| **Media** | CachedImage |
| **Animations** | fadeIn, scaleIn, slideUp |
| **Hooks** | useTheme, useResponsive |

## Design Principles

1. **Token-first** — Every value comes from tokens, never hardcoded
2. **Theme-aware** — Every component adapts to light/dark/amoled
3. **Accessible** — Screen reader labels on every interactive element
4. **Performant** — No unnecessary re-renders, memoized where needed
5. **Composable** — Components combine cleanly without conflicts
