/** Auth Store + Context + Provider */
import React, { createContext, useContext, useEffect, useMemo } from 'react';
import { create } from 'zustand';
import type { AuthStatus, UserIdentity, AuthTokens, UserRole, AuthConfig } from './AuthTypes';
import { authConfig } from './AuthTypes';
import { authLogger } from './AuthTypes';
import { authEvents } from './AuthTypes';

interface AuthState {
  status: AuthStatus; user: UserIdentity | null; tokens: AuthTokens | null;
  roles: UserRole[]; permissions: string[]; biometricEnabled: boolean;
  loading: boolean; error: Error | null; loginAttempts: number; lockoutUntil: number | null;
  setAuthenticated: (user: UserIdentity, tokens: AuthTokens) => void;
  setUnauthenticated: () => void; setLoading: (v: boolean) => void;
  setError: (e: Error) => void; setBiometric: (v: boolean) => void;
  incrementLoginAttempts: () => void; resetLoginAttempts: () => void;
  updateTokens: (tokens: AuthTokens) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: 'idle', user: null, tokens: null, roles: [], permissions: [],
  biometricEnabled: false, loading: false, error: null, loginAttempts: 0, lockoutUntil: null,
  setAuthenticated: (user, tokens) => set({ status: 'authenticated', user, tokens, roles: [user.role], permissions: Object.keys(require('./AuthTypes').AUTH_CONSTANTS.PERMISSIONS).filter((p) => require('./AuthTypes').AUTH_CONSTANTS.PERMISSIONS[p].includes(user.role)), loading: false, error: null }),
  setUnauthenticated: () => set({ status: 'unauthenticated', user: null, tokens: null, roles: [], permissions: [], loading: false }),
  setLoading: (v) => set({ loading: v, status: v ? 'loading' : get().status }),
  setError: (e) => set({ error: e, status: 'error', loading: false }),
  setBiometric: (v) => set({ biometricEnabled: v }),
  incrementLoginAttempts: () => { const a = get().loginAttempts + 1; set({ loginAttempts: a, lockoutUntil: a >= authConfig.get().maxLoginAttempts ? Date.now() + authConfig.get().lockoutDurationMs : null }); },
  resetLoginAttempts: () => set({ loginAttempts: 0, lockoutUntil: null }),
  updateTokens: (tokens) => set({ tokens }),
}));

interface AuthContextValue {
  isAuthenticated: boolean; isLoading: boolean; user: UserIdentity | null;
  tokens: AuthTokens | null; hasRole: (r: UserRole) => boolean;
  hasPermission: (p: string) => boolean; biometricAvailable: boolean;
}

export const AuthContext = createContext<AuthContextValue>({
  isAuthenticated: false, isLoading: true, user: null, tokens: null,
  hasRole: () => false, hasPermission: () => false, biometricAvailable: false,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { status, user, tokens, roles, permissions, biometricEnabled, loading } = useAuthStore();

  const value = useMemo(() => ({
    isAuthenticated: status === 'authenticated',
    isLoading: status === 'loading' || status === 'idle',
    user, tokens,
    hasRole: (r: UserRole) => roles.includes(r),
    hasPermission: (p: string) => permissions.includes(p),
    biometricAvailable: biometricEnabled,
  }), [status, user, tokens, roles, permissions, biometricEnabled, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
