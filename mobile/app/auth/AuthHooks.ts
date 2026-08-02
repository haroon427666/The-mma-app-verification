/** Auth Hooks — useAuth, useLogin, useLogout, useBiometric, useSession, useAuthorization */
import { useState, useCallback, useContext } from 'react';
import { useAuthStore, AuthContext } from './AuthStore';
import { authManager, biometricManager } from './AuthManager';
import { Authorization } from './Authorization';
import type { UserRole, LoginRequest } from './AuthTypes';

export function useAuth() {
  const ctx = useContext(AuthContext);
  const store = useAuthStore();
  return { ...ctx, ...store };
}

export function useLogin() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const login = useCallback(async (req: LoginRequest) => {
    setLoading(true); setError(null);
    try { await authManager.login(req); } catch (err) { setError(err as Error); throw err; } finally { setLoading(false); }
  }, []);
  return { login, loading, error };
}

export function useLogout() {
  const [loading, setLoading] = useState(false);
  const logout = useCallback(async (allDevices = false) => {
    setLoading(true);
    try { await authManager.logout(allDevices); } finally { setLoading(false); }
  }, []);
  return { logout, loading };
}

export function useCurrentUser() { return useAuthStore((s) => s.user); }

export function useBiometric() {
  const { biometricEnabled, setBiometric } = useAuthStore();
  const auth = useCallback(async (reason?: string) => biometricManager.authenticate(reason), []);
  const enroll = useCallback(async () => { const ok = await biometricManager.enroll(); if (ok) setBiometric(true); return ok; }, []);
  return { biometricEnabled, authenticate: auth, enroll };
}

export function useAuthorization<T extends UserRole = UserRole>(requiredRoles?: T[]) {
  const user = useCurrentUser();
  const isAuthorized = !requiredRoles || (user && Authorization.check(user.role, requiredRoles));
  const hasPermission = (p: string) => user ? Authorization.checkPermission(user.role, p) : false;
  return { isAuthorized, hasPermission, userRole: user?.role };
}

export function useSession() {
  const { status, user } = useAuthStore();
  const isValid = status === 'authenticated';
  const restore = useCallback(() => authManager.restoreSession(), []);
  return { isValid, restore, user };
}

export function usePermissions() {
  const user = useCurrentUser();
  const check = useCallback((p: string) => user ? Authorization.checkPermission(user.role, p) : false, [user]);
  return { hasPermission: check };
}
