/** Storage Hooks — useStorage, useCache, usePreferences, useSession, useSecureStorage */
import { useState, useCallback, useEffect } from 'react';
import { storageManager, useStorageState } from './StorageManager';
import { cacheStorage } from './CacheStorage';
import { sessionStorage } from './CacheStorage';
import { preferencesStorage } from './CacheStorage';
import { secureStorage } from './MMKVStorage';

export function useStorage<T>(key: string) {
  const [value, setValue] = useState<T | null>(() => storageManager.get<T>(key));
  const set = useCallback((v: T, ttlMs?: number) => { storageManager.set(key, v, ttlMs); setValue(v); }, [key]);
  const remove = useCallback(() => { storageManager.remove(key); setValue(null); }, [key]);
  return { value, set, remove };
}

export function useCache<T>(key: string, ttlMs?: number) {
  const [value, setValue] = useState<T | null>(() => cacheStorage.get<T>(key));
  const set = useCallback((v: T) => { cacheStorage.set(key, v, ttlMs); setValue(v); }, [key, ttlMs]);
  const remove = useCallback(() => { cacheStorage.delete(key); setValue(null); }, [key]);
  const stats = cacheStorage.stats;
  return { value, set, remove, stats };
}

export function usePreferences<T>(key: string, defaultValue?: T) {
  const [value, setValue] = useState<T>(() => preferencesStorage.get<T>(key) ?? defaultValue as T);
  const set = useCallback((v: T) => { preferencesStorage.set(key, v); setValue(v); }, [key]);
  return { value, set };
}

export function useSession<T>(key: string) {
  const [value, setValue] = useState<T | undefined>(() => sessionStorage.get<T>(key));
  const set = useCallback((v: T) => { sessionStorage.set(key, v); setValue(v); }, [key]);
  const remove = useCallback(() => { sessionStorage.delete(key); setValue(undefined); }, [key]);
  return { value, set, remove };
}

export function useSecureStorage<T>(key: string) {
  const [value, setValue] = useState<T | null>(() => secureStorage.get<T>(key));
  const set = useCallback((v: T) => { secureStorage.set(key, v); setValue(v); }, [key]);
  const remove = useCallback(() => { secureStorage.delete(key); setValue(null); }, [key]);
  return { value, set, remove };
}

export function usePersistentStorage<T>(key: string) {
  const { value, set, remove } = useStorage<T>(key);
  return { value, set, remove };
}
