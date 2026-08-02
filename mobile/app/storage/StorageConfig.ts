/** Storage Config + Constants + Errors + Logger + Utils */
import { StorageConfig } from './StorageTypes';

export const defaultStorageConfig: StorageConfig = {
  defaultType: 'mmkv', maxCacheEntries: 1000, defaultTTLMs: 30 * 60 * 1000,
  enableEncryption: true, enableCompression: false, enableMigration: true,
  autoCleanup: true, cleanupIntervalMs: 60 * 60 * 1000,
};

let overrides: Partial<StorageConfig> = {};
export const storageConfig = {
  get: (): StorageConfig => ({ ...defaultStorageConfig, ...overrides }),
  update: (p: Partial<StorageConfig>) => { overrides = { ...overrides, ...p }; },
};

export const STORAGE_CONSTANTS = {
  KEYS: { THEME: 'theme_pref', LOCALE: 'locale_pref', TOKEN: 'auth_token', REFRESH_TOKEN: 'refresh_token', USER: 'user_profile', FAVORITES: 'favorites', WATCHLIST: 'watchlist', SEARCH_HISTORY: 'search_history', OFFLINE_QUEUE: 'offline_queue', REMOTE_CONFIG: 'remote_config' },
  PREFIXES: { CACHE: 'cache:', SESSION: 'session:', PREF: 'pref:', SECURE: 'secure:', TEMP: 'temp:' },
  VERSION_KEY: '__storage_version__',
} as const;

export class StorageLogger {
  private prefix = '[Storage]';
  info(m: string) { console.log(`${this.prefix} ${m}`); }
  warn(m: string) { console.warn(`${this.prefix} ${m}`); }
  error(m: string, e?: Error) { console.error(`${this.prefix} ${m}`, e?.message || ''); }
}
export const storageLogger = new StorageLogger();

export const storageUtils = {
  encode: (v: any): string => { try { return JSON.stringify(v); } catch { return ''; } },
  decode: <T>(s: string): T | null => { try { return JSON.parse(s); } catch { return null; } },
  ttlKey: (key: string): string => `${key}:ttl`,
  isExpired: (ts: number, ttl: number): boolean => Date.now() - ts > ttl,
};
