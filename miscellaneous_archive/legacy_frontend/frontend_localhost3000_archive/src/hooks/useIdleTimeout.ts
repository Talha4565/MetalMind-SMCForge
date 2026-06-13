import { useEffect, useRef, useState, useCallback } from 'react';
import { SESSION_CONFIG } from '@/config/constants';

interface UseIdleTimeoutOptions {
  timeout?: number;
  warningTime?: number;
  onIdle?: () => void;
  onWarning?: () => void;
  onActive?: () => void;
}

/**
 * useIdleTimeout Hook
 * Monitors user activity and triggers callbacks on idle/warning
 */
export function useIdleTimeout({
  timeout = SESSION_CONFIG.timeout,
  warningTime = SESSION_CONFIG.warningTime,
  onIdle,
  onWarning,
  onActive,
}: UseIdleTimeoutOptions = {}) {
  const [isIdle, setIsIdle] = useState(false);
  const [showWarning, setShowWarning] = useState(false);
  const [remainingTime, setRemainingTime] = useState(timeout);

  const timeoutRef = useRef<NodeJS.Timeout>();
  const warningTimeoutRef = useRef<NodeJS.Timeout>();
  const countdownRef = useRef<NodeJS.Timeout>();
  const lastActivityRef = useRef<number>(Date.now());

  // Reset all timers
  const resetTimers = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current);
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
    }

    setIsIdle(false);
    setShowWarning(false);
    setRemainingTime(timeout);
    lastActivityRef.current = Date.now();

    // Set warning timer
    warningTimeoutRef.current = setTimeout(() => {
      setShowWarning(true);
      onWarning?.();

      // Start countdown
      countdownRef.current = setInterval(() => {
        const elapsed = Date.now() - lastActivityRef.current;
        const remaining = Math.max(0, timeout - elapsed);
        setRemainingTime(remaining);

        if (remaining <= 0) {
          clearInterval(countdownRef.current!);
        }
      }, 1000);
    }, timeout - warningTime);

    // Set idle timer
    timeoutRef.current = setTimeout(() => {
      setIsIdle(true);
      setShowWarning(false);
      onIdle?.();
    }, timeout);
  }, [timeout, warningTime, onIdle, onWarning]);

  // Handle user activity
  const handleActivity = useCallback(() => {
    if (!isIdle && !showWarning) {
      // Just update timestamp if not in warning/idle state
      lastActivityRef.current = Date.now();
    } else if (showWarning || isIdle) {
      // Reset everything if user was inactive
      onActive?.();
      resetTimers();
    }
  }, [isIdle, showWarning, onActive, resetTimers]);

  // Setup event listeners
  useEffect(() => {
    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

    const throttledActivity = throttle(handleActivity, 1000);

    events.forEach((event) => {
      document.addEventListener(event, throttledActivity);
    });

    // Initialize timers
    resetTimers();

    return () => {
      events.forEach((event) => {
        document.removeEventListener(event, throttledActivity);
      });
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (warningTimeoutRef.current) clearTimeout(warningTimeoutRef.current);
      if (countdownRef.current) clearInterval(countdownRef.current);
    };
  }, [handleActivity, resetTimers]);

  return {
    isIdle,
    showWarning,
    remainingTime,
    reset: resetTimers,
  };
}

/**
 * Throttle helper
 */
function throttle<T extends (...args: unknown[]) => void>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return function (this: unknown, ...args: Parameters<T>) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
