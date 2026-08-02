/** Storage Manager — central orchestrator with Zustand store */
import { create } from 'zustand';
import type { StorageType, StorageEntry, CacheStats } from './StorageTypes';
import { storageLogger } from './StorageConfig';

class StorageStore {
  private store = new Map<string, StorageEntry>();

  get<T>(key: string): T | null {
    const entry = this.store.get(key);
    if (!entry) return null;
    entry.accessCount++; entry.lastAccessed = Date.now();
    return entry.value as T;
  }

  set<T>(key: string, value: T, type: StorageType = 'mmkv', ttlMs?: number): void {
    this.store.set(key, { key, value, type, createdAt: Date.now(), ttlMs: ttlMs ?? null, accessCount: 0, lastAccessed: Date.now() });
  }

  delete(key: string): boolean { return this.store.delete(key); }
  has(key: string): boolean { return this.store.has(key); }
  keys(): string[] { return Array.from(this.store.keys()); }
  getAll(): Record<string, any> { const obj: Record<string, any> = {}; this.store.forEach((v, k) => { obj[k] = v.value; }); return obj; }
  clear(): void { this.store.clear(); storageLogger.info('Storage cleared'); }
  size(): number { return this.store.size; }

  getStats(): CacheStats {
    let hits = 0; let misses = 0;
    this.store.forEach((v) => { if (v.accessCount > 0) hits += v.accessCount; else misses++; });
    return { entries: this.store.size, hits, misses, hitRate: hits + misses > 0 ? hits / (hits + misses) : 0, sizeBytes: 0 };
  }

  cleanup(ttlMs?: number): void {
    const maxTtl = ttlMs ?? 30 * 60 * 1000;
    const now = Date.now();
    const toDelete: string[] = [];
    this.store.forEach((v, k) => { if (now - v.createdAt > maxTtl) toDelete.push(k); });
    toDelete.forEach((k) => this.store.delete(k));
    if (toDelete.length > 0) storageLogger.info(`Cleaned up ${toDelete.length} stale entries`);
  }
}

interface StoreState { ready: boolean; cacheSize: number; usage: number; lastCleanup: number; migrationStatus: string; }
export const useStorageState = create<StoreState>(() => ({ ready: false, cacheSize: 0, usage: 0, lastCleanup: 0, migrationStatus: 'pending' }));
export const storageStore = new StorageStore();

export class StorageManager {
  private store = storageStore;
  private log = storageLogger;

  async initialize(): Promise<void> { this.log.info('Storage initialized'); useStorageState.setState({ ready: true, migrationStatus: 'complete' }); }
  get<T>(key: string): T | null { return this.store.get<T>(key); }
  set<T>(key: string, value: T, ttlMs?: number): void { this.store.set(key, value, 'mmkv', ttlMs); }
  remove(key: string): void { this.store.delete(key); }
  clear(): void { this.store.clear(); useStorageState.setState({ cacheSize: 0 }); }
  getStats(): CacheStats { return this.store.getStats(); }
}
export const storageManager = new StorageManager();
