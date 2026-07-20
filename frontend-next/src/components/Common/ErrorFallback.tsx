'use client';

interface ErrorFallbackProps {
  code?: string;
  title?: string;
  message: string;
  buttonLabel?: string;
  onReset: () => void;
}

export default function ErrorFallback({
  code = 'ERR',
  title = 'Something went wrong',
  message,
  buttonLabel = 'Try again',
  onReset,
}: ErrorFallbackProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="max-w-md text-center space-y-4">
        <p className="text-6xl font-black font-mono text-terminal-sell">{code}</p>
        <h1 className="text-xl font-bold text-card-foreground">{title}</h1>
        <p className="text-sm text-muted-foreground">{message}</p>
        <button
          onClick={onReset}
          className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors"
        >
          {buttonLabel}
        </button>
      </div>
    </div>
  );
}
