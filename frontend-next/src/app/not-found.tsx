import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="max-w-md text-center space-y-4">
        <p className="text-6xl font-black font-mono text-terminal-hold">404</p>
        <h1 className="text-xl font-bold text-card-foreground">Page not found</h1>
        <p className="text-sm text-muted-foreground">
          The page you are looking for does not exist or has been moved.
        </p>
        <Link
          href="/"
          className="inline-block px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg transition-colors"
        >
          Go home
        </Link>
      </div>
    </div>
  );
}
