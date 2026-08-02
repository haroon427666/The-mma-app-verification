/** useAuth — authentication hook for components */

import { useCallback } from 'react';
import { useAuthStore } from '@/stores/auth';
import { authService } from '@/services/auth';
import type { User } from '@/types';

export function useAuth() {
  const store = useAuthStore();

  const login = useCallback(async (email: string, password: string, rememberMe = false) => {
    store.setStatus('loading');
    try {
      const data = await authService.login(email, password, rememberMe);
      return data.user;
    } finally {
      store.setStatus('authenticated');
    }
  }, [store]);

  const register = useCallback(async (
    email: string, username: string, password: string, displayName?: string,
  ) => {
    store.setStatus('loading');
    try {
      const data = await authService.register(email, username, password, displayName);
      return data.user;
    } finally {
      store.setStatus('authenticated');
    }
  }, [store]);

  const logout = useCallback(async () => {
    await authService.logout();
  }, []);

  const logoutAll = useCallback(async () => {
    await authService.logoutAll();
  }, []);

  const restoreSession = useCallback(async (): Promise<boolean> => {
    store.setStatus('loading');
    try {
      const ok = await authService.restoreSession();
      store.setStatus(ok ? 'authenticated' : 'unauthenticated');
      return ok;
    } catch {
      store.setStatus('unauthenticated');
      return false;
    }
  }, [store]);

  return {
    user: store.user as User | null,
    status: store.status,
    isAuthenticated: store.status === 'authenticated',
    isLoading: store.status === 'loading',
    login, register, logout, logoutAll, restoreSession,
  };
}
