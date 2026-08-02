/** Conflict Resolver — resolution strategies (LWW, server wins, client wins, merge, manual) */
import type { ConflictStrategy } from './OfflineTypes';
import { offlineConfig } from './OfflineConfig';

interface ConflictRecord { localVersion: number; serverVersion: number; localData: any; serverData: any; entityId: string; }

export class ConflictResolver {
  private pending: ConflictRecord[] = [];

  resolve(local: any, server: any, entityId: string, localVersion: number, serverVersion: number): any {
    const strategy = offlineConfig.get().conflictStrategy;
    const record: ConflictRecord = { localVersion, serverVersion, localData: local, serverData: server, entityId };
    this.pending.push(record);

    switch (strategy) {
      case 'last_write_wins': return localVersion >= serverVersion ? local : server;
      case 'server_wins': return server;
      case 'client_wins': return local;
      case 'merge': return this.mergeFields(local, server);
      case 'manual': return { local, server, requiresResolution: true, entityId };
      default: return server;
    }
  }

  private mergeFields(local: any, server: any): any {
    if (typeof local !== 'object' || typeof server !== 'object') return server;
    const merged = { ...server, ...local };
    for (const key of Object.keys(merged)) {
      if (Array.isArray(local[key]) && Array.isArray(server[key])) merged[key] = [...new Set([...server[key], ...local[key]])];
    }
    return merged;
  }

  get pendingCount(): number { return this.pending.length; }
  clear(): void { this.pending = []; }
}
export const conflictResolver = new ConflictResolver();
