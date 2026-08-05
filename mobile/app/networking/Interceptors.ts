/** Interceptors — Logging, Cache, Error, Response */
import { AxiosInstance } from 'axios';
import { RateLimitError, APIError } from './NetworkTypes';

export class LoggingInterceptor {
  attach(instance: AxiosInstance): void {
    if (!__DEV__) return;
    instance.interceptors.request.use((c) => { console.log(`[HTTP] ${c.method?.toUpperCase()} ${c.url}`); return c; });
    instance.interceptors.response.use(
      (r) => { console.log(`[HTTP] ${r.status} ${r.config.url} ${r.headers['x-response-time'] || ''}`); return r; },
      (e) => { console.warn(`[HTTP] ERROR ${e.config?.url}`, e.message); return Promise.reject(e); },
    );
  }
}

export class ErrorInterceptor {
  attach(instance: AxiosInstance): void {
    instance.interceptors.response.use((r) => r, async (error) => {
      if (!error.response) return Promise.reject(error);
      const { status, data } = error.response;
      // Transform to typed errors
      if (status === 429) return Promise.reject(new RateLimitError());
      if (status >= 500) return Promise.reject(new APIError('Server error', status));
      if (status === 422) return Promise.reject(new APIError('Validation failed', status, data?.code, data?.errors));
      return Promise.reject(error);
    });
  }
}

export class ResponseInterceptor {
  attach(instance: AxiosInstance): void {
    instance.interceptors.response.use((response) => {
      // Standardize response: unwrap envelope if needed
      const data = response.data;
      if (data?.success === false) return Promise.reject(new APIError(data?.message || 'Request failed', response.status));
      return response;
    });
  }
}

import { cacheStore } from './ETagCache';
export class CacheInterceptor {
  attach(instance: AxiosInstance): void {
    instance.interceptors.response.use((response) => {
      const etag = response.headers['etag'];
      if (etag && response.config.url) {
        cacheStore.set(response.config.url, { data: response.data, etag, timestamp: Date.now() });
      }
      return response;
    });
  }
}

export const loggingInterceptor = new LoggingInterceptor();
export const errorInterceptor = new ErrorInterceptor();
export const responseInterceptor = new ResponseInterceptor();
export const cacheInterceptor = new CacheInterceptor();
