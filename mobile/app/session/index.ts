/** Session Platform — barrel export */
export { SessionManager, sessionManager, IdleDetector, idleDetector, ActivityTracker, activityTracker, LifecycleObserver, lifecycleObserver, useSessionStore } from './SessionManager';
export { DeviceManager, deviceManager, SessionPersistence, sessionPersistence, SessionValidator, sessionValidator, SessionExpiration, sessionExpiration, SessionCleanup, sessionCleanup, HeartbeatScheduler, heartbeatScheduler, SessionAnalytics, sessionAnalytics, SessionMetricsCollector, sessionMetrics } from './SessionDevice';
export { useSession, useSessionTimeout, useIdle, useAppLifecycle, useActiveDevices, useHeartbeat } from './SessionHooks';
export { sessionConfig, SESSION_CONSTANTS, SessionLogger, sessionLogger, sessionEvents, sessionUtils } from './SessionTypes';
export type { SessionState, AppState, SessionEventType, SessionConfig, SessionData, SessionEvent, SessionMetrics, DeviceInfo } from './SessionTypes';
export { SessionExpiredError, IdleTimeoutError, HeartbeatError, DeviceError, LifecycleError } from './SessionTypes';
