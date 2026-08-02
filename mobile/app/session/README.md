/** Session Platform — README + Architecture + Lifecycle + Heartbeat + Device Management + Testing + Migration */

/*
## Session Management Platform — Architecture

### Flow
```
AppBootstrap (Stage 5: auth)
  → SessionManager.create()
  → IdleDetector.start()
  → HeartbeatScheduler.start()
  → LifecycleObserver.initialize()
```

### App Lifecycle
```
Foreground → IdleDetector active, Heartbeat active
Background  → IdleDetector paused, Heartbeat paused, persist state
Foreground → IdleDetector resumed, Heartbeat resumed, validate session
```

### Idle Detection
```
15 min no activity → idleTimeout → session expired
Activity event → ActivityTracker.notify() → reset timer
```

### Heartbeat
```
30s interval → ping server → success (reset failures)
                         → failure → increment → max (3) → session expired
```

### Device Management
```
deviceManager.getCurrent() → { id, name: 'iPhone', os: 'iOS 18', ... }
deviceManager.addDevice(device)
deviceManager.removeDevice(id)
deviceManager.getDevices() → DeviceInfo[]
```

### Hooks
- `useSession()` → isActive, isExpired, isIdle, terminate, refresh
- `useIdle(thresholdMs?)` → isIdle, idleTimeMs, onActivity
- `useAppLifecycle()` → isForeground, isBackground, appState
- `useActiveDevices()` → devices, refresh, remove
- `useHeartbeat()` → ping, latency, failures, isConnected
- `useSessionTimeout()` → warning, timeLeft, extend

### Testing
```ts
it('detects idle state', () => { expect(sessionManager.getSession()).toBeNull(); });
it('handles app state changes', () => { lifecycleObserver.initialize(); });
it('schedules heartbeats', () => { heartbeatScheduler.start(); heartbeatScheduler.stop(); });
```
*/

export * from './SessionTypes';
export * from './SessionManager';
export * from './SessionDevice';
export * from './SessionHooks';
