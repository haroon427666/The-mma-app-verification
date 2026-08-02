/** Auth Types, Config, Constants, Errors, Logger, Utils, Events */
export type AuthStatus = 'idle' | 'loading' | 'authenticated' | 'unauthenticated' | 'expired' | 'error';
export type BiometricType = 'face_id' | 'fingerprint' | 'passcode' | 'none';
export type AuthMethod = 'email' | 'google' | 'apple' | 'biometric';

export interface AuthConfig {
  tokenRefreshBufferMs: number; maxLoginAttempts: number;
  lockoutDurationMs: number; sessionTimeoutMs: number;
  enableBiometric: boolean; enableRememberMe: boolean;
  requireEmailVerification: boolean; tokenStorage: 'secure' | 'encrypted';
}
export interface UserIdentity { id: string; email: string; username: string; displayName: string | null; avatarUrl: string | null; role: UserRole; emailVerified: boolean; createdAt: string; }
export type UserRole = 'user' | 'premium' | 'analyst' | 'moderator' | 'admin';
export interface AuthTokens { accessToken: string; refreshToken: string; expiresAt: number; tokenType: string; }
export interface LoginRequest { email: string; password: string; rememberMe?: boolean; }
export interface AuthEvent { type: 'login' | 'logout' | 'refresh' | 'biometric' | 'error' | 'session_expired'; timestamp: number; details?: any; }
export interface AuthMetrics { loginCount: number; failedLogins: number; avgSessionDurationMs: number; lastLogin: number; }

export class AuthenticationError extends Error { constructor(m: string, public code?: string) { super(m); this.name = 'AuthenticationError'; } }
export class AuthorizationError extends Error { constructor(m: string) { super(m); this.name = 'AuthorizationError'; } }
export class TokenExpiredError extends AuthenticationError { constructor() { super('Token expired', 'TOKEN_EXPIRED'); this.name = 'TokenExpiredError'; } }
export class RefreshError extends AuthenticationError { constructor(m = 'Token refresh failed') { super(m, 'REFRESH_FAILED'); this.name = 'RefreshError'; } }
export class BiometricError extends AuthenticationError { constructor(m: string) { super(m, 'BIOMETRIC_ERROR'); this.name = 'BiometricError'; } }
export class SessionError extends AuthenticationError { constructor(m: string) { super(m, 'SESSION_ERROR'); this.name = 'SessionError'; } }

export const defaultAuthConfig: AuthConfig = {
  tokenRefreshBufferMs: 5 * 60 * 1000, maxLoginAttempts: 5, lockoutDurationMs: 15 * 60 * 1000,
  sessionTimeoutMs: 30 * 60 * 1000, enableBiometric: true, enableRememberMe: true,
  requireEmailVerification: true, tokenStorage: 'secure',
};

let overrides: Partial<AuthConfig> = {};
export const authConfig = {
  get: (): AuthConfig => ({ ...defaultAuthConfig, ...overrides }),
  update: (p: Partial<AuthConfig>) => { overrides = { ...overrides, ...p }; },
};

export const AUTH_CONSTANTS = {
  TOKEN_KEYS: { ACCESS: 'auth_token', REFRESH: 'refresh_token', EXPIRES: 'token_expires_at' },
  STORAGE_KEYS: { USER: 'user_profile', SESSION: 'session_state', BIOMETRIC: 'biometric_enabled', LOGIN_ATTEMPTS: 'login_attempts', LOCKOUT_UNTIL: 'lockout_until' },
  ROLES: ['user', 'premium', 'analyst', 'moderator', 'admin'] as UserRole[],
  PERMISSIONS: { VIEW_RANKINGS: ['user'], VIEW_PREDICTIONS: ['user', 'premium'], MANAGE_EVENTS: ['admin', 'moderator'], VIEW_ANALYTICS: ['analyst', 'admin'], EXPORT_DATA: ['premium', 'analyst', 'admin'] },
} as const;

export class AuthLogger {
  private prefix = '[Auth]';
  info(m: string) { console.log(`${this.prefix} ${m}`); }
  warn(m: string) { console.warn(`${this.prefix} ${m}`); }
  error(m: string, e?: Error) { console.error(`${this.prefix} ${m}`, e?.message ?? ''); }
}
export const authLogger = new AuthLogger();

export const authUtils = {
  isTokenExpired: (expiresAt: number, bufferMs = 5 * 60_000): boolean => Date.now() + bufferMs >= expiresAt,
  hasRole: (userRole: UserRole, allowedRoles: UserRole[]): boolean => allowedRoles.includes(userRole),
  hasPermission: (role: UserRole, permission: string): boolean => (AUTH_CONSTANTS.PERMISSIONS as any)[permission]?.includes(role) ?? false,
  generateDeviceId: (): string => `${Math.random().toString(36).slice(2)}-${Date.now()}`,
};

class AuthEventBus { private handlers = new Set<(e: AuthEvent) => void>(); on(h: (e: AuthEvent) => void): () => void { this.handlers.add(h); return () => this.handlers.delete(h); } emit(e: AuthEvent): void { this.handlers.forEach((h) => { try { h(e); } catch {} }); } }
export const authEvents = new AuthEventBus();
