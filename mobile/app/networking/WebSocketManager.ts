/** WebSocket Manager — connection, reconnection, heartbeat, subscriptions */
import type { WebSocketMessage } from './NetworkTypes';

type MessageHandler = (msg: WebSocketMessage) => void;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private url: string = '';
  private handlers = new Map<string, Set<MessageHandler>>();
  private reconnectTimer: any = null;
  private heartbeatTimer: any = null;
  private connected = false;

  connect(url: string, token?: string): void {
    this.url = url;
    this.createConnection(token);
  }

  private createConnection(token?: string): void {
    try {
      const wsUrl = token ? `${this.url}?token=${token}` : this.url;
      this.ws = new WebSocket(wsUrl);
      this.ws.onopen = () => { this.connected = true; this.startHeartbeat(); };
      this.ws.onmessage = (event) => { try { const msg: WebSocketMessage = JSON.parse(event.data); this.handlers.get(msg.type)?.forEach((h) => h(msg)); } catch {} };
      this.ws.onclose = () => { this.connected = false; this.scheduleReconnect(); };
      this.ws.onerror = () => {};
    } catch {}
  }

  subscribe(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  send(type: string, payload: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify({ type, payload, timestamp: Date.now() }));
  }

  private startHeartbeat(): void { this.heartbeatTimer = setInterval(() => this.send('ping', {}), 30000); }
  private scheduleReconnect(): void { clearTimeout(this.reconnectTimer); this.reconnectTimer = setTimeout(() => this.createConnection(), 3000); }

  disconnect(): void { clearTimeout(this.reconnectTimer); clearInterval(this.heartbeatTimer); this.ws?.close(); this.handlers.clear(); }
  get isConnected(): boolean { return this.connected; }
}
export const wsManager = new WebSocketManager();
