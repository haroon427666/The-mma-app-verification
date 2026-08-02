/** Bootstrap types — startup stage, state, events, errors */
export type StartupStage =
  | 'idle' | 'env' | 'storage' | 'theme_locale' | 'query_client'
  | 'auth' | 'notifications' | 'remote_config' | 'ready' | 'failed';

export interface BootstrapState {
  stage: StartupStage; progress: number; isReady: boolean;
  error: BootstrapError | null; startupTimeMs: number; startedAt: number;
}

export interface BootstrapConfig {
  environment: 'development' | 'staging' | 'production';
  apiBaseUrl: string; minSplashDurationMs: number;
  retryMaxAttempts: number; retryBackoffMs: number;
  requireAuth: boolean; enableAnalytics: boolean;
  enableCrashReporting: boolean; enableFeatureFlags: boolean;
}

export interface StartupTask {
  name: string; stage: StartupStage; execute: () => Promise<void>;
  onError?: (err: Error) => void; critical: boolean;
}

export interface BootstrapEvent {
  type: 'stage_start' | 'stage_complete' | 'stage_failed' | 'startup_complete' | 'fatal_error';
  stage?: StartupStage; durationMs?: number; error?: Error; timestamp: number;
}

export interface BootstrapMetrics {
  coldStart: boolean; totalDurationMs: number;
  stageDurations: Partial<Record<StartupStage, number>>;
  providerCount: number; memoryUsageBytes?: number;
}

export class BootstrapError extends Error {
  constructor(message: string, public stage: StartupStage, public recoverable: boolean) { super(message); this.name = 'BootstrapError'; }
}
