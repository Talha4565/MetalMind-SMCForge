'use client';

import { useRouter } from 'next/navigation';
import { RegisterForm } from '@/components/Auth/RegisterForm';
import { useState } from 'react';
import { toast } from 'sonner';
import Link from 'next/link';
import { Zap, ArrowRight } from 'lucide-react';
import ThemeToggle from '@/components/Common/ThemeToggle';

type RegisterValues = {
  email: string;
  password: string;
  confirmPassword?: string;
};

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const handleRegister = async (values: RegisterValues) => {
    setIsLoading(true);

    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      const registerResponse = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: values.email,
          password: values.password,
        }),
      });

      const data = await registerResponse.json();
      if (!registerResponse.ok) {
        throw new Error(data.error || data.message || 'Registration failed');
      }

      if (data.dev_verified) {
        toast.success('Account created! Please log in.');
        router.push('/auth/login');
      } else {
        toast.success('Account created! Check your email for a verification code.');
        router.push(`/auth/verify-email?email=${encodeURIComponent(values.email)}`);
      }
    } catch (error: unknown) {
      setIsLoading(false);
      const message = error instanceof Error ? error.message : 'Please try again.';
      toast.error(`Registration Failed: ${message}`);
    }
  };

  return (
    <div className="flex min-h-screen">
      {/* Theme toggle — top right */}
      <div className="absolute top-4 right-4 z-50">
        <ThemeToggle />
      </div>

      {/* Left — Form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-md space-y-8">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-600/20">
              <span className="text-white text-sm font-black">M</span>
            </div>
            <div>
              <p className="text-sm font-bold text-card-foreground">MetalMind</p>
              <p className="text-[9px] font-medium uppercase tracking-widest text-muted-foreground">SMCForge</p>
            </div>
          </Link>

          {/* Headline */}
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground">
              Create your account
            </h1>
            <p className="text-sm text-muted-foreground mt-2">
              Start trading with AI-powered signals and analytics.
            </p>
          </div>

          {/* Form */}
          <RegisterForm onSubmit={handleRegister} isLoading={isLoading} />

          <p className="text-xs text-muted-foreground text-center">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-emerald-500 hover:text-emerald-400 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>

      {/* Right — Brand panel (hidden on mobile) */}
      <div className="hidden lg:flex flex-1 items-center justify-center bg-muted/30 border-l border-border">
        <div className="max-w-md space-y-12 px-12">
          <div className="relative space-y-6">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-accent/30 w-fit">
              <Zap className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
                AI-powered signals
              </span>
            </div>

            <h2 className="text-4xl font-black tracking-tight text-card-foreground leading-tight">
              Join thousands of
              <br />
              <span className="text-emerald-500">smart traders</span>
            </h2>

            <p className="text-sm text-muted-foreground leading-relaxed">
              Access XGBoost models trained on 20 years of tick data.
              SHAP explainability on every prediction.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div>
              <p className="text-3xl font-black font-mono text-card-foreground">XAU</p>
              <p className="text-[10px] uppercase tracking-widest text-emerald-500 mt-1">Gold</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-card-foreground">XAG</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">Silver</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-emerald-500">90</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">Features</p>
            </div>
            <div>
              <p className="text-3xl font-black font-mono text-emerald-500">86%</p>
              <p className="text-[10px] uppercase tracking-widest text-muted-foreground mt-1">Accuracy</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
