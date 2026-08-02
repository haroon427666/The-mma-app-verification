/** Networking Types — all type definitions for the networking layer */
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS';
export type NetworkState = 'online' | 'offline' | 'reconnecting';
export type ConnectionType = 'wifi' | 'cellular' | 'ethernet' | 'unknown' | 'none';
export type RetryStrategy = 'exponential' | 'linear' | 'fixed';

export interface NetworkConfig {
  baseURL: string; timeout: number; retryMaxAttempts: number;
  retryBackoffMs: number; retryJitter: boolean; enableOfflineQueue: boolean;
  enableRequestDedup: boolean; enableCircuitBreaker: boolean;
  circuitBreakerThreshold: number; circuitBreakerResetMs: number;
  rateLimitRpm: number; rateLimitBurst: number;
}

export interface RequestConfig {
  method: HttpMethod; url: string; headers: Record<string, string>;
  params?: Record<string, string>; data?: any; timeout?: number;
  retryCount?: number; cacheStrategy?: 'none' | 'memory' | 'persistent';
  ttl?: number; dedupKey?: string; offline?: boolean;
}

export interface RequestMetrics {
  url: string; method: HttpMethod; durationMs: number;
  status: number; success: boolean; retryCount: number;
  cached: boolean; offline: boolean; timestamp: number;
}

export interface UploadProgress { loaded: number; total: number; percentage: number; }
export interface DownloadProgress extends UploadProgress { speed: number; }
export interface WebSocketMessage { type: string; payload: any; timestamp: number; }

export class NetworkError extends Error {
  constructor(message: string, public statusCode?: number, public retryable = false) { super(message); this.name = 'NetworkError'; }
}
export class APIError extends NetworkError {
  constructor(message: string, statusCode: number, public errorCode?: string, public validationErrors?: Record<string, string[]>) { super(message, statusCode, false); this.name = 'APIError'; }
}
export class OfflineError extends NetworkError { constructor(message = 'No network connection') { super(message, undefined, true); this.name = 'OfflineError'; } }
export class TimeoutError extends NetworkError { constructor(url: string, timeoutMs: number) { super(`Request to ${url} timed out after ${timeoutMs}ms`, undefined, true); this.name = 'TimeoutError'; } }
export class RateLimitError extends NetworkError { constructor(retryAfterSeconds = 60) { super(`Rate limited. Retry after ${retryAfterSeconds}s`, 429, true); this.name = 'RateLimitError'; } }
