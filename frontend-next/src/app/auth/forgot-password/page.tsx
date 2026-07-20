'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Instrument_Serif, IBM_Plex_Mono } from 'next/font/google';
import { Mail, ArrowLeft, Loader2 } from 'lucide-react';

const serif = Instrument_Serif({
  subsets: ['latin'], weight: '400', style: ['normal', 'italic'], variable: '--font-serif',
});
const mono = IBM_Plex_Mono({
  subsets: ['latin'], weight: ['400', '500'], variable: '--font-mono',
});

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) { toast.error('Email is required'); return; }
    setIsLoading(true);
    try {
      await apiClient.forgotPassword(email.trim());
      setSent(true);
      toast.success('If email exists, reset link sent');
    } catch {
      toast.error('Failed to send reset link');
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
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#5C5C59]">No. 0X43</span>
          <span className="h-3 w-px bg-white/10" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#B8935A]">SMC-90F</span>
        </div>

        <h1 className="mb-1 text-center text-5xl italic" style={{ fontFamily: 'var(--font-serif)' }}>MetalMind</h1>
        <p className="mb-12 font-mono text-[10px] uppercase tracking-[0.35em] text-[#5C5C59]">SMCForge — account recovery</p>

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
              {sent ? 'Check your email' : 'Forgot password?'}
            </h2>
            <p className="mb-8 text-[13px] text-[#8B9099]">
              {sent ? 'We sent a reset link. It expires in 1 hour.' : 'Enter your email and we\'ll send you a reset link.'}
            </p>

            {!sent ? (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="text-slate-400 text-xs font-medium">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@example.com" required
                    className="w-full mt-1 h-11 px-3 bg-input/30 border border-border text-foreground placeholder:text-muted-foreground focus:border-ring focus:ring-ring/20 transition-all" />
                </div>
                <button type="submit" disabled={isLoading}
                  className="w-full h-11 bg-[#B8935A] hover:bg-[#D1AC79] text-[#0A0A0B] font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                  {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Mail className="w-4 h-4" />}
                  Send Reset Link
                </button>
              </form>
            ) : (
              <div className="text-center py-6">
                <Mail className="w-10 h-10 text-[#B8935A] mx-auto mb-3" />
                <p className="text-[13px] text-[#8B9099] mb-4">
                  If an account exists with <span className="text-[#EDEAE3]">{email}</span>, you&apos;ll receive a reset link shortly.
                </p>
                <button onClick={() => router.push('/auth/login')}
                  className="text-[#B8935A] hover:text-[#D1AC79] text-sm transition-colors">
                  Return to login
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
