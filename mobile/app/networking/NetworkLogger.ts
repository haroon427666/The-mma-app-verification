/** Network Logger + Analytics + Request Metrics */
import type { RequestMetrics } from './NetworkTypes';

export class NetworkLogger {
  private enabled = __DEV__;
  setEnabled(v: boolean) { this.enabled = v; }
  log(method: string, url: string, status?: number, duration?: number, error?: string): void {
    if (!this.enabled) return;
    const statusStr = status ? ` ${status}` : '';
    const durStr = duration ? ` (${duration}ms)` : '';
    console.log(`[Network] ${method} ${url}${statusStr}${durStr}${error ? ` ERROR: ${error}` : ''}`);
  }
}
export const networkLogger = new NetworkLogger();

export class NetworkAnalytics {
  private metrics: RequestMetrics[] = [];
  private maxEntries = 1000;

  record(m: RequestMetrics): void { this.metrics.push(m); if (this.metrics.length > this.maxEntries) this.metrics.shift(); }

  getStats() {
    const total = this.metrics.length;
    if (total === 0) return { total: 0, successRate: 0, avgDurationMs: 0, cacheHitRate: 0 };
    const success = this.metrics.filter((m) => m.success).length;
    const avgDur = this.metrics.reduce((s, m) => s + m.durationMs, 0) / total;
    const cached = this.metrics.filter((m) => m.cached).length;
    return { total, successRate: success / total, avgDurationMs: Math.round(avgDur), cacheHitRate: cached / total };
  }

  getRecent(count = 20): RequestMetrics[] { return this.metrics.slice(-count); }
  clear(): void { this.metrics = []; }
}
export const networkAnalytics = new NetworkAnalytics();
