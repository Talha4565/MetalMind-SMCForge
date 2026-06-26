'use client';

import { useEffect, useRef, useState, useCallback } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

interface UseLongPollOptions {
  url: string;
  timeout?: number;
  enabled?: boolean;
}

/**
 * Long-polling hook.
 *
 * Sends GET with If-None-Match header. Server holds connection up to `timeout`
 * seconds, returning 304 if unchanged or 200 with new data. Automatically
 * re-connects on every response.
 */
export function useLongPoll<T>({ url, timeout = 30, enabled = true }: UseLongPollOptions) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const etagRef = useRef<string>('');
  const abortRef = useRef<AbortController | null>(null);
  const activeRef = useRef(true);

  const poll = useCallback(async () => {
    if (!enabled || !activeRef.current) return;

    const headers: Record<string, string> = {};
    if (etagRef.current) {
      headers['If-None-Match'] = etagRef.current;
    }

    // Also attach auth token if present
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const res = await fetch(url, {
        headers,
        signal: controller.signal,
      });

      if (res.status === 304) {
        // Nothing changed — reconnect immediately
      } else if (res.ok) {
        const newEtag = res.headers.get('ETag') || '';
        if (newEtag) etagRef.current = newEtag;
        const json = await res.json();
        setData(json);
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        // Network error — brief pause then retry
        await new Promise(r => setTimeout(r, 2000));
      }
    } finally {
      setLoading(false);
      if (activeRef.current) {
        poll();
      }
    }
  }, [url, enabled]);

  useEffect(() => {
    activeRef.current = true;
    setLoading(true);
    poll();
    return () => {
      activeRef.current = false;
      abortRef.current?.abort();
    };
  }, [poll]);

  return { data, loading };
}
