/** Bootstrap config — environment-specific settings */
import { BootstrapConfig } from './BootstrapTypes';

export function getBootstrapConfig(): BootstrapConfig {
  return {
    environment: (process.env.EXPO_PUBLIC_ENV as any) || 'development',
    apiBaseUrl: process.env.EXPO_PUBLIC_API_URL || 'https://api.mma-app.com',
    minSplashDurationMs: 1500,
    retryMaxAttempts: 3,
    retryBackoffMs: 1000,
    requireAuth: true,
    enableAnalytics: true,
    enableCrashReporting: true,
    enableFeatureFlags: false,
  };
}
