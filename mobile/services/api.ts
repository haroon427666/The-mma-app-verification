/** Axios API client with interceptors, retry, and token refresh */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/auth';
import { useConnectivityStore } from '@/stores/connectivity';
import type { ApiError, AuthTokens } from '@/types';

const BASE_URL = __DEV__
  ? 'http://localhost:8000/api'
  : 'https://api.mma-platform.com/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Request interceptor — attach token + request ID ──────────────────

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = useAuthStore.getState().tokens;
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`;
  }
  config.headers['X-Request-ID'] = `mob_${Date.now().toString(36)}`;
  return config;
});

// ── Response interceptor — token refresh on 401 ─────────────────────

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token!);
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const tokens = useAuthStore.getState().tokens;
        if (!tokens?.refreshToken) throw new Error('No refresh token');

        const { data } = await axios.post<AuthTokens>(
          `${BASE_URL}/v1/auth/refresh`,
          { refresh_token: tokens.refreshToken },
        );

        useAuthStore.getState().setTokens(data);
        processQueue(null, data.accessToken);
        originalRequest.headers.Authorization = `Bearer ${data.accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Offline detection
    if (!error.response) {
      useConnectivityStore.getState().setStatus('offline');
    }

    return Promise.reject(error);
  },
);

export default api;
export const API_BASE = BASE_URL;
