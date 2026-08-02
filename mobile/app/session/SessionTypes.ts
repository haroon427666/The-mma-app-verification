/** Session Types, Config, Constants, Errors, Logger, Events, Utils */
export type SessionState = 'active' | 'background' | 'inactive' | 'expired' | 'terminated';
export type AppState = 'active' | 'background' | 'inactive' | 'unknown';
export type SessionEventType = 'created' | 'restored' | 'expired' | 'timeout' | 'heartbeat' | 'background' | 'foreground' | 'terminated' | 'error';

export interface SessionConfig {
  idleTimeoutMs: number; sessionTimeoutMs: number; warningBeforeMs: number;
  heartbeatIntervalMs: number; maxHeartbeatFailures: number;
  enableIdleDetection: boolean; enableBackgroundSync: boolean;
  maxActiveDevices: number;
}

export interface SessionData {
  id: string; deviceId: string; createdAt: number; lastActivityAt: number;
  expiresAt: number; state: SessionState; metadata: Record<string, string>;
}

export interface SessionEvent { type: SessionEventType; timestamp: number; details?: any; }
export interface SessionMetrics {
  totalSessions: number; avgDurationMs: number; idleTimeouts: number;
  sessionExpirations: number; heartbeatLatencyMs: number; recoveries: number;
}

export interface DeviceInfo { id: string; name: string; os: string; platform: string; lastSeen: number; current: boolean; trusted: boolean; location?: string; }

export class SessionExpiredError extends Error { constructor() { super('Session expired'); this.name = 'SessionExpiredError'; } }
export class IdleTimeoutError extends Error { constructor() { super('User idle timeout'); this.name = 'IdleTimeoutError'; } }
export class HeartbeatError extends Error { constructor() { super('Heartbeat failed'); this.name = 'HeartbeatError'; } }
export class DeviceError extends Error { constructor(m: string) { super(m); this.name = 'DeviceError'; } }
export class LifecycleError extends Error { constructor(m: string) { super(m); this.name = 'LifecycleError'; } }

export const defaultSessionConfig: SessionConfig = {
  idleTimeoutMs: 15 * 60 * 1000, sessionTimeoutMs: 60 * 60 * 1000,
  warningBeforeMs: 60 * 1000, heartbeatIntervalMs: 30 * 1000,
  maxHeartbeatFailures: 3, enableIdleDetection: true,
  enableBackgroundSync: true, maxActiveDevices: 5,
};

let overrides: Partial<SessionConfig> = {};
export const sessionConfig = {
  get: (): SessionConfig => ({ ...defaultSessionConfig, ...overrides }),
  update: (p: Partial<SessionConfig>) => { overrides = { ...overrides, ...p }; },
};

export const SESSION_CONSTANTS = {
  IDLE_EVENTS: ['touch', 'scroll', 'keypress', 'navigation'] as const,
  APP_STATES: ['active', 'background', 'inactive'] as const,
  HEARTBEAT: { PING: 'ping', PONG: 'pong', TIMEOUT: 5000 },
} as const;

export class SessionLogger { private p = '[Session]'; info(m: string) { console.log(`${this.p} ${m}`); } warn(m: string) { console.warn(`${this.p} ${m}`); } error(m: string, e?: Error) { console.error(`${this.p} ${m}`, e?.message ?? ''); } }
export const sessionLogger = new SessionLogger();

class SessionEventBus { private h = new Set<(e: SessionEvent) => void>(); on(h: (e: SessionEvent) => void): () => void { this.h.add(h); return () => this.h.delete(h); } emit(e: SessionEvent): void { this.h.forEach((f) => { try { f(e); } catch {} }); } }
export const sessionEvents = new SessionEventBus();

export const sessionUtils = {
  generateSessionId: (): string => `sess-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
  generateDeviceId: (): string => `dev-${Math.random().toString(36).slice(2, 10)}`,
  isExpired: (expiresAt: number): boolean => Date.now() >= expiresAt,
  getIdleDuration: (lastActivity: number): number => Date.now() - lastActivity,
};
