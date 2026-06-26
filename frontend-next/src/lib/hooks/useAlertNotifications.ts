'use client';

import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

const SOCKET_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000';

interface AlertTriggered {
  id: string;
  asset: string;
  signal: string;
  result: string;
  entry: number;
  exit_price: number;
  pnl_pct: number;
  timestamp: string;
}

export function useAlertNotifications() {
  const socketRef = useRef<Socket | null>(null);
  const permissionRef = useRef<NotificationPermission>('default');

  useEffect(() => {
    // Request notification permission on mount
    if ('Notification' in window) {
      Notification.requestPermission().then((perm) => {
        permissionRef.current = perm;
      });
    }

    const socket = io(SOCKET_URL, {
      path: '/socket.io',
      transports: ['websocket'],
      timeout: 5000,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: 3,
      reconnectionDelay: 2000,
    });

    socket.on('alert_triggered', (alert: AlertTriggered) => {
      const isWin = alert.result === 'WIN_TP';

      // Show browser notification
      if ('Notification' in window && Notification.permission === 'granted') {
        const emoji = isWin ? '🎯' : '🛑';
        const title = `${emoji} ${alert.result.replace('_', ' ')} — ${alert.asset.toUpperCase()}`;
        const body = [
          `${alert.signal} @ $${alert.entry.toLocaleString()}`,
          `Exited @ $${alert.exit_price.toLocaleString()}`,
          `PnL: ${alert.pnl_pct >= 0 ? '+' : ''}${alert.pnl_pct}%`,
        ].join('\n');

        const notification = new Notification(title, {
          body,
          icon: '/favicon.ico',
          tag: alert.id,
        });

        notification.onclick = () => {
          window.focus();
          notification.close();
        };
      }

      // Play a sound
      try {
        const beeps = isWin ? 3 : 2;
        const ctx = new AudioContext();
        for (let i = 0; i < beeps; i++) {
          const osc = ctx.createOscillator();
          const gain = ctx.createGain();
          osc.connect(gain);
          gain.connect(ctx.destination);
          osc.frequency.value = isWin ? 880 : 440;
          osc.type = 'sine';
          gain.gain.value = 0.15;
          osc.start(ctx.currentTime + i * 0.15);
          osc.stop(ctx.currentTime + i * 0.15 + 0.1);
        }
      } catch {}
    });

    socketRef.current = socket;

    return () => {
      socket.disconnect();
      socketRef.current = null;
    };
  }, []);

  const requestPermission = useCallback(async () => {
    if ('Notification' in window) {
      const perm = await Notification.requestPermission();
      permissionRef.current = perm;
      return perm;
    }
    return 'denied' as NotificationPermission;
  }, []);

  return { requestPermission };
}
