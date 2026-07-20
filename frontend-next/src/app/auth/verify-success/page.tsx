'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { CheckCircle2 } from 'lucide-react';
import { Suspense } from 'react';

function VerifySuccessContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="relative z-10 w-full max-w-lg">
        <div className="rounded-3xl border border-border bg-card/95 p-10 shadow-2xl shadow-slate-950/40">
          <div className="flex items-center justify-center mb-6 rounded-3xl bg-emerald-600/10 p-5">
            <CheckCircle2 className="h-12 w-12 text-emerald-400" />
          </div>

          <div className="space-y-6 text-center">
            <h1 className="text-4xl font-black tracking-tight text-white">Email Verified</h1>
            <p className="text-slate-400 text-base leading-7">
              Your email has been successfully verified. {email ? `You can now sign in with ${email}.` : 'You may now access your account.'}
            </p>

            <div className="space-y-4 sm:space-y-0 sm:flex sm:justify-center sm:gap-4">
              <Link
                href="/auth/login"
                className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-6 py-4 text-sm font-semibold text-white transition hover:bg-emerald-500 sm:w-auto"
              >
                Sign In
              </Link>
              <Link
                href="/"
                className="inline-flex w-full items-center justify-center rounded-2xl border border-border bg-background px-6 py-4 text-sm font-semibold text-foreground transition hover:border-ring sm:w-auto"
              >
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function VerifySuccessPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    }>
      <VerifySuccessContent />
    </Suspense>
  );
}
