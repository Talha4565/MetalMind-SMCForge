import React, { useMemo } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { ErrorBoundary } from '@/components/common';
import { queryClient } from '@/lib/queryClient';
import { lightTheme, darkTheme } from '@/styles/theme';
import { useUiStore } from '@/store/uiStore';

interface AppProvidersProps {
  children: React.ReactNode;
}

/**
 * App Providers
 * Wraps the app with all necessary providers
 */
export function AppProviders({ children }: AppProvidersProps) {
  const themeMode = useUiStore((state) => state.themeMode);

  // Memoize theme to prevent unnecessary re-renders
  const theme = useMemo(
    () => (themeMode === 'light' ? lightTheme : darkTheme),
    [themeMode]
  );

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {children}
          
          {/* Toast Notifications */}
          <ToastContainer
            position="top-right"
            autoClose={4000}
            hideProgressBar={false}
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
            theme={themeMode}
            style={{ zIndex: 9999 }}
          />
          
          {/* React Query Devtools (only in development) */}
          {import.meta.env.DEV && (
            <ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
          )}
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
