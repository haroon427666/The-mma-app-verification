/** Dependency Container — register and resolve all application dependencies */
export class DependencyContainer {
  private registry = new Map<string | symbol, any>();
  private factories = new Map<string | symbol, (c: DependencyContainer) => any>();

  register<T>(token: string | symbol, instance: T): void { this.registry.set(token, instance); }
  registerFactory<T>(token: string | symbol, factory: (c: DependencyContainer) => T): void { this.factories.set(token, factory); }
  resolve<T>(token: string | symbol): T | undefined { return this.registry.get(token) ?? this.factories.get(token)?.(this); }
  has(token: string | symbol): boolean { return this.registry.has(token) || this.factories.has(token); }
}
export const container = new DependencyContainer();

export const DI_TOKENS = {
  API_CLIENT: Symbol('apiClient'), QUERY_CLIENT: Symbol('queryClient'),
  AUTH_SERVICE: Symbol('authService'), STORAGE: Symbol('storage'),
  ENCRYPTED_STORAGE: Symbol('encryptedStorage'), CACHE: Symbol('cache'),
  ANALYTICS: Symbol('analytics'), NOTIFICATIONS: Symbol('notifications'),
  DEEP_LINKS: Symbol('deepLinks'), REMOTE_CONFIG: Symbol('remoteConfig'),
  NETWORK_MONITOR: Symbol('networkMonitor'), LOGGER: Symbol('logger'),
} as const;
