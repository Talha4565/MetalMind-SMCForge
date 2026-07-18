'use client';

import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

/**
 * Syncs NextAuth session token with api-client (memory-only, never localStorage).
 */
export function useAuthSync() {
  const { data: session, status } = useSession();

  useEffect(() => {
    if (status === 'authenticated' && session?.user?.accessToken) {
      apiClient.setTokens(
        session.user.accessToken,
        session.user.refreshToken
      );
    } else if (status === 'unauthenticated') {
      apiClient.clearAuth();
    }
  }, [session, status]);
}

/**
 * Hook for handling logout using NextAuth.
 */
export function useLogout() {
  const router = useRouter();

  return async () => {
    apiClient.clearAuth();
    await signOut({ redirect: false });
    router.push('/auth/login');
  };
}

/**
 * Hook to get current user session info.
 */
export function useCurrentUser() {
  const { data: session, status } = useSession();

  return {
    user: session?.user,
    isLoading: status === 'loading',
    isAuthenticated: status === 'authenticated',
  };
}
