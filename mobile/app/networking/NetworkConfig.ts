/** Networking Config */
import { NetworkConfig } from './NetworkTypes';

export const defaultNetworkConfig: NetworkConfig = {
  baseURL: process.env.EXPO_PUBLIC_API_URL || 'https://api.mma-app.com',
  timeout: 15000, retryMaxAttempts: 3, retryBackoffMs: 1000,
  retryJitter: true, enableOfflineQueue: true, enableRequestDedup: true,
  enableCircuitBreaker: true, circuitBreakerThreshold: 5,
  circuitBreakerResetMs: 30000, rateLimitRpm: 60, rateLimitBurst: 10,
};

let overrides: Partial<NetworkConfig> = {};
export const networkConfig = {
  get: (): NetworkConfig => ({ ...defaultNetworkConfig, ...overrides }),
  update: (partial: Partial<NetworkConfig>) => { overrides = { ...overrides, ...partial }; },
};
