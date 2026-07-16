'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Lock, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!token) {
      toast.error('Invalid or missing reset token');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }

    setIsLoading(true);
    try {
      await apiClient.resetPassword(token, password);
      setSuccess(true);
      toast.success('Password reset successful!');
    } catch (error: unknown) {
      const errorMsg = error instanceof Error ? error.message : 'Failed to reset password';
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
              {success ? 'Password reset' : 'Set new password'}
            </h1>
            <p className="text-sm text-slate-400 mt-2">
              {success
                ? 'Your password has been reset. You can now login with your new password.'
                : 'Enter your new password below.'}
            </p>
          </div>

          {!success ? (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-card-foreground">New Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 8 characters"
                  className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-card-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-card-foreground">Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm your password"
                  className="w-full mt-1 px-3 py-2 bg-background border border-border rounded-lg text-card-foreground focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                  minLength={8}
                />
              </div>
              <p className="text-xs text-slate-500">
                Password must be 8+ characters with uppercase, lowercase, number, and special character.
              </p>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                Reset Password
              </button>
            </form>
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
              <p className="text-sm text-slate-400 mb-4">
                Your password has been successfully reset.
              </p>
              <button
                onClick={() => router.push('/auth/login')}
                className="px-6 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg transition-colors"
              >
                Go to Login
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="hidden lg:flex flex-1 items-center justify-center bg-muted/30 border-l border-border">
        <div className="max-w-md px-12 space-y-6">
          <h2 className="text-4xl font-black tracking-tight text-card-foreground">
            Secure<br />
            <span className="text-emerald-400">reset</span>
          </h2>
          <p className="text-sm text-slate-300">
            Your new password is encrypted with bcrypt.
            Old sessions are invalidated for security.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-background p-4">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
