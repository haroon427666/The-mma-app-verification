/** Request Deduplicator — prevent duplicate in-flight requests */
const inFlight = new Map<string, Promise<any>>();

export const requestDeduplicator = {
  get(key: string): Promise<any> | undefined { return inFlight.get(key); },
  set(key: string, promise: Promise<any>): void {
    inFlight.set(key, promise);
    promise.finally(() => { if (inFlight.get(key) === promise) inFlight.delete(key); });
  },
  cancel(key: string): void { inFlight.delete(key); },
  clear(): void { inFlight.clear(); },
  size(): number { return inFlight.size; },
};
