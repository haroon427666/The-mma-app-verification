/** Production Error System — typed errors, global mapper, React Query integration.

Replaces all bare try/catch and generic "Something went wrong" messages.
Every feature imports from here for consistent error handling.
*/

import { QueryClient } from '@tanstack/react-query';

// ═══════════════════════════════════════════════════════════════════════════
// Error Hierarchy
// ═══════════════════════════════════════════════════════════════════════════

export class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number,
    public retryable: boolean = false,
    public originalError?: unknown,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NetworkError extends AppError {
  constructor(message = 'Network connection lost', originalError?: unknown) {
    super(message, 'NETWORK_ERROR', 0, true, originalError);
    this.name = 'NetworkError';
  }
}

export class TimeoutError extends AppError {
  constructor(message = 'Request timed out', originalError?: unknown) {
    super(message, 'TIMEOUT', 408, true, originalError);
    this.name = 'TimeoutError';
  }
}

export class ValidationError extends AppError {
  public field: string | undefined;
  constructor(message: string, field?: string, originalError?: unknown) {
    super(message, 'VALIDATION_ERROR', 422, false, originalError);
    this.field = field;
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message = 'Please log in again', originalError?: unknown) {
    super(message, 'AUTH_ERROR', 401, false, originalError);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message = 'Access denied', originalError?: unknown) {
    super(message, 'FORBIDDEN', 403, false, originalError);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(entity: string, id?: string, originalError?: unknown) {
    super(`${entity} not found${id ? `: ${id}` : ''}`, 'NOT_FOUND', 404, false, originalError);
    this.name = 'NotFoundError';
  }
}

export class RateLimitError extends AppError {
  public retryAfter: number;
  constructor(retryAfter = 60, originalError?: unknown) {
    super(`Rate limited — retry after ${retryAfter}s`, 'RATE_LIMIT', 429, true, originalError);
    this.retryAfter = retryAfter;
    this.name = 'RateLimitError';
  }
}

export class ServerError extends AppError {
  constructor(message = 'Server error — please try again', originalError?: unknown) {
    super(message, 'SERVER_ERROR', 500, true, originalError);
    this.name = 'ServerError';
  }
}

export class CancelledError extends AppError {
  constructor(originalError?: unknown) {
    super('Request cancelled', 'CANCELLED', 0, false, originalError);
    this.name = 'CancelledError';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Global Error Mapper — Axios error → typed AppError
// ═══════════════════════════════════════════════════════════════════════════

export function mapApiError(error: unknown): AppError {
  if (error instanceof AppError) return error;
  if (error instanceof DOMException && error.name === 'AbortError') {
    return new CancelledError(error);
  }
  
  const anyErr = error as any;
  const status = anyErr?.response?.status;
  const data = anyErr?.response?.data;
  const message = data?.detail || data?.error || anyErr?.message || 'Unknown error';

  if (anyErr?.code === 'ECONNABORTED') return new TimeoutError(undefined, error);
  if (anyErr?.code === 'ERR_NETWORK' || anyErr?.message?.includes('Network')) {
    return new NetworkError(undefined, error);
  }
  if (!status && !anyErr?.response) return new NetworkError('Unable to reach server', error);

  switch (status) {
    case 400: return new ValidationError(message, data?.field, error);
    case 401: return new AuthenticationError(message, error);
    case 403: return new AuthorizationError(message, error);
    case 404: return new NotFoundError('Resource', '', error);
    case 422: return new ValidationError(message, data?.field, error);
    case 429:
      const retryAfter = parseInt(anyErr?.response?.headers?.['retry-after'] || '60', 10);
      return new RateLimitError(retryAfter, error);
    case 502:
    case 503:
      return new ServerError('Service temporarily unavailable', error);
    default:
      if (status && status >= 500) return new ServerError(message, error);
      return new AppError(message, 'UNKNOWN', status || 0, false, error);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// React Query Integration — global onError handler
// ═══════════════════════════════════════════════════════════════════════════

export function configureQueryErrorHandler(queryClient: QueryClient) {
  queryClient.setDefaultOptions({
    queries: { retry: (failureCount, error) => mapApiError(error).retryable && failureCount < 3, retryDelay: (attempt) => Math.min(1000 * 2 ** attempt, 30000), },
    mutations: { onError: (error) => { const mapped = mapApiError(error); if (mapped instanceof AuthenticationError) { import('@/stores/auth').then(m => m.useAuthStore.getState().logout?.()); } }, },
  });
}

// ═══════════════════════════════════════════════════════════════════════════
// User-Facing Messages
// ═══════════════════════════════════════════════════════════════════════════

export const USER_MESSAGES: Record<string, (e: AppError) => string> = {
  NETWORK_ERROR: () => 'No internet connection',
  TIMEOUT: () => 'Request timed out — please try again',
  AUTH_ERROR: () => 'Session expired — please log in again',
  FORBIDDEN: () => 'You don\'t have permission to do this',
  NOT_FOUND: (e) => e.message,
  RATE_LIMIT: (e) => `Too many requests — wait ${(e as RateLimitError).retryAfter}s`,
  SERVER_ERROR: () => 'Something went wrong — we\'re on it',
  VALIDATION_ERROR: (e) => e.message,
  CANCELLED: () => '',
  UNKNOWN: () => 'Something went wrong',
};

export function getUserMessage(error: unknown): string {
  const e = mapApiError(error);
  const formatter = USER_MESSAGES[e.code] || USER_MESSAGES.UNKNOWN;
  return formatter(e) || 'Something went wrong';
}
