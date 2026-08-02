# Networking — README + Architecture

## Architecture
```
Feature Repository → useRequest (hook) → CircuitBreaker → RateLimiter → Axios → Backend
                                           ↓ (offline)
                                      OfflineQueue → replay when online
```

## Key Classes
| Module | Purpose |
|---|---|
| AxiosClient | Central HTTP instance with config |
| RequestBuilder | Fluent API for request construction |
| AuthInterceptor | Token injection + 401 handling |
| RetryPolicy | Exponential backoff with jitter |
| CircuitBreaker | Failure detection + auto-recovery |
| RateLimiter | Token bucket rate limiting |
| OfflineQueue | Queue mutations when offline |
| RequestDeduplicator | Prevent duplicate in-flight requests |
| ETagCache | Conditional request caching |
| WebSocketManager | Real-time connections with heartbeat |
| NetworkMonitor | Connectivity state tracking |
| NetworkLogger | Structured request logging |
| NetworkAnalytics | Success rate, duration, cache hit stats |

## Usage
```ts
const { execute, loading } = useRequest();
const data = await execute(
  new RequestBuilder('/v1/fighters', 'GET')
    .withParams({ weight_class: 'Heavyweight' })
    .withCache('memory', 60000)
);
```
