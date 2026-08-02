# Design System — Changelog

## Phase 14.1 — Enterprise Modular Refactor

### BREAKING CHANGES from Phase 14.0

Removed monolithic files:
- `components/index.ts` (12KB → split into 15 component folders)
- `components/supporting.tsx` (16KB → split into 10 component folders)
- `tokens/index.ts` (4KB → split into 20 individual token files)
- `theme/ThemeSystem.tsx` (3KB → split into 7 theme files)
- `stories-and-tests.ts` (9KB → split into 2 directories)

### New Architecture

- **20 token files** — one per token category
- **7 theme files** — one per theme concern
- **25+ component folders** — each with types, styles, utils, component, stories, tests, and index
- **4 hook files** — one per hook
- **5 utility functions**
- **8 animation functions**
- **3 chart components**
- **3 image components**
- **4 gesture creators**
- **Responsive layout utilities**
- **Accessibility labels + role factories**

### Migration from Phase 14.0

All import paths remain the same via the barrel `index.ts`. No feature code changes required.

```tsx
// Before (still works)
import { Button, Card, TextField } from '@/design-system';

// Now also possible (tree-shaking)
import { Button } from '@/design-system/components/Button';
import { buildTheme } from '@/design-system/theme/ThemeBuilder';
```