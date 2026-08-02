/** Auth store — JWT tokens, user state, session management */

import { create } from 'zustand';
import type { User, AuthTokens, AuthStatus } from '@/types';

interface AuthState {
  status: AuthStatus;
  user: User | null;
  tokens: AuthTokens | null;
  isBiometricEnabled: boolean;

  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  setStatus: (status: AuthStatus) => void;
  setBiometric: (enabled: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'idle',
  user: null,
  tokens: null,
  isBiometricEnabled: false,

  setUser: (user) => set({ user, status: 'authenticated' }),
  setTokens: (tokens) => set({ tokens }),
  setStatus: (status) => set({ status }),
  setBiometric: (enabled) => set({ isBiometricEnabled: enabled }),
  logout: () => set({
    user: null, tokens: null,
    status: 'unauthenticated',
    isBiometricEnabled: false,
  }),
}));
