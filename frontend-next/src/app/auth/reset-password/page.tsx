'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Instrument_Serif, IBM_Plex_Mono } from 'next/font/google';
import { Lock, ArrowLeft, Loader2, CheckCircle } from 'lucide-react';

const serif = Instrument_Serif({
  subsets: ['latin'], weight: '400', style: ['normal', 'italic'], variable: '--font-serif',
});
const mono = IBM_Plex_Mono({
  subsets: ['latin'], weight: ['400', '500'], variable: '--font-mono',
});

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
    if (!token) { toast.error('Invalid or missing reset token'); return; }
    if (password !== confirmPassword) { toast.error('Passwords do not match'); return; }
    if (password.length < 8) { toast.error('Password must be at least 8 characters'); return; }

    setIsLoading(true);
    try {
      await apiClient.resetPassword(token, password);
      setSuccess(true);
      toast.success('Password reset successful!');
    } catch {
      toast.error('Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`${serif.variable} ${mono.variable} relative min-h-screen overflow-hidden bg-[#0A0A0B] text-[#EDEAE3]`}>
      <div className="absolute right-6 top-6 z-50"><ThemeToggle /></div>

      <div className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{ backgroundImage: 'linear-gradient(#EDEAE3 1px, transparent 1px), linear-gradient(90deg, #EDEAE3 1px, transparent 1px)', backgroundSize: '64px 64px' }} />

      <div className="relative flex flex-col items-center justify-center px-6 py-20">
        <div className="mb-10 flex items-center gap-3">
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#5C5C59]">No. 0X44</span>
          <span className="h-3 w-px bg-white/10" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#B8935A]">SMC-90F</span>
        </div>

        <h1 className="mb-1 text-center text-5xl italic" style={{ fontFamily: 'var(--font-serif)' }}>MetalMind</h1>
        <p className="mb-12 font-mono text-[10px] uppercase tracking-[0.35em] text-[#5C5C59]">SMCForge — new credentials</p>

        <div className="relative w-full max-w-md">
          <span className="absolute -left-px -top-px h-3 w-3 border-l border-t border-[#B8935A]" />
          <span className="absolute -right-px -top-px h-3 w-3 border-r border-t border-[#B8935A]" />
          <span className="absolute -bottom-px -left-px h-3 w-3 border-b border-l border-[#B8935A]" />
          <span className="absolute -bottom-px -right-px h-3 w-3 border-b border-r border-[#B8935A]" />

          <div className="border border-white/10 bg-[#131315] px-8 py-10">
            <div className="mb-6">
              <Link href="/auth/login" className="inline-flex items-center gap-1.5 text-[11px] text-[#5C5C59] hover:text-[#B8935A] transition-colors">
                <ArrowLeft className="w-3 h-3" /> Back to login
              </Link>
            </div>

            <h2 className="mb-1 text-lg font-normal text-[#EDEAE3]">
              {success ? 'Password reset' : 'Set new password'}
            </h2>
            <p className="mb-8 text-[13px] text-[#8B9099]">
              {success ? 'Your password has been reset. You can now login.' : 'Enter your new password below.'}
            </p>

            {!success ? (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="text-slate-400 text-xs font-medium">New Password</label>
                  <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                    placeholder="At least 8 characters" required minLength={8}
                    className="w-full mt-1 h-11 px-3 bg-input/30 border border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all" />
                </div>
                <div>
                  <label className="text-slate-400 text-xs font-medium">Confirm Password</label>
                  <input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password" required minLength={8}
                    className="w-full mt-1 h-11 px-3 bg-input/30 border border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all" />
                </div>
                <p className="text-[10px] text-[#5C5C59]">8+ chars, uppercase, lowercase, number, special character.</p>
                <button type="submit" disabled={isLoading}
                  className="w-full h-11 bg-[#B8935A] hover:bg-[#D1AC79] text-[#0A0A0B] font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Lock className="w-4 h-4" />}
                  Reset Password
                </button>
              </form>
            ) : (
              <div className="text-center py-6">
                <CheckCircle className="w-10 h-10 text-[#B8935A] mx-auto mb-3" />
                <p className="text-[13px] text-[#8B9099] mb-4">Your password has been successfully reset.</p>
                <button onClick={() => router.push('/auth/login')}
                  className="px-6 py-2.5 bg-[#B8935A] hover:bg-[#D1AC79] text-[#0A0A0B] font-bold transition-all">
                  Go to Login
                </button>
              </div>
            )}
          </div>
        </div>

        <p className="mt-10 font-mono text-[9px] uppercase tracking-[0.25em] text-[#454543]">
          XGBoost · SHAP · ChromaDB · Walk-forward CV
        </p>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0B]">
        <p className="font-mono text-xs text-[#5C5C59] tracking-widest">LOADING...</p>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
