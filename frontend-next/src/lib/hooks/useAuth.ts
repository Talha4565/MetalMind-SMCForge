'use client';

import { useSession, signOut } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';

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
