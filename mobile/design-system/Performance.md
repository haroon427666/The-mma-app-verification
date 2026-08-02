# Design System — Performance Guide

## Tree Shaking
All imports are tree-shakeable:
```tsx
import { Button } from '@/design-system'; // Tree-shaken: only Button loaded
import { buildTheme } from '@/design-system/theme/ThemeBuilder'; // Deep import
```

## Memoization
All heavy components should be wrapped:
```tsx
const MyComponent = React.memo(({ data }) => <Card>...</Card>);
```

## Image Caching
Use `<CachedImage>` which implements:
- In-memory cache
- Disk cache
- Progressive loading
- Error fallbacks

## Skeleton Priority
Always show skeletons BEFORE data loads:
```tsx
if (isLoading) return <SkeletonCard lines={5} />;
if (error) return <ErrorState onRetry={refetch} />;
if (!data?.length) return <EmptyState message="No results" />;
```

## Animation Performance
All animations use `useNativeDriver: true`.
Spring animations use the design system's optimized spring config.

## Bundle Size
Import only what you need. The modular architecture ensures:
- No circular dependencies
- No side-effect imports
- Clean module boundaries