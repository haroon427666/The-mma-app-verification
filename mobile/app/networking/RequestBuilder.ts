/** Request Builder — fluent API for constructing requests */
import { AxiosRequestConfig } from 'axios';
import type { HttpMethod, RequestConfig } from './NetworkTypes';
import { generateRequestId } from './NetworkUtils';

export class RequestBuilder {
  private config: RequestConfig;

  constructor(url: string, method: HttpMethod = 'GET') {
    this.config = { method, url, headers: { 'Content-Type': 'application/json' } };
  }

  withHeaders(headers: Record<string, string>): this { Object.assign(this.config.headers, headers); return this; }
  withParams(params: Record<string, string>): this { this.config.params = params; return this; }
  withBody(data: any): this { this.config.data = data; return this; }
  withTimeout(ms: number): this { this.config.timeout = ms; return this; }
  withCache(strategy: 'memory' | 'persistent', ttl?: number): this { this.config.cacheStrategy = strategy; this.config.ttl = ttl; return this; }
  offline(): this { this.config.offline = true; return this; }
  withDedupKey(key: string): this { this.config.dedupKey = key; return this; }
  build(): { config: RequestConfig; axiosConfig: AxiosRequestConfig } {
    const { method, url, headers, params, data, timeout } = this.config;
    return { config: this.config, axiosConfig: { method, url, headers, params, data, timeout } };
  }
}
