/** Live Fight WebSocket — real-time fight updates, no polling needed */

type FightUpdateHandler = (data: FightUpdate) => void;
type ConnectionHandler = (connected: boolean) => void;

interface FightUpdate {
  type: 'fight_start' | 'round_change' | 'fight_end' | 'score_update';
  fightId: string;
  eventId: string;
  data: Record<string, unknown>;
}

const WS_BASE = __DEV__ ? 'ws://localhost:8000/ws' : 'wss://api.mma-platform.com/ws';

class LiveFightSocket {
  private ws: WebSocket | null = null;
  private fightHandlers = new Map<string, Set<FightUpdateHandler>>();
  private connectionHandlers = new Set<ConnectionHandler>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private eventId: string | null = null;

  connect(eventId: string, token: string) {
    this.eventId = eventId;
    this.disconnect();

    this.ws = new WebSocket(`${WS_BASE}/events/${eventId}/live?token=${token}`);
    this.ws.onopen = () => this.connectionHandlers.forEach((h) => h(true));
    this.ws.onclose = () => {
      this.connectionHandlers.forEach((h) => h(false));
      this.scheduleReconnect();
    };
    this.ws.onmessage = (event) => {
      const update: FightUpdate = JSON.parse(event.data);
      const fightHandlers = this.fightHandlers.get(update.fightId);
      fightHandlers?.forEach((h) => h(update));
    };
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
  }

  onFightUpdate(fightId: string, handler: FightUpdateHandler) {
    if (!this.fightHandlers.has(fightId)) this.fightHandlers.set(fightId, new Set());
    this.fightHandlers.get(fightId)!.add(handler);
    return () => { this.fightHandlers.get(fightId)?.delete(handler); };
  }

  onConnectionChange(handler: ConnectionHandler) {
    this.connectionHandlers.add(handler);
    return () => { this.connectionHandlers.delete(handler); };
  }

  private scheduleReconnect() {
    this.reconnectTimer = setTimeout(() => {
      if (this.eventId) this.connect(this.eventId, '');
    }, 5000);
  }
}

export const liveFightSocket = new LiveFightSocket();
