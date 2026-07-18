'use client';

import ErrorFallback from '@/components/Common/ErrorFallback';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorFallback
      code="ERR"
      title="Dashboard Error"
      message={error.message || 'Failed to load dashboard data.'}
      buttonLabel="Reload"
      onReset={reset}
    />
  );
}
