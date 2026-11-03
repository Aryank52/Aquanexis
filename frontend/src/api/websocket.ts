// ============================================================================
// AquaNexis WebSocket Manager — real-time telemetry & alerts
// ============================================================================
import type { WSMessage, WSMessageType } from '@/types/api';
import { getAccessToken } from './client';

type MessageHandler = (message: WSMessage) => void;

interface WSManagerOptions {
  deviceId: string;
  onMessage: MessageHandler;
  onStatusChange?: (status: WSConnectionStatus) => void;
}

export type WSConnectionStatus = 'connecting' | 'connected' | 'reconnecting' | 'disconnected';

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || `ws://${window.location.host}/ws`;
const MAX_RECONNECT_DELAY = 30_000;
const INITIAL_RECONNECT_DELAY = 1_000;
const PING_INTERVAL = 25_000;

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private deviceId: string;
  private onMessage: MessageHandler;
  private onStatusChange?: (status: WSConnectionStatus) => void;
  private reconnectDelay = INITIAL_RECONNECT_DELAY;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private pingTimer: ReturnType<typeof setInterval> | null = null;
  private isDestroyed = false;
  private _status: WSConnectionStatus = 'disconnected';

  constructor(options: WSManagerOptions) {
    this.deviceId = options.deviceId;
    this.onMessage = options.onMessage;
    this.onStatusChange = options.onStatusChange;
  }

  get status(): WSConnectionStatus {
    return this._status;
  }

  private setStatus(status: WSConnectionStatus) {
    this._status = status;
    this.onStatusChange?.(status);
  }

  connect(): void {
    if (this.isDestroyed) return;
    this.cleanup();
    this.setStatus('connecting');

    const token = getAccessToken();
    const url = `${WS_BASE_URL}/realtime/${this.deviceId}${token ? `?token=${token}` : ''}`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.setStatus('connected');
      this.reconnectDelay = INITIAL_RECONNECT_DELAY;

      // Send subscribe message
      this.send({ type: 'subscribe', device_id: this.deviceId });

      // Start ping/pong keepalive
      this.pingTimer = setInterval(() => {
        this.send({ type: 'ping' });
      }, PING_INTERVAL);
    };

    this.ws.onmessage = event => {
      try {
        const message: WSMessage = JSON.parse(event.data);
        if (message.type === 'pong') return;
        this.onMessage(message);
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = _event => {
      this.stopPing();
      if (!this.isDestroyed) {
        this.setStatus('reconnecting');
        this.scheduleReconnect();
      } else {
        this.setStatus('disconnected');
      }
    };

    this.ws.onerror = () => {
      // onclose will fire after onerror, reconnect handled there
    };
  }

  disconnect(): void {
    this.isDestroyed = true;
    this.cleanup();
    this.setStatus('disconnected');
  }

  private send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private cleanup(): void {
    this.stopPing();
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onopen = null;
      this.ws.onmessage = null;
      this.ws.onclose = null;
      this.ws.onerror = null;
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close();
      }
      this.ws = null;
    }
  }

  private stopPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.isDestroyed) return;
    this.reconnectTimer = setTimeout(() => {
      this.connect();
    }, this.reconnectDelay);
    // Exponential backoff with jitter
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2 + Math.random() * 500,
      MAX_RECONNECT_DELAY
    );
  }
}
