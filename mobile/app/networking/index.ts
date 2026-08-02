/** Networking — Enterprise Master Barrel Export */

// ── Core ──
export { createAxiosInstance, axiosInstance, trackRequestMetrics } from './AxiosClient';
export { RequestBuilder } from './RequestBuilder';
export { networkConfig, defaultNetworkConfig } from './NetworkConfig';

// ── Interceptors ──
export { authInterceptor } from './AuthInterceptor';
export { loggingInterceptor, errorInterceptor, responseInterceptor, cacheInterceptor } from './Interceptors';

// ── Retry + Backoff ──
export { shouldRetry, getRetryDelay } from './RetryPolicy';
export { BackoffStrategy } from './BackoffStrategy';

// ── Cache + Dedup ──
export { cacheStore } from './ETagCache';
export { requestDeduplicator } from './RequestDeduplicator';

// ── Resilience ──
export { circuitBreaker } from './CircuitBreaker';
export { rateLimiter } from './RateLimiter';
export { timeoutManager } from './TimeoutManager';

// ── Offline ──
export { offlineQueue } from './OfflineQueue';

// ── Upload / Download ──
export { uploadManager, downloadManager } from './UploadManager';

// ── Monitoring ──
export { networkMonitor, useNetwork, useConnectivity } from './NetworkMonitor';
export { networkLogger } from './NetworkLogger';
export { networkAnalytics } from './NetworkAnalytics';

// ── WebSocket ──
export { wsManager } from './WebSocketManager';

// ── Hooks ──
export { useRequest, useUpload, useDownload, useRequestQueue } from './NetworkHooks';

// ── Data ──
export { API_ENDPOINTS } from './Endpoints';
export { defaultHeaders, createHeaders, authHeader } from './Headers';
export { Serializer, Parser, Compression } from './Serializer';

// ── HTTP Status ──
export { HttpStatus, NetworkErrorMessages } from './HttpStatus';

// ── Utilities ──
export { generateRequestId, buildRetryDelay, isRetryableStatus, isRetryableError, sanitizeUrl } from './NetworkUtils';
export { CancellationHandler, cancellationHandler } from './BackoffStrategy';

// ── Types ──
export type { HttpMethod, NetworkState, ConnectionType, RetryStrategy, NetworkConfig, RequestConfig, RequestMetrics, UploadProgress, DownloadProgress, WebSocketMessage } from './NetworkTypes';
export { NetworkError, APIError, OfflineError, TimeoutError, RateLimitError } from './NetworkTypes';
