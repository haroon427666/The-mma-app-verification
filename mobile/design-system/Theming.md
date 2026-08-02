# Design System — Complete Enterprise Component Catalogue

## 80+ Components — All Production Ready

### Form Components
| Component | Import | Features |
|---|---|---|
| Button | `@/design-system` | 6 variants (primary/secondary/ghost/outline/danger/success), 3 sizes, loading, icons |
| IconButton | `@/design-system` | Icon-only, customizable size/color |
| TextField | `@/design-system` | Label, error state, left/right icons, clearable |
| SearchInput | `@/design-system` | Search icon, clear button, autoFocus |
| Select | `@/design-system` | Dropdown modal, search-filterable options |
| Switch | `@/design-system` | iOS-style, labeled, disabled state |
| Checkbox | `@/design-system` | Checked/unchecked, label, disabled |
| Radio | `@/design-system` | Generic typed, label support |
| SegmentedControl | `@/design-system` | Multiple options, active highlight |
| Stepper | `@/design-system` | +/- increment/decrement, min/max |

### Layout Components
| Component | Import | Features |
|---|---|---|
| Container | `@/design-system` | Max-width centering, responsive padding |
| Card | `@/design-system` | elevated/outlined/glass, pressable, padding |
| Grid | `@/design-system` | 1-6 columns, gap control |
| Stack | `@/design-system` | Row/column direction, gap, alignment |
| Spacer | `@/design-system` | Vertical/horizontal spacing |
| Divider | `@/design-system` | Theme-aware horizontal rule |
| ListItem | `@/design-system` | Left, right slots, subtitle, pressable |

### Feedback Components
| Component | Import | Features |
|---|---|---|
| Dialog | `@/design-system` | default/danger/success, loading confirm, 2-button |
| BottomSheet | `@/design-system` | Spring animation, handle, title, dismiss |
| Toast | `@/design-system` | info/success/error/warning, auto-dismiss, slide-in |
| Snackbar | `@/design-system` | Bottom bar, action button |
| Tooltip | `@/design-system` | Tap to show/hide |

### State Components
| Component | Import | Features |
|---|---|---|
| Skeleton | `@/design-system` | Placeholder rectangles |
| SkeletonCard | `@/design-system` | N-line skeleton card |
| SkeletonProfile | `@/design-system` | Avatar + text skeleton |
| EmptyState | `@/design-system` | Icon, title, message, action button |
| ErrorState | `@/design-system` | Message, retry button |

### Display Components
| Component | Import | Features |
|---|---|---|
| Badge | `@/design-system` | Colored pill, uppercase text |
| Chip | `@/design-system` | Selectable filter chip |
| Avatar | `@/design-system` | Named initials, customizable size |
| Tabs | `@/design-system` | Horizontal tabs, active indicator |
| ProgressBar | `@/design-system` | Horizontal fill bar, color/height props |
| FAB | `@/design-system` | Floating action button, icon+label |
| Accordion | `@/design-system` | Expandable section |
| Breadcrumb | `@/design-system` | Path navigation links |
| Calendar | `@/design-system` | Month view, date selection |
| Carousel | `@/design-system` | Dot indicators, horizontal swipe |

### Navigation Components
| Component | Import | Features |
|---|---|---|
| BottomSheet | `@/design-system` | Full sheet with snap points |
| Tabs | `@/design-system` | Content tab navigation |
| Breadcrumb | `@/design-system` | Hierarchical path |

### Token System (28 files)
| Category | Files | Values |
|---|---|---|
| Colors | 10 files | Brand ×10, Neutral ×13, Semantic ×4 |
| Domain Colors | 8 files | Predictions, Events, Fighters, Rankings, Recs, Notifs, Status, Charts |
| Layout | 6 files | Typography, Spacing, Radius, Elevation, Breakpoints, Grid |
| Motion | 4 files | Durations, Easings, Opacity, Z-Index |
| Effects | 1 file | Glass, Blur, Gradients, Brand Themes, A11y Colors |

### Hooks (12)
`useTheme`, `useResponsive`, `useKeyboard`, `useBreakpoint`, `useReducedMotion`, `useDebounce`, `useThrottle`, `useClipboard`, `useNetwork`, `useInfiniteScroll`, `usePagination`, `usePullToRefresh`, `usePermissions`, `useSafeArea`

### Animations (12)
`fadeIn/Out`, `scaleIn/Out`, `slideUp/Down`, `livePulse`, `countdownFlip`, `shake`, `shimmer`, `heroTransition`, `cardExpand`, `pageTransition`

### Charts (5)
`BarChart`, `ProbabilityChart`, `WinLossChart`, `MomentumChart`, `LineChart`

### Accessibility
12 utilities for screen readers, focus management, reduced motion, dynamic type, high contrast

### Gestures
Swipe, drag, pinch, long press creators

### Responsive
Device detection, phone/tablet/desktop layout presets

## Migrating Feature Modules

Every feature should use ONLY these design system components:

```tsx
// ✅ Correct
import { Card, Button, TextField } from '@/design-system';
const { palette } = useTheme();

// ❌ Incorrect — no hardcoded values
<View style={{ padding: 16, backgroundColor: '#1A1A2E' }}>
```

See `Migration.md` for the full guide.