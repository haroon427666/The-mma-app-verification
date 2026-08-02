/** QueryProvider — TanStack React Query with offline cache */

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import { PersistQueryClientProvider } from '@tanstack/react-query-persist-client';

let MMKV: any;
try { MMKV = require('react-native-mmkv'); } catch { /* fallback */ }

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,       // 5 min
      gcTime: 30 * 60 * 1000,          // 30 min garbage collection
      retry: 2,
      retryDelay: (attempt) => Math.min(attempt * 1000, 5000),
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Offline persistence via MMKV
let persister: any = null;
if (MMKV) {
  const storage = new MMKV.MMKV({ id: 'query-cache' });
  persister = createAsyncStoragePersister({
    storage: {
      getItem: (key: string) => storage.getString(key) ?? null,
      setItem: (key: string, value: string) => storage.set(key, value),
      removeItem: (key: string) => storage.delete(key),
    },
  });
}

export function QueryProvider({ children }: { children: React.ReactNode }) {
  if (persister) {
    return (
      <PersistQueryClientProvider
        client={queryClient}
        persistOptions={{ persister }}
      >
        {children}
      </PersistQueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

export { queryClient };
