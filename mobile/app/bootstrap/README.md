# Bootstrap Platform

Application startup pipeline: env → storage → theme/locale → query client → auth → notifications → remote config → ready.

## Exports

- `AppBootstrap` — root bootstrap component
- `AppInitializer` — imperative initializer
- `StartupPipeline` — staged startup orchestrator
- `useBootstrapState` — Zustand bootstrap store (stage, progress, isReady, error)
- `useBootstrap`, `useStartup`, `useStartupStatus`, `useInitialization`, `useDependencies` — hooks
- `ProviderComposer` — nested provider composition
- `ErrorBoundary` — top-level error capture
- `DependencyContainer` / `container` / `DI_TOKENS` — service locator
- `createStartupTasks` — predefined startup task list
- `getBootstrapConfig` — runtime config accessor
- `bootstrapLogger` / `bootstrapMetrics` / `bootstrapEvents` — observability

## Stages

`idle → env → storage → theme_locale → query_client → auth → notifications → remote_config → ready` (or `failed`).
