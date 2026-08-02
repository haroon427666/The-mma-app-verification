/** Network Monitor — tracks connectivity state */
import { useEffect, useState, useCallback } from 'react';
import type { NetworkState, ConnectionType } from './NetworkTypes';

class NetworkMonitorService {
  private listeners = new Set<(s: NetworkState) => void>();
  private _state: NetworkState = 'online';
  private _type: ConnectionType = 'wifi';

  get state(): NetworkState { return this._state; }
  get connectionType(): ConnectionType { return this._type; }
  get isOnline(): boolean { return this._state === 'online'; }

  subscribe(fn: (s: NetworkState) => void): () => void { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  setState(s: NetworkState): void { this._state = s; this.listeners.forEach((fn) => fn(s)); }
  setType(t: ConnectionType): void { this._type = t; }
}
export const networkMonitor = new NetworkMonitorService();

/** React hook */
export function useNetwork() {
  const [state, setState] = useState<NetworkState>(networkMonitor.state);
  useEffect(() => networkMonitor.subscribe(setState), []);
  return { isOnline: state === 'online', state, connectionType: networkMonitor.connectionType };
}

export function useConnectivity() { return useNetwork(); }
