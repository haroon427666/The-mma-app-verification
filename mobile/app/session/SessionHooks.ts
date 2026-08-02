/** Session Hooks — useSession, useSessionTimeout, useIdle, useAppLifecycle, useActiveDevices, useHeartbeat */
import { useState, useEffect, useCallback } from 'react';
import { useSessionStore, sessionManager, idleDetector, lifecycleObserver, activityTracker } from './SessionManager';
import { heartbeatScheduler } from './SessionDevice';
import { deviceManager } from './SessionDevice';
import { sessionConfig } from './SessionTypes';
import type { DeviceInfo } from './SessionTypes';

export function useSession() {
  const { active, expired, idle, background, foreground, lastActivity, sessionId } = useSessionStore();
  return { isActive: active, isExpired: expired, isIdle: idle, isBackground: background, isForeground: foreground, lastActivity, sessionId, terminate: () => sessionManager.terminate(), refresh: () => sessionManager.updateActivity() };
}

export function useSessionTimeout() {
  const [warning, setWarning] = useState(false);
  const [timeLeft, setTimeLeft] = useState<number | null>(null);
  const extend = useCallback(() => { setWarning(false); setTimeLeft(null); }, []);
  return { warning, timeLeft, extend };
}

export function useIdle(thresholdMs?: number) {
  const { idle, lastActivity } = useSessionStore();
  const idleTime = Date.now() - lastActivity;
  const isIdle = idle || idleTime > (thresholdMs ?? sessionConfig.get().idleTimeoutMs);
  return { isIdle, idleTimeMs: idleTime, onActivity: () => activityTracker.notify() };
}

export function useAppLifecycle() {
  const { foreground, background, appState } = useSessionStore();
  return { isForeground: foreground, isBackground: background, appState };
}

export function useActiveDevices() {
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const refresh = useCallback(() => { setDevices(deviceManager.getDevices()); }, []);
  const remove = useCallback((id: string) => { deviceManager.removeDevice(id); refresh(); }, []);
  return { devices, refresh, remove };
}

export function useHeartbeat() {
  const [latency, setLatency] = useState<number | null>(null);
  const { heartbeatFailures } = useSessionStore();
  const ping = useCallback(async () => {
    const start = Date.now();
    await new Promise((r) => setTimeout(r, 50)); // Simulated heartbeat
    setLatency(Date.now() - start);
    return Date.now() - start;
  }, []);
  return { ping, latency, failures: heartbeatFailures, isConnected: heartbeatFailures < 3 };
}
