/** Offline Analytics + Sync Metrics */
import type { SyncResult, SyncMetrics } from './OfflineTypes';

export class OfflineAnalytics {
  trackOfflineSession(): void {}
  trackSync(result: SyncResult): void { if (__DEV__) console.log('[Offline] Sync result:', result); }
  trackConflict(entityId: string): void {}
  trackRetry(mutationId: string): void {}
}
export const offlineAnalytics = new OfflineAnalytics();

export class SyncMetricsCollector {
  private metrics: SyncMetrics = { totalSyncs: 0, failedSyncs: 0, avgDurationMs: 0, conflictsResolved: 0, lastSyncTime: 0 };
  record(result: SyncResult): void {
    this.metrics.totalSyncs++;
    if (!result.success) this.metrics.failedSyncs++;
    this.metrics.conflictsResolved += result.conflicts;
    this.metrics.avgDurationMs = (this.metrics.avgDurationMs * (this.metrics.totalSyncs - 1) + result.durationMs) / this.metrics.totalSyncs;
    this.metrics.lastSyncTime = result.timestamp;
  }
  get(): SyncMetrics { return { ...this.metrics }; }
}
export const syncMetrics = new SyncMetricsCollector();
