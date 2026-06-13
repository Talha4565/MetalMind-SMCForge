import React from 'react';
import { ErrorBoundary as ReactErrorBoundary } from 'react-error-boundary';
import { Box, Button, Container, Paper, Typography } from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import RefreshIcon from '@mui/icons-material/Refresh';

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

/**
 * Error Fallback Component
 * Displayed when an error is caught by the error boundary
 */
function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <Container maxWidth="md">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          py: 4,
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            textAlign: 'center',
            width: '100%',
          }}
        >
          <ErrorOutlineIcon
            sx={{
              fontSize: 64,
              color: 'error.main',
              mb: 2,
            }}
          />
          <Typography variant="h4" component="h1" gutterBottom>
            Oops! Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            We're sorry for the inconvenience. The application encountered an unexpected error.
          </Typography>
          
          {import.meta.env.DEV && (
            <Paper
              sx={{
                p: 2,
                mt: 3,
                mb: 3,
                textAlign: 'left',
                bgcolor: 'grey.100',
                border: '1px solid',
                borderColor: 'error.light',
              }}
            >
              <Typography variant="subtitle2" color="error" gutterBottom>
                Error Details (Development Only):
              </Typography>
              <Typography
                variant="body2"
                component="pre"
                sx={{
                  fontFamily: 'monospace',
                  fontSize: '0.875rem',
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {error.message}
                {'\n\n'}
                {error.stack}
              </Typography>
            </Paper>
          )}

          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', mt: 3 }}>
            <Button
              variant="contained"
              startIcon={<RefreshIcon />}
              onClick={resetErrorBoundary}
            >
              Try Again
            </Button>
            <Button
              variant="outlined"
              onClick={() => window.location.href = '/'}
            >
              Go to Dashboard
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
}

/**
 * Error handler
 * Logs errors and sends to monitoring service (Sentry)
 */
function errorHandler(error: Error, info: { componentStack: string }) {
  console.error('Error caught by boundary:', error);
  console.error('Component stack:', info.componentStack);

  // Send to Sentry in production
  if (import.meta.env.PROD && import.meta.env.VITE_SENTRY_DSN) {
    // Sentry integration will be added in Phase 6
    // Sentry.captureException(error, { extra: info });
  }
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<ErrorFallbackProps>;
}

/**
 * Error Boundary Wrapper
 * Catches JavaScript errors anywhere in child component tree
 */
export function ErrorBoundary({ children, fallback }: ErrorBoundaryProps) {
  return (
    <ReactErrorBoundary
      FallbackComponent={fallback || ErrorFallback}
      onError={errorHandler}
      onReset={() => {
        // Reset app state if needed
        window.location.href = '/';
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
}
