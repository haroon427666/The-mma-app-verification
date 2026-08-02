/** Offline Config + Constants + Errors + Logger + Utils */
import { OfflineConfig, ConflictStrategy } from './OfflineTypes';

export const defaultOfflineConfig: OfflineConfig = {
  enableBackgroundSync: true, syncIntervalMs: 5 * 60 * 1000,
  maxQueueSize: 500, retryMaxAttempts: 5, retryBackoffMs: 2000,
  conflictStrategy: 'last_write_wins', enableAutoSync: true,
  syncOnReconnect: true, persistQueue: true,
};

let overrides: Partial<OfflineConfig> = {};
export const offlineConfig = {
  get: (): OfflineConfig => ({ ...defaultOfflineConfig, ...overrides }),
  update: (p: Partial<OfflineConfig>) => { overrides = { ...overrides, ...p }; },
};

export const OFFLINE_CONSTANTS = {
  SYNC_PRIORITY: { HIGH: 1, MEDIUM: 5, LOW: 10 } as const,
  MAX_RETRIES: 5, QUEUE_PERSIST_KEY: 'offline_queue',
  LAST_SYNC_KEY: 'last_sync_timestamp', BATCH_SIZE: 50,
};

export class OfflineLogger {
  private prefix = '[Offline]';
  info(m: string) { console.log(`${this.prefix} ${m}`); }
  warn(m: string) { console.warn(`${this.prefix} ${m}`); }
  error(m: string, e?: Error) { console.error(`${this.prefix} ${m}`, e?.message || ''); }
  sync(m: string, d?: number) { console.log(`${this.prefix} ⚡ ${m}${d ? ` (${d}ms)` : ''}`); }
}
export const offlineLogger = new OfflineLogger();

export function generateId(): string { return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`; }
export function isExpired(timestamp: number, ttlMs: number): boolean { return Date.now() - timestamp > ttlMs; }
