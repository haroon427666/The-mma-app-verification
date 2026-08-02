/** Auth Managers — Login, Logout, Register, PasswordReset, EmailVerification, AuthService, AuthManager, Token Management */
import { useAuthStore } from './AuthStore';
import { authLogger, authEvents, authUtils, authConfig, AUTH_CONSTANTS, AuthenticationError, TokenExpiredError, RefreshError } from './AuthTypes';
import type { LoginRequest, UserIdentity, AuthTokens } from './AuthTypes';

// ── AuthService ──
export class AuthService {
  async login(req: LoginRequest): Promise<{ user: UserIdentity; tokens: AuthTokens }> {
    authLogger.info(`Login: ${req.email}`);
    return { user: { id: 'u-1', email: req.email, username: req.email.split('@')[0], displayName: null, avatarUrl: null, role: 'user', emailVerified: true, createdAt: new Date().toISOString() }, tokens: { accessToken: 'at-xxx', refreshToken: 'rt-xxx', expiresAt: Date.now() + 3600000, tokenType: 'Bearer' } };
  }
  async register(email: string, password: string, username: string): Promise<{ user: UserIdentity; tokens: AuthTokens }> {
    return { user: { id: 'u-new', email, username, displayName: null, avatarUrl: null, role: 'user', emailVerified: false, createdAt: new Date().toISOString() }, tokens: { accessToken: 'at-new', refreshToken: 'rt-new', expiresAt: Date.now() + 3600000, tokenType: 'Bearer' } };
  }
  async refreshToken(refreshToken: string): Promise<AuthTokens> {
    return { accessToken: 'at-refreshed', refreshToken, expiresAt: Date.now() + 3600000, tokenType: 'Bearer' };
  }
  async logout(): Promise<void> {}
  async resetPassword(email: string): Promise<void> { authLogger.info(`Password reset sent: ${email}`); }
  async verifyEmail(token: string): Promise<void> { authLogger.info('Email verified'); }
}

export const authService = new AuthService();

// ── AuthManager ──
export class AuthManager {
  private svc = authService;

  async login(req: LoginRequest): Promise<void> {
    const store = useAuthStore.getState();
    if (store.lockoutUntil && Date.now() < store.lockoutUntil) throw new AuthenticationError('Account locked');
    store.setLoading(true);
    try {
      const result = await this.svc.login(req);
      store.setAuthenticated(result.user, result.tokens);
      store.resetLoginAttempts();
      authEvents.emit({ type: 'login', timestamp: Date.now() });
      authLogger.info('Login successful');
    } catch (err) {
      store.incrementLoginAttempts();
      authEvents.emit({ type: 'error', timestamp: Date.now(), details: err });
      throw err;
    }
  }

  async logout(allDevices = false): Promise<void> {
    try { await this.svc.logout(); } catch {}
    useAuthStore.getState().setUnauthenticated();
    authEvents.emit({ type: 'logout', timestamp: Date.now(), details: { allDevices } });
  }

  async register(email: string, password: string, username: string): Promise<void> {
    useAuthStore.getState().setLoading(true);
    try {
      const result = await this.svc.register(email, password, username);
      useAuthStore.getState().setAuthenticated(result.user, result.tokens);
    } catch (err) { throw err; }
  }

  async restoreSession(): Promise<void> {
    const tokens = TokenStorage.getTokens();
    if (!tokens) { useAuthStore.getState().setUnauthenticated(); return; }
    if (authUtils.isTokenExpired(tokens.expiresAt, authConfig.get().tokenRefreshBufferMs)) {
      try {
        const newTokens = await this.svc.refreshToken(tokens.refreshToken);
        TokenStorage.saveTokens(newTokens);
        useAuthStore.getState().updateTokens(newTokens);
      } catch {
        useAuthStore.getState().setUnauthenticated();
        return;
      }
    }
    // Restore user from stored profile
    useAuthStore.getState().setAuthenticated({ id: 'u-restored', email: '', username: '', displayName: null, avatarUrl: null, role: 'user', emailVerified: true, createdAt: '' }, tokens);
  }
}

export const authManager = new AuthManager();

// ── Token Management ──
export class TokenStorage {
  static saveTokens(tokens: AuthTokens): void { /* secureStorage.set multiple keys */ }
  static getTokens(): AuthTokens | null { return null; /* secureStorage.get */ }
  static clearTokens(): void { /* secureStorage.delete */ }
  static isValid(): boolean { const t = this.getTokens(); return t ? !authUtils.isTokenExpired(t.expiresAt) : false; }
}

export class TokenValidator {
  static validate(token: string): boolean { return token?.length > 10; }
  static decode(token: string): any { try { return JSON.parse(atob(token.split('.')[1])); } catch { return null; } }
}

export class RefreshManager {
  private refreshing: Promise<AuthTokens> | null = null;
  async refresh(token: string): Promise<AuthTokens> {
    if (this.refreshing) return this.refreshing;
    this.refreshing = authService.refreshToken(token);
    try { const result = await this.refreshing; return result; } finally { this.refreshing = null; }
  }
}
export const refreshManager = new RefreshManager();

// ── Biometric ──
export class BiometricManager {
  async isAvailable(): Promise<{ available: boolean; type: string }> { return { available: true, type: 'face_id' }; }
  async authenticate(reason = 'Sign in'): Promise<boolean> { authEvents.emit({ type: 'biometric', timestamp: Date.now(), details: { success: true, reason } }); return true; }
  async enroll(): Promise<boolean> { useAuthStore.getState().setBiometric(true); return true; }
}
export const biometricManager = new BiometricManager();
