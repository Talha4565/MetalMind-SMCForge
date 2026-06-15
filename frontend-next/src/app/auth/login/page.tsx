'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signIn } from 'next-auth/react';
import { LoginForm } from '@/components/Auth/LoginForm';
import { toast } from 'sonner';
import Link from 'next/link';
import { ArrowRight, Zap } from 'lucide-react';
import ThemeToggle from '@/components/Common/ThemeToggle';

type LoginValues = {
  email: string;
  password: string;
  totp_code?: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [requires2fa, setRequires2fa] = useState(false);

  const handleLogin = async (values: LoginValues) => {
    setIsLoading(true);
    try {
      const result = await signIn('credentials', {
        redirect: false,
        callbackUrl: '/dashboard',
        email: values.email,
        password: values.password,
        totp_code: values.totp_code,
      });

      if (result?.error) {
        const message = result.error;
        if (message.includes('requires_2fa') || message.toLowerCase().includes('2fa')) {
          setRequires2fa(true);
          toast.error('Two-factor authentication required. Enter your 2FA code below.');
        } else {
          toast.error(`Login failed: ${message}`);
        }
        return;
      }

      if (result?.ok) {
        toast.success('Welcome back! Redirecting to dashboard...');
        router.push('/dashboard');
        return;
      }

      toast.error('Login failed. Please try again.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Login failed';
      if (message.includes('requires_2fa')) {
        setRequires2fa(true);
        toast.error('Two-factor authentication required. Enter your 2FA code below.');
      } else {
        toast.error(`Login failed: ${message}`);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Theme toggle â€” top right */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Left â€” Form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-600/20">
              <span className="text-white text-sm font-black">M</span>
            </div>
            <div>
              <p className="text-sm font-bold text-card-foreground">MetalMind</p>
              <p className="text-[9px] font-medium uppercase tracking-widest text-slate-500">SMCForge</p>
            </div>
          </Link>

          {/* Headline */}
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground">
              Welcome back
            </h1>
            <p className="text-sm text-slate-500 mt-2">
              Sign in to access your trading signals and analytics.
            </p>
          </div>

          {/* Form */}
          <LoginForm
            onSubmit={handleLogin}
            isLoading={isLoading}
            showOtp={requires2fa}
          />

          <p className="text-xs text-slate-600 text-center">
            Don&apos;t have an account?{' '}
            <Link href="/auth/register" className="text-emerald-400 hover:text-emerald-300 font-medium">
              Create one
            </Link>
          </p>
        </div>
      </div>

      {/* Right â€” Brand panel (hidden on mobile) */}
      <div className="hidden lg:flex flex-1 items-center justify-center bg-muted/30 border-l border-border">
        <div className="max-w-md space-y-12 px-12">

          <div className="relative space-y-6">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-accent/30 w-fit">
              <Zap className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] font-medium uppercase tracking-widest text-slate-400">
                AI-powered signals
              </span>
            </div>

            <h2 className="text-4xl font-black tracking-tight text-card-foreground leading-tight">
              Trade with
              <br />
              <span className="text-emerald-400">machine precision</span>
            </h2>

            <p className="text-sm text-slate-500 leading-relaxed">
              XGBoost models trained on 20 years of tick data.
              SHAP explainability on every prediction.
            </p>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-3xl font-black font-mono text-card-foreground">XAU</p>
              <p className="text-[10px] uppercase tracking-widest text-emerald-500 mt-1">Gold</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-card-foreground">XAG</p>
              <p className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Silver</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-emerald-400">90</p>
              <p className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Features</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-emerald-400">86%</p>
              <p className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Accuracy</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
