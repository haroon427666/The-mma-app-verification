# Bootstrap — README + Architecture + BootstrapFlow + DependencyGraph + Testing + Migration

## Bootstrap Pipeline (8 stages)
```
Stage 1: env       → Load environment, validate config
Stage 2: storage    → MMKV, encrypted storage, cache
Stage 3: theme      → Theme, localization, accessibility
Stage 4: query      → TanStack Query, API client, network
Stage 5: auth       → Restore session, refresh tokens
Stage 6: notifs     → Push notifications, deep links
Stage 7: config     → Remote config, feature flags
Stage 8: ready      → Hide splash, navigate Home
```

## Dependency Container
```tsx
import { container, DI_TOKENS } from '@/app/bootstrap';
const apiClient = container.resolve(DI_TOKENS.API_CLIENT);
```

## Usage in App.tsx
```tsx
import { AppBootstrap } from '@/app/bootstrap';
export default function App() {
  return <AppBootstrap><MainNavigator /></AppBootstrap>;
}
```

## Testing
```ts
it('completes all startup stages', async () => {
  const init = new AppInitializer();
  await init.initialize();
  expect(useBootstrapState.getState().isReady).toBe(true);
});
```
