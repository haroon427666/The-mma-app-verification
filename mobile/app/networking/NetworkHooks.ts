/** Networking Hooks — useRequest, useUpload, useDownload, useRequestQueue */
import { useState, useCallback, useRef, useEffect } from 'react';
import { axiosInstance } from './AxiosClient';
import { RequestBuilder } from './RequestBuilder';
import { requestDeduplicator } from './RequestDeduplicator';
import { offlineQueue } from './OfflineQueue';
import { networkMonitor } from './NetworkMonitor';
import { rateLimiter } from './RateLimiter';
import { circuitBreaker } from './CircuitBreaker';
import { networkLogger } from './NetworkLogger';
import { networkAnalytics } from './NetworkAnalytics';
import { trackRequestMetrics } from './AxiosClient';
import type { RequestMetrics, UploadProgress, DownloadProgress } from './NetworkTypes';

export function useRequest() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const execute = useCallback(async <T>(builder: RequestBuilder): Promise<T> => {
    setLoading(true); setError(null);
    const { config, axiosConfig } = builder.build();
    const start = Date.now();
    try {
      const dedupKey = config.dedupKey || `${config.method}:${config.url}`;
      if (config.dedupKey) {
        const existing = requestDeduplicator.get(dedupKey);
        if (existing) return existing as T;
      }
      if (!networkMonitor.isOnline && config.offline !== true) {
        return offlineQueue.enqueue(dedupKey, async () => {
          await rateLimiter.acquire();
          const res = await circuitBreaker.call(() => axiosInstance(axiosConfig));
          return res.data;
        });
      }
      await rateLimiter.acquire();
      const response = await circuitBreaker.call(() => axiosInstance(axiosConfig));
      const metrics = trackRequestMetrics(config, start, response);
      networkLogger.log(config.method, config.url, response.status, metrics.durationMs);
      networkAnalytics.record(metrics);
      return response.data;
    } catch (err) {
      const error = err as Error;
      setError(error);
      networkLogger.log(config.method, config.url, undefined, Date.now() - start, error.message);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return { execute, loading, error };
}

export function useUpload() {
  const [progress, setProgress] = useState<UploadProgress>({ loaded: 0, total: 0, percentage: 0 });
  const [loading, setLoading] = useState(false);

  const upload = useCallback(async (url: string, formData: FormData, onProgress?: (p: UploadProgress) => void): Promise<any> => {
    setLoading(true);
    const start = Date.now();
    try {
      const response = await axiosInstance.post(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          const p = { loaded: e.loaded ?? 0, total: e.total ?? 0, percentage: e.total ? (e.loaded ?? 0) / e.total : 0 };
          setProgress(p); onProgress?.(p);
        },
      });
      return response.data;
    } finally { setLoading(false); }
  }, []);

  return { upload, progress, loading };
}

export function useDownload() {
  const [progress, setProgress] = useState<DownloadProgress>({ loaded: 0, total: 0, percentage: 0, speed: 0 });
  const [loading, setLoading] = useState(false);

  const download = useCallback(async (url: string, onProgress?: (p: DownloadProgress) => void): Promise<any> => {
    setLoading(true);
    try {
      const response = await axiosInstance.get(url, { responseType: 'blob', onDownloadProgress: (e) => {
        const p = { loaded: e.loaded ?? 0, total: e.total ?? 0, percentage: e.total ? (e.loaded ?? 0) / e.total : 0, speed: 0 };
        setProgress(p); onProgress?.(p);
      }});
      return response.data;
    } finally { setLoading(false); }
  }, []);

  return { download, progress, loading };
}

export function useRequestQueue() {
  const [queueLength, setQueueLength] = useState(offlineQueue.length);
  useEffect(() => { const iv = setInterval(() => setQueueLength(offlineQueue.length), 1000); return () => clearInterval(iv); }, []);
  return { queueLength, clearQueue: () => offlineQueue.clear() };
}
