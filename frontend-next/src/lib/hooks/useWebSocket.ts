'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000';

export function useWebSocket<T>(event: string) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    let socket: Socket;

    try {
      socket = io(SOCKET_URL, {
        path: '/socket.io',
        transports: ['websocket'],
        timeout: 5000,
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: 3,
        reconnectionDelay: 2000,
      });

      socket.on('connect', () => {
        setIsConnected(true);
        setError(null);
      });

      socket.on('disconnect', () => {
        setIsConnected(false);
      });

      socket.on('connect_error', () => {
        setIsConnected(false);
      });

      socket.on(event, (payload: T) => {
        setData(payload);
      });

      socketRef.current = socket;
    } catch {
      setIsConnected(false);
    }

    return () => {
      socketRef.current?.disconnect();
      socketRef.current = null;
    };
  }, [event]);

  const emit = useCallback(
    (eventName: string, payload: unknown) => {
      if (socketRef.current && isConnected) {
        socketRef.current.emit(eventName, payload);
      }
    },
    [isConnected]
  );

  return { data, isConnected, error, emit };
}
