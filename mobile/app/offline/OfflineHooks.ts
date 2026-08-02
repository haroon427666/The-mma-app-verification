/** Offline Hooks — useOffline, useConnectivity, useSync, useQueue */
import { useEffect, useState } from 'react';
import { useOfflineStore, offlineManager } from './OfflineManager';
import { connectivity } from './Connectivity';
import type { ConnectionState, SyncStatus } from './OfflineTypes';

export function useOffline() {
  const { isOffline, connectionState, syncStatus, queueSize, pendingMutations, lastSync, syncErrors } = useOfflineStore();
  return { isOffline, connectionState, syncStatus, queueSize, pendingMutations, lastSync, syncErrors };
}

export function useOfflineStatus() {
  return useOffline();
}

export { useConnectivity } from './Connectivity';

export function useSync() {
  const { syncStatus, syncProgress, lastSync } = useOfflineStore();
  return { syncStatus, syncProgress, lastSync };
}

export function useQueue() {
  const [size, setSize] = useState(offlineManager.queueLength);
  useEffect(() => offlineManager.subscribe(() => setSize(offlineManager.queueLength)), []);
  return { queueSize: size, clearQueue: () => offlineManager.clear() };
}

export function usePendingMutations() {
  const { pendingMutations } = useOfflineStore();
  return { pendingMutations };
}

export function useLastSync() {
  const { lastSync } = useOfflineStore();
  return { lastSync };
}
