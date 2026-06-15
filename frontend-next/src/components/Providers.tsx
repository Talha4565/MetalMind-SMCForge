'use client';

import { SessionProvider, useSession } from "next-auth/react";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from 'next-themes';
import { ReactNode, useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

function SessionSync() {
  const { data: session, status } = useSession();

  useEffect(() => {
    if (status === 'authenticated' && session?.user?.accessToken) {
      apiClient.setToken(session.user.accessToken as string);
      return;
    }

    if (status === 'unauthenticated') {
      apiClient.clearAuth();
    }
  }, [session?.user?.accessToken, status]);

  return null;
}

/**
 * Global providers wrapper for the application.
 * Handles NextAuth sessions and TanStack Query client.
 */
export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,
          },
        },
      })
  );

  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
      <SessionProvider>
        <SessionSync />
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </SessionProvider>
    </ThemeProvider>
  );
}
