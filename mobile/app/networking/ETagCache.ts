/** ETag Cache — memory cache for conditional requests */
interface CacheEntry { data: any; etag: string; timestamp: number; }
export const cacheStore = {
  entries: new Map<string, CacheEntry>(),
  get(key: string): CacheEntry | undefined { return this.entries.get(key); },
  set(key: string, entry: CacheEntry): void { this.entries.set(key, entry); },
  has(key: string): boolean { return this.entries.has(key); },
  delete(key: string): void { this.entries.delete(key); },
  clear(): void { this.entries.clear(); },
  size(): number { return this.entries.size; },
  getStaleKeys(maxAgeMs: number): string[] {
    const now = Date.now(); const stale: string[] = [];
    this.entries.forEach((v, k) => { if (now - v.timestamp > maxAgeMs) stale.push(k); });
    return stale;
  },
};
