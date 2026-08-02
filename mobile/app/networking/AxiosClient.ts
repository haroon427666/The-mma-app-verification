/** Axios Client — central HTTP instance factory */
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { networkConfig } from './NetworkConfig';
import { generateRequestId } from './NetworkUtils';
import type { RequestConfig, RequestMetrics } from './NetworkTypes';

export function createAxiosInstance(overrides?: Partial<AxiosRequestConfig>): AxiosInstance {
  const cfg = networkConfig.get();
  const instance = axios.create({
    baseURL: cfg.baseURL, timeout: cfg.timeout,
    headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
    ...overrides,
  });
  return instance;
}

export const axiosInstance = createAxiosInstance();

export function trackRequestMetrics(rc: RequestConfig, start: number, response?: AxiosResponse, error?: any): RequestMetrics {
  return {
    url: rc.url, method: rc.method, durationMs: Date.now() - start,
    status: response?.status ?? error?.response?.status ?? 0,
    success: !!response && response.status >= 200 && response.status < 300,
    retryCount: rc.retryCount ?? 0, cached: false, offline: false,
    timestamp: Date.now(),
  };
}
