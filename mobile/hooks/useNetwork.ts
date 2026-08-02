/** useNetwork — monitors connectivity and triggers offline queue sync */

import { useEffect, useCallback } from 'react';
import { AppState, AppStateStatus } from 'react-native';
import { useConnectivityStore } from '@/stores/connectivity';
import api from '@/services/api';

export function useNetwork() {
  const store = useConnectivityStore();

  const checkConnectivity = useCallback(async () => {
    try {
      await api.get('/health', { timeout: 5000 });
      store.setStatus('online');
    } catch {
      store.setStatus('offline');
    }
  }, [store]);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (state: AppStateStatus) => {
      if (state === 'active') checkConnectivity();
    });
    checkConnectivity();
    return () => sub.remove();
  }, [checkConnectivity]);

  return {
    status: store.status,
    isOnline: store.status === 'online',
    isOffline: store.status === 'offline',
    hasQueue: store.offlineQueue.length > 0,
    checkConnectivity,
  };
}
