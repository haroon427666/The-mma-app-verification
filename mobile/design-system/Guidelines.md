# Design System — Usage Guidelines

## Always

- Import components from `@/design-system`
- Use tokens via `useTheme()` or directly from `@/design-system/tokens`
- Pass `accessibilityLabel` to interactive elements
- Use variants instead of custom styles
- Handle loading, empty, and error states

## Never

- Hardcode colors, spacing, or typography values
- Create one-off components that duplicate design system functionality
- Use inline styles for layout (use spacing tokens)
- Ship a component without loading/error/empty state handling

## Import Paths

```tsx
// Components
import { Button, Card, TextField, Dialog, BottomSheet } from '@/design-system';

// Tokens
import { colors, typography, spacing, radius } from '@/design-system/tokens';

// Theme
import { ThemeProvider, useTheme, buildTheme } from '@/design-system/theme';

// States
import { Skeleton, EmptyState, ErrorState } from '@/design-system';
```

## Component Patterns

### Button variants
```tsx
<Button variant="primary" size="md" label="Save" onPress={handleSave} />
<Button variant="danger" label="Delete" loading={isDeleting} />
<Button variant="outline" label="Cancel" />
```

### Cards
```tsx
<Card variant="elevated" onPress={handlePress}>
  <Text>Content</Text>
</Card>
<MetricCard label="Win Rate" value="73%" trend="up" />
```

### Inputs
```tsx
<TextField label="Email" value={email} onChangeText={setEmail} error={error} />
<SearchField value={query} onChangeText={setQuery} />
```

### Dialogs
```tsx
<Dialog visible={show} title="Delete?" message="This is permanent."
  variant="danger" confirmLabel="Delete" onConfirm={handleDelete} onDismiss={() => setShow(false)} />
```

### States
```tsx
// Loading
<SkeletonCard lines={3} />

// Empty
<EmptyState icon="🔍" message="No results found" actionLabel="Clear filters" onAction={clearFilters} />

// Error
<ErrorState message="Failed to load" onRetry={refetch} />
```
