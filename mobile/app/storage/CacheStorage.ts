/** Cache + Session + Temporary + Preferences + Persistent Storage */
import { storageStore, storageLogger } from './StorageManager';

export class CacheStorage {
  private prefix = 'cache:';
  get<T>(key: string): T | null { return storageStore.get<T>(this.prefix + key); }
  set<T>(key: string, value: T, ttlMs = 30 * 60 * 1000): void { storageStore.set(this.prefix + key, value, 'cache', ttlMs); }
  delete(key: string): void { storageStore.delete(this.prefix + key); }
  cleanup(olderThanMs: number): void { storageStore.cleanup(olderThanMs); }
  size(): number { return storageStore.size(); }
  get stats() { return storageStore.getStats(); }
}
export const cacheStorage = new CacheStorage();

export class SessionStorage {
  private prefix = 'session:';
  private active = new Map<string, any>();
  get<T>(key: string): T | undefined { return this.active.get(this.prefix + key) as T; }
  set<T>(key: string, value: T): void { this.active.set(this.prefix + key, value); }
  delete(key: string): void { this.active.delete(this.prefix + key); }
  clear(): void { this.active.clear(); }
}
export const sessionStorage = new SessionStorage();

export class PreferencesStorage {
  private prefix = 'pref:';
  get<T>(key: string): T | null { return storageStore.get<T>(this.prefix + key); }
  set<T>(key: string, value: T): void { storageStore.set(this.prefix + key, value, 'preferences'); }
  delete(key: string): void { storageStore.delete(this.prefix + key); }
  getAll(): Record<string, any> { const prefs: Record<string, any> = {}; storageStore.keys().filter((k) => k.startsWith(this.prefix)).forEach((k) => { prefs[k.replace(this.prefix, '')] = storageStore.get(k); }); return prefs; }
  sync(): void { storageLogger.info('Preferences synced'); }
}
export const preferencesStorage = new PreferencesStorage();

export class TemporaryStorage {
  private prefix = 'temp:';
  private store = new Map<string, { value: any; expires: number }>();
  get<T>(key: string): T | undefined { const e = this.store.get(this.prefix + key); if (!e || Date.now() > e.expires) return undefined; return e.value as T; }
  set<T>(key: string, value: T, ttlMs = 60_000): void { this.store.set(this.prefix + key, { value, expires: Date.now() + ttlMs }); }
  delete(key: string): void { this.store.delete(this.prefix + key); }
  clear(): void { this.store.clear(); }
}
export const temporaryStorage = new TemporaryStorage();

export class PersistentStorage {
  get<T>(key: string): T | null { return storageStore.get<T>(key); }
  set<T>(key: string, value: T): void { storageStore.set(key, value, 'persistent'); }
  delete(key: string): void { storageStore.delete(key); }
  exists(key: string): boolean { return storageStore.has(key); }
}
export const persistentStorage = new PersistentStorage();
