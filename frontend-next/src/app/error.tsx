'use client';

import ErrorFallback from '@/components/Common/ErrorFallback';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <ErrorFallback
      code="500"
      title="Something went wrong"
      message={error.message || 'An unexpected error occurred.'}
      onReset={reset}
    />
  );
}
