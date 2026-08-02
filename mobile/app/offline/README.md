# Offline Platform — README + Architecture

## Architecture
```
Feature Module
  → useOffline() / useSync() (hooks)
  → OfflineManager (queue mutations)
  → QueueManager (persistent mutation queue)
  → SyncEngine (on reconnect: replay queue, fetch fresh data)
  → ConflictResolver (LWW, server wins, client wins, merge)
  → RetryManager (exponential backoff)
```

## Key Classes
| Class | Purpose |
|---|---|
| OfflineManager | Central orchestrator: enqueue/dequeue mutations, store state |
| QueueManager | Persistent mutation queue with serialize/deserialize |
| SyncEngine | Incremental/full/background/foreground sync |
| ConflictResolver | 5 resolution strategies (LWW, server, client, merge, manual) |
| Connectivity | Network state detection with onReconnect callback |
| RetryManager | Exponential backoff with jitter |

## Hooks
- `useOffline()` → isOffline, connectionState, syncStatus, queueSize
- `useConnectivity()` → isOnline, connectionState, connectionType
- `useSync()` → syncStatus, syncProgress, lastSync
- `useQueue()` → queueSize, clearQueue
- `usePendingMutations()` → pendingMutations count

## Conflict Strategies
| Strategy | Behavior |
|---|---|
| last_write_wins | Higher version number wins |
| server_wins | Server always authoritative |
| client_wins | Client always authoritative |
| merge | Deep merge arrays + objects |
| manual | Returns both versions for UI resolution |

## Usage
```tsx
import { useOffline, useSync, offlineManager } from '@/app/offline';

function MyScreen() {
  const { isOffline } = useOffline();
  const { syncStatus } = useSync();

  const handleSave = (data) => {
    if (isOffline) {
      offlineManager.enqueue({ type: 'update', endpoint: '/v1/me', payload: data });
    } else {
      // normal API call
    }
  };
}
```
