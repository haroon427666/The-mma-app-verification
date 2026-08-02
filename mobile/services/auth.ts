/** Auth service — login, register, token management, biometric */

import api from './api';
import { useAuthStore } from '@/stores/auth';
import type { User, AuthTokens } from '@/types';
import * as SecureStore from 'expo-secure-store';
import * as LocalAuthentication from 'expo-local-authentication';

const TOKEN_KEY = 'auth_tokens';
const BIOMETRIC_KEY = 'biometric_enabled';
const USER_KEY = 'cached_user';

export const authService = {
  // ── API calls ──────────────────────────────────────────────────────

  async login(email: string, password: string, rememberMe = false) {
    const { data } = await api.post<AuthTokens & { user: User }>(
      '/v1/auth/login', { email, password, remember_me: rememberMe },
    );
    await this.persistSession(data);
    return data;
  },

  async register(email: string, username: string, password: string, displayName?: string) {
    const { data } = await api.post<AuthTokens & { user: User }>(
      '/v1/auth/register', { email, username, password, display_name: displayName },
    );
    await this.persistSession(data);
    return data;
  },

  async logout() {
    try { await api.post('/v1/auth/logout'); } catch { /* fire-and-forget */ }
    await this.clearSession();
  },

  async logoutAll() {
    try { await api.post('/v1/auth/logout-all'); } catch { /* fire-and-forget */ }
    await this.clearSession();
  },

  async forgotPassword(email: string) {
    await api.post('/v1/auth/forgot-password', { email });
  },

  async resetPassword(token: string, newPassword: string) {
    await api.post('/v1/auth/reset-password', { token, new_password: newPassword });
  },

  async verifyEmail(token: string) {
    await api.post('/v1/auth/verify-email', { token });
  },

  async changePassword(currentPassword: string, newPassword: string) {
    await api.post('/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  async deleteAccount() {
    await api.delete('/v1/me');
    await this.clearSession();
  },

  // ── Session persistence ────────────────────────────────────────────

  async persistSession(data: AuthTokens & { user: User }) {
    const store = useAuthStore.getState();
    store.setTokens({ accessToken: data.accessToken, refreshToken: data.refreshToken, expiresIn: data.expiresIn, tokenType: data.tokenType });
    store.setUser(data.user);

    await SecureStore.setItemAsync(TOKEN_KEY, JSON.stringify({
      accessToken: data.accessToken,
      refreshToken: data.refreshToken,
    }));
    await SecureStore.setItemAsync(USER_KEY, JSON.stringify(data.user));
  },

  async restoreSession(): Promise<boolean> {
    try {
      const raw = await SecureStore.getItemAsync(TOKEN_KEY);
      const userRaw = await SecureStore.getItemAsync(USER_KEY);
      if (!raw || !userRaw) return false;

      const tokens = JSON.parse(raw) as AuthTokens;
      const user = JSON.parse(userRaw) as User;

      useAuthStore.getState().setTokens(tokens);
      useAuthStore.getState().setUser(user);

      // Verify token is still valid with a quick ping
      try {
        await api.get('/v1/me');
        return true;
      } catch {
        // Try refresh
        try {
          const { data } = await api.post<AuthTokens>('/v1/auth/refresh', {
            refresh_token: tokens.refreshToken,
          });
          useAuthStore.getState().setTokens(data);
          await SecureStore.setItemAsync(TOKEN_KEY, JSON.stringify(data));
          return true;
        } catch {
          await this.clearSession();
          return false;
        }
      }
    } catch {
      return false;
    }
  },

  async clearSession() {
    useAuthStore.getState().logout();
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    await SecureStore.deleteItemAsync(USER_KEY);
  },

  // ── Biometric ──────────────────────────────────────────────────────

  async isBiometricAvailable(): Promise<boolean> {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    return compatible && enrolled;
  },

  async authenticateWithBiometric(): Promise<boolean> {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Unlock MMA Intelligence',
        fallbackLabel: 'Use password',
      });
      return result.success;
    } catch {
      return false;
    }
  },

  async enableBiometric(): Promise<void> {
    await SecureStore.setItemAsync(BIOMETRIC_KEY, 'true');
    useAuthStore.getState().setBiometric(true);
  },

  async disableBiometric(): Promise<void> {
    await SecureStore.deleteItemAsync(BIOMETRIC_KEY);
    useAuthStore.getState().setBiometric(false);
  },
};
