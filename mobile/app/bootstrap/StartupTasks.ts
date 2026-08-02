/** Startup tasks — ordered initialization steps for each stage */
import { container, DI_TOKENS } from './DependencyContainer';
import { bootstrapLogger } from './BootstrapLogger';
import { bootstrapEvents } from './BootstrapEvents';
import { getBootstrapConfig } from './BootstrapConfig';
import type { StartupTask } from './BootstrapTypes';

export function createStartupTasks(): StartupTask[] {
  const cfg = getBootstrapConfig();
  const log = bootstrapLogger;

  return [
    // Stage 1 — Environment
    { name: 'load_env', stage: 'env', critical: true, execute: async () => { log.stage('Environment validated'); } },
    { name: 'validate_config', stage: 'env', critical: true, execute: async () => { if (!cfg.apiBaseUrl) throw new Error('API base URL not configured'); log.stage('Config validated'); } },
    // Stage 2 — Storage
    { name: 'init_mmkv', stage: 'storage', critical: true, execute: async () => { /* MMKV.initialize() */ container.register(DI_TOKENS.STORAGE, {}); log.stage('MMKV initialized'); } },
    { name: 'init_encrypted', stage: 'storage', critical: false, execute: async () => { container.register(DI_TOKENS.ENCRYPTED_STORAGE, {}); log.stage('Encrypted storage ready'); } },
    { name: 'init_cache', stage: 'storage', critical: false, execute: async () => { container.register(DI_TOKENS.CACHE, new Map()); log.stage('Cache ready'); } },
    // Stage 3 — Theme & Locale
    { name: 'init_theme', stage: 'theme_locale', critical: false, execute: async () => { log.stage('Theme initialized'); } },
    { name: 'init_locale', stage: 'theme_locale', critical: false, execute: async () => { log.stage('Locale initialized'); } },
    // Stage 4 — Query Client
    { name: 'init_query', stage: 'query_client', critical: true, execute: async () => { container.register(DI_TOKENS.QUERY_CLIENT, {}); log.stage('Query client ready'); } },
    { name: 'init_api', stage: 'query_client', critical: true, execute: async () => { container.register(DI_TOKENS.API_CLIENT, {}); log.stage('API client ready'); } },
    // Stage 5 — Auth
    { name: 'restore_session', stage: 'auth', critical: false, execute: async () => { /* stored token restore */ log.stage('Session restored'); } },
    { name: 'refresh_token', stage: 'auth', critical: false, execute: async () => { /* background refresh if needed */ } },
    // Stage 6 — Notifications
    { name: 'init_notifications', stage: 'notifications', critical: false, execute: async () => { container.register(DI_TOKENS.NOTIFICATIONS, {}); log.stage('Notifications ready'); } },
    { name: 'init_deep_links', stage: 'notifications', critical: false, execute: async () => { container.register(DI_TOKENS.DEEP_LINKS, {}); log.stage('Deep links ready'); } },
    // Stage 7 — Remote Config
    { name: 'remote_config', stage: 'remote_config', critical: false, execute: async () => { if (cfg.enableFeatureFlags) { /* fetch remote config */ } log.stage('Remote config loaded'); } },
    { name: 'init_analytics', stage: 'remote_config', critical: false, execute: async () => { if (cfg.enableAnalytics) { container.register(DI_TOKENS.ANALYTICS, {}); } log.stage('Analytics ready'); } },
  ];
}
