/** Session Store + Manager + Timeout + Idle + Activity + Lifecycle */
import { useState, useEffect, useCallback, useRef } from 'react';
import { create } from 'zustand';
import { AppState, AppStateStatus } from 'react-native';
import type { SessionState, AppState as AppStateEnum, SessionData, SessionEventType } from './SessionTypes';
import { sessionConfig, sessionLogger, sessionEvents, sessionUtils, SessionExpiredError, IdleTimeoutError, SESSION_CONSTANTS } from './SessionTypes';

// ── Store ──
interface SessionStore {
  active: boolean; expired: boolean; idle: boolean; background: boolean; foreground: boolean;
  lastActivity: number; sessionId: string | null; deviceId: string | null;
  heartbeatFailures: number; appState: AppStateEnum;
}

export const useSessionStore = create<SessionStore>(() => ({
  active: false, expired: false, idle: false, background: false, foreground: true,
  lastActivity: Date.now(), sessionId: null, deviceId: null,
  heartbeatFailures: 0, appState: 'active',
}));

// ── Manager ──
export class SessionManager {
  private session: SessionData | null = null;
  private log = sessionLogger;

  create(): SessionData {
    const deviceId = sessionUtils.generateDeviceId();
    const now = Date.now();
    this.session = { id: sessionUtils.generateSessionId(), deviceId, createdAt: now, lastActivityAt: now, expiresAt: now + sessionConfig.get().sessionTimeoutMs, state: 'active', metadata: {} };
    useSessionStore.setState({ active: true, sessionId: this.session.id, deviceId, lastActivity: now, foreground: true });
    sessionEvents.emit({ type: 'created', timestamp: now });
    this.log.info('Session created');
    return this.session;
  }

  getSession(): SessionData | null { return this.session; }

  updateActivity(): void {
    if (!this.session) return;
    const now = Date.now();
    this.session.lastActivityAt = now;
    useSessionStore.setState({ lastActivity: now, idle: false });
  }

  expire(): void {
    if (!this.session) return;
    this.session.state = 'expired';
    useSessionStore.setState({ active: false, expired: true });
    sessionEvents.emit({ type: 'expired', timestamp: Date.now() });
    this.log.info('Session expired');
  }

  terminate(): void {
    this.session = null;
    useSessionStore.setState({ active: false, expired: false, sessionId: null });
    sessionEvents.emit({ type: 'terminated', timestamp: Date.now() });
    this.log.info('Session terminated');
  }
}
export const sessionManager = new SessionManager();

// ── Idle Detector ──
export class IdleDetector {
  private lastActivity = Date.now();
  private timer: any = null;
  private log = sessionLogger;

  start(): void {
    const cfg = sessionConfig.get();
    this.lastActivity = Date.now();
    this.timer = setInterval(() => {
      const idleMs = Date.now() - this.lastActivity;
      if (idleMs >= cfg.idleTimeoutMs) {
        useSessionStore.setState({ idle: true, expired: true, active: false });
        sessionEvents.emit({ type: 'timeout', timestamp: Date.now() });
        this.log.info('Idle timeout reached');
      }
    }, 5000);
  }

  onActivity(): void { this.lastActivity = Date.now(); }
  stop(): void { if (this.timer) { clearInterval(this.timer); this.timer = null; } }
}
export const idleDetector = new IdleDetector();

// ── Activity Tracker ──
export class ActivityTracker {
  private handlers = new Set<() => void>();
  track(fn: () => void): () => void { this.handlers.add(fn); return () => this.handlers.delete(fn); }
  notify(): void { idleDetector.onActivity(); sessionManager.updateActivity(); this.handlers.forEach((f) => f()); }
}
export const activityTracker = new ActivityTracker();

// ── Lifecycle Observer ──
export class LifecycleObserver {
  private log = sessionLogger;
  private currentState: AppStateStatus = 'active';

  initialize(): void {
    AppState.addEventListener('change', this.handleChange);
  }

  private handleChange = (state: AppStateStatus): void => {
    this.currentState = state;
    const store = useSessionStore.getState();
    if (state === 'active') {
      useSessionStore.setState({ foreground: true, background: false, appState: 'active' });
      sessionEvents.emit({ type: 'foreground', timestamp: Date.now() });
      idleDetector.start();
    } else if (state === 'background') {
      useSessionStore.setState({ foreground: false, background: true, appState: 'background' });
      sessionEvents.emit({ type: 'background', timestamp: Date.now() });
      idleDetector.stop();
    }
    this.log.info(`App state: ${state}`);
  };

  getCurrentState(): AppStateStatus { return this.currentState; }
  isForeground(): boolean { return this.currentState === 'active'; }
  destroy(): void { idleDetector.stop(); }
}
export const lifecycleObserver = new LifecycleObserver();
