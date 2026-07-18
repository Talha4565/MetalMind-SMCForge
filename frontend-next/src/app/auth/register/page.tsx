'use client';

import { useRouter } from 'next/navigation';
import { RegisterForm } from '@/components/Auth/RegisterForm';
import { useState } from 'react';
import { toast } from 'sonner';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Instrument_Serif, IBM_Plex_Mono } from 'next/font/google';

const serif = Instrument_Serif({
  subsets: ['latin'],
  weight: '400',
  style: ['normal', 'italic'],
  variable: '--font-serif',
});

const mono = IBM_Plex_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
});

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
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: values.email, password: values.password }),
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
    <div
      className={`${serif.variable} ${mono.variable} relative min-h-screen overflow-hidden bg-[#0A0A0B] text-[#EDEAE3]`}
    >
      <div className="absolute right-6 top-6 z-50">
        <ThemeToggle />
      </div>

      {/* Faint chart-grid backdrop */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            'linear-gradient(#EDEAE3 1px, transparent 1px), linear-gradient(90deg, #EDEAE3 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }}
      />

      <div className="relative flex flex-col items-center justify-center px-6 py-20">
        {/* Registry / brand line */}
        <div className="mb-10 flex items-center gap-3">
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#5C5C59]">No. 0X42</span>
          <span className="h-3 w-px bg-white/10" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#B8935A]">SMC-90F</span>
        </div>

        <h1 className="mb-1 text-center text-5xl italic" style={{ fontFamily: 'var(--font-serif)' }}>
          MetalMind
        </h1>
        <p className="mb-12 font-mono text-[10px] uppercase tracking-[0.35em] text-[#5C5C59]">
          SMCForge — new account
        </p>

        {/* Certificate-style card */}
        <div className="relative w-full max-w-md">
          <span className="absolute -left-px -top-px h-3 w-3 border-l border-t border-[#B8935A]" />
          <span className="absolute -right-px -top-px h-3 w-3 border-r border-t border-[#B8935A]" />
          <span className="absolute -bottom-px -left-px h-3 w-3 border-b border-l border-[#B8935A]" />
          <span className="absolute -bottom-px -right-px h-3 w-3 border-b border-r border-[#B8935A]" />

          <div className="border border-white/10 bg-[#131315] px-8 py-10">
            <h2 className="mb-1 text-lg font-normal text-[#EDEAE3]">Create account</h2>
            <p className="mb-8 text-[13px] text-[#8B9099]">Start trading with AI-powered signals and analytics.</p>

            <RegisterForm onSubmit={handleRegister} isLoading={isLoading} />

            <p className="mt-8 text-center text-[13px] text-[#8B9099]">
              Already have an account?{' '}
              <Link href="/auth/login" className="text-[#B8935A] hover:text-[#D1AC79]">
                Sign in
              </Link>
            </p>
          </div>
        </div>

        <p className="mt-10 font-mono text-[9px] uppercase tracking-[0.25em] text-[#454543]">
          XGBoost · SHAP · ChromaDB · Walk-forward CV
        </p>
      </div>
    </div>
  );
}
