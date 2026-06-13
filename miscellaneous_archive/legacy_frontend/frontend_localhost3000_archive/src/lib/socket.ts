import { io, Socket } from 'socket.io-client';
import { APP_CONFIG, WEBSOCKET_EVENTS } from '@/config/constants';
import { tokenManager } from './tokenManager';
import type { WebSocketMessage } from '@/types';

type SocketEventHandler = (data: unknown) => void;

/**
 * WebSocket Client Manager
 * Handles Socket.io connection with authentication and reconnection logic
 */
class SocketManager {
  private socket: Socket | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private eventHandlers: Map<string, Set<SocketEventHandler>> = new Map();

  constructor() {
    // Don't auto-connect, wait for explicit connect() call
  }

  /**
   * Connect to WebSocket server
   */
  connect(): void {
    if (this.socket?.connected || this.isConnecting) {
      console.log('Socket already connected or connecting');
      return;
    }

    const token = tokenManager.getAccessToken();
    if (!token) {
      console.warn('Cannot connect to WebSocket: No access token');
      return;
    }

    this.isConnecting = true;

    try {
      this.socket = io(APP_CONFIG.wsUrl, {
        auth: {
          token,
        },
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 20000,
      });

      this.setupEventListeners();
      this.isConnecting = false;
    } catch (error) {
      console.error('Failed to create socket connection:', error);
      this.isConnecting = false;
    }
  }

  /**
   * Setup socket event listeners
   */
  private setupEventListeners(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on(WEBSOCKET_EVENTS.connect, () => {
      console.log('✓ WebSocket connected');
      this.reconnectAttempts = 0;
      this.notifyHandlers(WEBSOCKET_EVENTS.connect, { connected: true });
    });

    this.socket.on(WEBSOCKET_EVENTS.disconnect, (reason: string) => {
      console.log('WebSocket disconnected:', reason);
      this.notifyHandlers(WEBSOCKET_EVENTS.disconnect, { reason });
    });

    this.socket.on(WEBSOCKET_EVENTS.error, (error: Error) => {
      console.error('WebSocket error:', error);
      this.notifyHandlers(WEBSOCKET_EVENTS.error, error);
    });

    // Reconnection events
    this.socket.io.on('reconnect_attempt', (attempt: number) => {
      this.reconnectAttempts = attempt;
      console.log(`Reconnection attempt ${attempt}/${this.maxReconnectAttempts}`);
    });

    this.socket.io.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
      this.disconnect();
    });

    this.socket.io.on('reconnect', (attempt: number) => {
      console.log(`✓ WebSocket reconnected after ${attempt} attempts`);
      this.reconnectAttempts = 0;
    });
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    console.log('WebSocket disconnected');
  }

  /**
   * Subscribe to a specific event
   */
  on(event: string, handler: SocketEventHandler): void {
    // Add to internal handlers
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // Add to socket if connected
    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  /**
   * Unsubscribe from a specific event
   */
  off(event: string, handler: SocketEventHandler): void {
    // Remove from internal handlers
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
      if (handlers.size === 0) {
        this.eventHandlers.delete(event);
      }
    }

    // Remove from socket if connected
    if (this.socket) {
      this.socket.off(event, handler);
    }
  }

  /**
   * Emit event to server
   */
  emit(event: string, data?: unknown): void {
    if (!this.socket?.connected) {
      console.warn('Cannot emit: Socket not connected');
      return;
    }
    this.socket.emit(event, data);
  }

  /**
   * Subscribe to event once
   */
  once(event: string, handler: SocketEventHandler): void {
    if (!this.socket) {
      console.warn('Cannot subscribe: Socket not initialized');
      return;
    }
    this.socket.once(event, handler);
  }

  /**
   * Check if socket is connected
   */
  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  /**
   * Get socket instance (for advanced usage)
   */
  getSocket(): Socket | null {
    return this.socket;
  }

  /**
   * Notify all handlers for an event
   */
  private notifyHandlers(event: string, data: unknown): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in ${event} handler:`, error);
        }
      });
    }
  }

  /**
   * Reconnect with new token (after token refresh)
   */
  reconnectWithNewToken(): void {
    if (this.socket) {
      this.disconnect();
    }
    this.connect();
  }
}

// Export singleton instance
export const socketManager = new SocketManager();

/**
 * Helper function to parse WebSocket messages
 */
export function parseSocketMessage<T>(message: unknown): WebSocketMessage<T> | null {
  try {
    if (typeof message === 'object' && message !== null) {
      return message as WebSocketMessage<T>;
    }
    return null;
  } catch (error) {
    console.error('Failed to parse socket message:', error);
    return null;
  }
}
