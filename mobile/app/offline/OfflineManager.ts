/** Offline Manager — central orchestrator for connectivity, sync, and queues */
import { create } from 'zustand';
import type { ConnectionState, SyncStatus, Mutation, SyncResult, SyncMetrics } from './OfflineTypes';
import { offlineConfig } from './OfflineConfig';
import { offlineLogger } from './OfflineConfig';

interface OfflineStore {
  isOffline: boolean; connectionState: ConnectionState; syncStatus: SyncStatus;
  queueSize: number; pendingMutations: number; lastSync: number | null;
  syncErrors: string[]; syncProgress: number; metrics: SyncMetrics;
  setConnection: (s: ConnectionState) => void; setSyncStatus: (s: SyncStatus) => void;
  recordSync: (r: SyncResult) => void; addError: (e: string) => void;
  clearErrors: () => void; setProgress: (p: number) => void;
}

export const useOfflineStore = create<OfflineStore>((set) => ({
  isOffline: false, connectionState: 'unknown', syncStatus: 'idle',
  queueSize: 0, pendingMutations: 0, lastSync: null, syncErrors: [], syncProgress: 0,
  metrics: { totalSyncs: 0, failedSyncs: 0, avgDurationMs: 0, conflictsResolved: 0, lastSyncTime: 0 },
  setConnection: (s) => set({ isOffline: s === 'offline', connectionState: s }),
  setSyncStatus: (s) => set({ syncStatus: s }),
  recordSync: (r) => set((st) => ({
    lastSync: r.timestamp, syncProgress: 100,
    metrics: { ...st.metrics, totalSyncs: st.metrics.totalSyncs + 1, failedSyncs: st.metrics.failedSyncs + (r.success ? 0 : 1), lastSyncTime: r.timestamp, conflictsResolved: st.metrics.conflictsResolved + r.conflicts },
  })),
  addError: (e) => set((s) => ({ syncErrors: [...s.syncErrors.slice(-10), e] })),
  clearErrors: () => set({ syncErrors: [] }),
  setProgress: (p) => set({ syncProgress: p }),
}));

export class OfflineManager {
  private queue: Mutation[] = [];
  private listeners = new Set<() => void>();
  private log = offlineLogger;

  get isOffline(): boolean { return useOfflineStore.getState().isOffline; }
  get queueLength(): number { return this.queue.length; }

  subscribe(fn: () => void): () => void { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  private notify() { this.listeners.forEach((f) => f()); this.syncStore(); }

  enqueue(mutation: Mutation): void {
    const cfg = offlineConfig.get();
    if (this.queue.length >= cfg.maxQueueSize) { this.log.warn('Queue full, dropping oldest'); this.queue.shift(); }
    this.queue.push({ ...mutation, retries: 0, timestamp: Date.now() });
    this.notify();
  }

  dequeue(): Mutation | undefined { const m = this.queue.shift(); this.notify(); return m; }
  peek(): Mutation | undefined { return this.queue[0]; }
  remove(id: string): void { this.queue = this.queue.filter((m) => m.id !== id); this.notify(); }
  clear(): void { this.queue = []; this.notify(); }

  private syncStore() {
    const store = useOfflineStore.getState();
    useOfflineStore.setState({ queueSize: this.queue.length, pendingMutations: this.queue.length });
  }
}
export const offlineManager = new OfflineManager();
