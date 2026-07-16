'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Mail, ArrowLeft, Loader2 } from 'lucide-react';

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) {
      toast.error('Email is required');
      return;
    }

    setIsLoading(true);
    try {
      await apiClient.forgotPassword(email.trim());
      setSent(true);
      toast.success('If email exists, reset link sent');
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to send reset link';
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          <Link href="/auth/login" className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300">
            <ArrowLeft className="w-4 h-4" />
            Back to login
          </Link>

          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground">
              {sent ? 'Check your email' : 'Forgot password?'}
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              {sent
                ? 'We sent a reset link to your email. It expires in 1 hour.'
                : 'Enter your email and we\'ll send you a reset link.'}
            </p>
          </div>

          {!sent ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-card-foreground">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-card-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                />
              </div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                Send Reset Link
              </button>
            </form>
          ) : (
            <div className="text-center py-8">
              <Mail className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
              <p className="text-sm text-slate-400 mb-4">
                If an account exists with {email}, you&apos;ll receive a reset link shortly.
              </p>
              <button
                onClick={() => router.push('/auth/login')}
                className="text-emerald-400 hover:text-emerald-300 text-sm font-medium"
              >
                Return to login
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="hidden lg:flex flex-1 items-center justify-center bg-muted/30 border-l border-border">
        <div className="max-w-md px-12 space-y-6">
          <h2 className="text-4xl font-black tracking-tight text-card-foreground">
            Reset your<br />
            <span className="text-emerald-400">password</span>
          </h2>
          <p className="text-sm text-slate-300">
            Secure password reset with token-based verification.
            Links expire in 1 hour for your protection.
          </p>
        </div>
      </div>
    </div>
  );
}
