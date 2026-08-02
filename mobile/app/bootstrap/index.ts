/** Bootstrap — barrel export */
export { AppBootstrap } from './AppBootstrap';
export { AppInitializer } from './AppInitializer';
export { StartupPipeline } from './StartupPipeline';
export { createStartupTasks } from './StartupTasks';
export { SplashController, splashController } from './SplashController';
export { ProviderComposer } from './ProviderComposer';
export { ErrorBoundary } from './ErrorBoundary';
export { DependencyContainer, container, DI_TOKENS } from './DependencyContainer';
export { BootstrapContext } from './BootstrapContext';
export { BootstrapLogger, bootstrapLogger } from './BootstrapLogger';
export { BootstrapMetricsCollector, bootstrapMetrics } from './BootstrapMetrics';
export { bootstrapEvents } from './BootstrapEvents';
export { getBootstrapConfig } from './BootstrapConfig';
export { useBootstrapState } from './BootstrapState';
export { useBootstrap, useStartup, useStartupStatus, useInitialization, useDependencies } from './BootstrapHooks';
export { formatStartupTime, isStageCritical, shouldRetryStartup, logBootstrapEvent } from './BootstrapUtils';
export { BOOTSTRAP_CONSTANTS } from './BootstrapConstants';
export { bootstrapErrors } from './BootstrapErrors';
export type { StartupStage, BootstrapState, BootstrapConfig, StartupTask, BootstrapEvent, BootstrapMetrics } from './BootstrapTypes';
export { BootstrapError } from './BootstrapTypes';

// Documentation
export { default as BootstrapDocs } from './README.md';
