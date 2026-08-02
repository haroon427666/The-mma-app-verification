/** Connectivity — network state detection with React hook */
import { useEffect, useState, useCallback } from 'react';
import type { ConnectionState, ConnectionType } from './OfflineTypes';
import { useOfflineStore } from './OfflineManager';

class ConnectivityService {
  private state: ConnectionState = 'online';
  private type: ConnectionType = 'wifi';
  private listeners = new Set<(s: ConnectionState) => void>();

  getState(): ConnectionState { return this.state; }
  getType(): ConnectionType { return this.type; }
  get isOnline(): boolean { return this.state === 'online'; }

  subscribe(fn: (s: ConnectionState) => void): () => void { this.listeners.add(fn); return () => this.listeners.delete(fn); }

  update(state: ConnectionState, type?: ConnectionType): void {
    this.state = state; if (type) this.type = type;
    useOfflineStore.getState().setConnection(state);
    this.listeners.forEach((f) => f(state));
  }

  onReconnect(fn: () => void): () => void {
    const handler = (s: ConnectionState) => { if (s === 'online') fn(); };
    return this.subscribe(handler);
  }
}
export const connectivity = new ConnectivityService();

export function useConnectivity() {
  const [state, setState] = useState<ConnectionState>(connectivity.getState());
  useEffect(() => connectivity.subscribe(setState), []);
  return { isOnline: state === 'online', connectionState: state, connectionType: connectivity.getType() };
}
