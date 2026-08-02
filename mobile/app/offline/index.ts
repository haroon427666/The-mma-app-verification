/** Offline Platform — barrel export */
export { OfflineManager, offlineManager, useOfflineStore } from './OfflineManager';
export { connectivity, useConnectivity } from './Connectivity';
export { SyncEngine, syncEngine } from './SyncEngine';
export { QueueManager, queueManager } from './QueueManager';
export { ConflictResolver, conflictResolver } from './ConflictResolver';
export { RetryManager, retryManager } from './RetryManager';
export { OfflineAnalytics, offlineAnalytics, SyncMetricsCollector, syncMetrics } from './OfflineAnalytics';
export { offlineConfig, OFFLINE_CONSTANTS, OfflineLogger, offlineLogger, generateId, isExpired } from './OfflineConfig';
export { useOffline, useOfflineStatus, useSync, useQueue, usePendingMutations, useLastSync } from './OfflineHooks';
export type { ConnectionState, ConnectionType, SyncMode, SyncStatus, ConflictStrategy, OfflineConfig, SyncTask, Mutation, QueueEntry, SyncResult, SyncMetrics } from './OfflineTypes';
export { OfflineError, SyncError, ConflictError, QueueError } from './OfflineTypes';
