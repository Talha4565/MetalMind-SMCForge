'use client';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="max-w-md text-center space-y-4">
        <p className="text-6xl font-black font-mono text-terminal-sell">ERR</p>
        <h1 className="text-xl font-bold text-card-foreground">Dashboard Error</h1>
        <p className="text-sm text-muted-foreground">
          {error.message || 'Failed to load dashboard data.'}
        </p>
        <button
          onClick={reset}
          className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors"
        >
          Reload
        </button>
      </div>
    </div>
  );
}
