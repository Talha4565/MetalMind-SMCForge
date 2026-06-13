import { useEffect, useCallback, useRef } from 'react';
import { socketManager } from '@/lib/socket';

type SocketEventHandler = (data: unknown) => void;

interface UseWebSocketOptions {
  autoConnect?: boolean;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  onError?: (error: Error) => void;
}

/**
 * useWebSocket Hook
 * Manages WebSocket connection lifecycle and event subscriptions
 */
export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    autoConnect = true,
    onConnect,
    onDisconnect,
    onError,
  } = options;

  const handlersRef = useRef<Map<string, SocketEventHandler>>(new Map());

  // Connect on mount if autoConnect is enabled
  useEffect(() => {
    if (autoConnect) {
      socketManager.connect();
    }

    return () => {
      // Cleanup: unsubscribe all handlers
      handlersRef.current.forEach((handler, event) => {
        socketManager.off(event, handler);
      });
      handlersRef.current.clear();
    };
  }, [autoConnect]);

  // Setup connection event handlers
  useEffect(() => {
    if (onConnect) {
      const handler = () => onConnect();
      socketManager.on('connect', handler);
      return () => socketManager.off('connect', handler);
    }
  }, [onConnect]);

  useEffect(() => {
    if (onDisconnect) {
      const handler = (data: unknown) => {
        const reason = (data as { reason?: string })?.reason || 'unknown';
        onDisconnect(reason);
      };
      socketManager.on('disconnect', handler);
      return () => socketManager.off('disconnect', handler);
    }
  }, [onDisconnect]);

  useEffect(() => {
    if (onError) {
      const handler = (error: unknown) => onError(error as Error);
      socketManager.on('error', handler);
      return () => socketManager.off('error', handler);
    }
  }, [onError]);

  // Subscribe to event
  const subscribe = useCallback((event: string, handler: SocketEventHandler) => {
    socketManager.on(event, handler);
    handlersRef.current.set(event, handler);

    // Return unsubscribe function
    return () => {
      socketManager.off(event, handler);
      handlersRef.current.delete(event);
    };
  }, []);

  // Emit event
  const emit = useCallback((event: string, data?: unknown) => {
    socketManager.emit(event, data);
  }, []);

  // Manual connect
  const connect = useCallback(() => {
    socketManager.connect();
  }, []);

  // Manual disconnect
  const disconnect = useCallback(() => {
    socketManager.disconnect();
  }, []);

  // Check connection status
  const isConnected = socketManager.isConnected();

  return {
    subscribe,
    emit,
    connect,
    disconnect,
    isConnected,
  };
}
