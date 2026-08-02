/** Offline Types — sync state, queues, conflicts, connectivity, metrics */
export type ConnectionState = 'online' | 'offline' | 'reconnecting' | 'unknown';
export type ConnectionType = 'wifi' | 'cellular' | 'ethernet' | 'none';
export type SyncMode = 'incremental' | 'full' | 'manual' | 'background' | 'foreground' | 'priority';
export type SyncStatus = 'idle' | 'syncing' | 'paused' | 'error' | 'complete';
export type ConflictStrategy = 'last_write_wins' | 'server_wins' | 'client_wins' | 'merge' | 'manual';

export interface OfflineConfig {
  enableBackgroundSync: boolean; syncIntervalMs: number;
  maxQueueSize: number; retryMaxAttempts: number; retryBackoffMs: number;
  conflictStrategy: ConflictStrategy; enableAutoSync: boolean;
  syncOnReconnect: boolean; persistQueue: boolean;
}

export interface SyncTask { id: string; type: SyncMode; entity: string; priority: number; data?: any; created: number; retries: number; }
export interface Mutation { id: string; type: 'create' | 'update' | 'delete'; endpoint: string; payload: any; timestamp: number; retries: number; priority: number; }
export interface QueueEntry<T = Mutation> { id: string; entry: T; status: 'pending' | 'processing' | 'failed' | 'completed'; addedAt: number; retries: number; }
export interface SyncResult { success: boolean; processed: number; failed: number; conflicts: number; durationMs: number; timestamp: number; }
export interface SyncMetrics { totalSyncs: number; failedSyncs: number; avgDurationMs: number; conflictsResolved: number; lastSyncTime: number; }

export class OfflineError extends Error { constructor(m: string) { super(m); this.name = 'OfflineError'; } }
export class SyncError extends Error { constructor(m: string, public taskId?: string) { super(m); this.name = 'SyncError'; } }
export class ConflictError extends Error { constructor(m: string, public entityId?: string) { super(m); this.name = 'ConflictError'; } }
export class QueueError extends Error { constructor(m: string) { super(m); this.name = 'QueueError'; } }
