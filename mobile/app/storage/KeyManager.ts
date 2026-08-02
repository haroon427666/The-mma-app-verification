/** Key Manager + Registry — centralize all storage keys */
export const StorageKeys = {
  // Auth
  AUTH_TOKEN: 'auth_token', REFRESH_TOKEN: 'refresh_token', SESSION: 'session_data', BIOMETRIC_ENABLED: 'biometric_enabled',
  // User
  USER_PROFILE: 'user_profile', USER_PREFERENCES: 'user_preferences', USER_SETTINGS: 'user_settings',
  // Theme
  THEME_MODE: 'theme_mode', DYNAMIC_THEME: 'dynamic_theme',
  // Locale
  LANGUAGE: 'language', TIMEZONE: 'timezone', UNITS: 'units',
  // App
  FIRST_LAUNCH: 'first_launch', LAST_LAUNCH: 'last_launch', APP_VERSION: 'app_version',
  INSTALL_ID: 'install_id',
  // Features
  FAVORITES: 'favorites', WATCHLIST: 'watchlist', SEARCH_HISTORY: 'search_history',
  RECENT_FILTERS: 'recent_filters',
  // Predictions
  SAVED_PREDICTIONS: 'saved_predictions', PREDICTION_HISTORY: 'prediction_history',
  // Notifications
  NOTIFICATION_PREFS: 'notification_prefs', PUSH_TOKEN: 'push_token',
  // Offline
  OFFLINE_QUEUE: 'offline_queue', MUTATION_QUEUE: 'mutation_queue', PENDING_SYNC: 'pending_sync',
  // Remote
  REMOTE_CONFIG: 'remote_config', FEATURE_FLAGS: 'feature_flags',
  // Analytics
  ANALYTICS_ENABLED: 'analytics_enabled', CRASH_REPORTING: 'crash_reporting',
  // Storage
  STORAGE_VERSION: '__storage_version__', MIGRATION_STATE: '__migration_state__',
} as const;

export class KeyManager {
  private registry = new Map<string, { type: string; encrypted: boolean }>();

  register(key: string, config: { type: string; encrypted?: boolean }): void {
    this.registry.set(key, { type: config.type, encrypted: config.encrypted ?? false });
  }

  getType(key: string): string | undefined { return this.registry.get(key)?.type; }
  isEncrypted(key: string): boolean { return this.registry.get(key)?.encrypted ?? false; }
  getAllKeys(): string[] { return Array.from(this.registry.keys()); }
  validate(key: string): boolean { return this.registry.has(key); }
}
export const keyManager = new KeyManager();
