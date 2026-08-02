/** Connectivity store — network status, offline queue */

import { create } from 'zustand';
import type { NetworkStatus, OfflineAction } from '@/types';

interface ConnectivityState {
  status: NetworkStatus;
  offlineQueue: OfflineAction[];
  lastOnlineAt: string | null;

  setStatus: (status: NetworkStatus) => void;
  enqueueOffline: (action: Omit<OfflineAction, 'id' | 'createdAt' | 'retryCount'>) => void;
  processQueue: () => OfflineAction[];
  clearQueue: () => void;
}

export const useConnectivityStore = create<ConnectivityState>((set, get) => ({
  status: 'online',
  offlineQueue: [],
  lastOnlineAt: null,

  setStatus: (status) => {
    if (status === 'online') {
      set({ status, lastOnlineAt: new Date().toISOString() });
    } else {
      set({ status });
    }
  },
  enqueueOffline: (action) => {
    const item: OfflineAction = {
      ...action,
      id: Math.random().toString(36).slice(2),
      createdAt: new Date().toISOString(),
      retryCount: 0,
    };
    set((s) => ({ offlineQueue: [...s.offlineQueue, item] }));
  },
  processQueue: () => {
    const queue = get().offlineQueue;
    set({ offlineQueue: [] });
    return queue;
  },
  clearQueue: () => set({ offlineQueue: [] }),
}));
