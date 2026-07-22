'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { signIn, useSession } from 'next-auth/react';
import { LoginForm } from '@/components/Auth/LoginForm';
import { toast } from 'sonner';
import Link from 'next/link';
import ThemeToggle from '@/components/Common/ThemeToggle';
import { Instrument_Serif, IBM_Plex_Mono } from 'next/font/google';
import { apiClient } from '@/lib/api-client';

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

type LoginValues = {
  email: string;
  password: string;
  totp_code?: string;
};

// Live ticker that fetches real prices from the API
function LiveTickerStrip() {
  interface TickerItem { label: string; value: string; delta: string; up: boolean }
  const [items, setItems] = useState<TickerItem[]>([
    { label: 'XAU/USD', value: '—', delta: 'LOADING', up: true },
    { label: 'XAG/USD', value: '—', delta: 'LOADING', up: true },
  ]);

  useEffect(() => {
    let mounted = true;
    const fetchPrices = async () => {
      try {
        const [gold, silver] = await Promise.all([
          apiClient.getLivePrice('gold'),
          apiClient.getLivePrice('silver'),
        ]);
        if (!mounted) return;
        setItems([
          { label: 'XAU/USD', value: gold.price.toLocaleString(undefined, { minimumFractionDigits: 2 }), delta: 'LIVE', up: true },
          { label: 'XAG/USD', value: silver.price.toLocaleString(undefined, { minimumFractionDigits: 2 }), delta: 'LIVE', up: true },
        ]);
      } catch {
        if (mounted) {
          setItems([
            { label: 'XAU/USD', value: '—', delta: 'OFFLINE', up: false },
            { label: 'XAG/USD', value: '—', delta: 'OFFLINE', up: false },
          ]);
        }
      }
    };
    fetchPrices();
    const interval = setInterval(fetchPrices, 30000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const tickerLoop = [...items, ...items, ...items, ...items, ...items];

  return (
    <div className="flex animate-[ticker_32s_linear_infinite] gap-10 px-6 py-2" style={{ width: 'max-content', fontFamily: 'var(--font-mono)' }}>
      {tickerLoop.map((t, i) => (
        <span key={i} className="flex items-center gap-2 text-[11px] tracking-wide text-[#8B9099]">
          <span className="text-[#5C5C59]">{t.label}</span>
          <span className="text-[#EDEAE3]">{t.value}</span>
          <span className={t.up ? 'text-[#B8935A]' : 'text-[#8B9099]'}>{t.delta}</span>
        </span>
      ))}
    </div>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const { status } = useSession();
  const [isLoading, setIsLoading] = useState(false);
  const [requires2fa, setRequires2fa] = useState(false);

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (status === 'authenticated') {
      router.replace('/dashboard');
    }
  }, [status, router]);

  // Show nothing while checking session (prevents flash of login form)
  if (status === 'loading' || status === 'authenticated') {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0A0B]">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#B8935A] border-t-transparent" />
      </div>
    );
  }

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
    <div
      className={`${serif.variable} ${mono.variable} relative min-h-screen overflow-hidden bg-[#0A0A0B] text-[#EDEAE3]`}
    >
      {/* Ticker strip — live prices from API */}
      <div className="relative overflow-hidden whitespace-nowrap border-b border-white/[0.06]">
        <LiveTickerStrip />
      </div>

      <div className="absolute right-6 top-14 z-50">
        <ThemeToggle />
      </div>

      {/* Faint chart-grid backdrop, not a dot texture */}
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
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#5C5C59]">No. 0X41</span>
          <span className="h-3 w-px bg-white/10" />
          <span className="font-mono text-[10px] tracking-[0.3em] text-[#B8935A]">SMC-90F</span>
        </div>

        <h1 className="mb-1 text-center text-5xl italic" style={{ fontFamily: 'var(--font-serif)' }}>
          MetalMind
        </h1>
        <p className="mb-12 font-mono text-[10px] uppercase tracking-[0.35em] text-[#5C5C59]">
          SMCForge — signal terminal
        </p>

        {/* Certificate-style card */}
        <div className="relative w-full max-w-md">
          <span className="absolute -left-px -top-px h-3 w-3 border-l border-t border-[#B8935A]" />
          <span className="absolute -right-px -top-px h-3 w-3 border-r border-t border-[#B8935A]" />
          <span className="absolute -bottom-px -left-px h-3 w-3 border-b border-l border-[#B8935A]" />
          <span className="absolute -bottom-px -right-px h-3 w-3 border-b border-r border-[#B8935A]" />

          <div className="border border-white/10 bg-[#131315] px-8 py-10">
            <h2 className="mb-1 text-lg font-normal text-[#EDEAE3]">Sign in</h2>
            <p className="mb-8 text-[13px] text-[#8B9099]">Access your signals, models and analytics.</p>

            <LoginForm onSubmit={handleLogin} isLoading={isLoading} showOtp={requires2fa} />

            <p className="mt-8 text-center text-[13px] text-[#8B9099]">
              No account?{' '}
              <Link href="/auth/register" className="text-[#B8935A] hover:text-[#D1AC79]">
                Register
              </Link>
            </p>
            <p className="mt-3 text-center">
              <Link href="/auth/forgot-password" className="text-[11px] text-[#5C5C59] hover:text-[#B8935A] transition-colors">
                Forgot password?
              </Link>
            </p>
          </div>
        </div>

        <p className="mt-10 font-mono text-[9px] uppercase tracking-[0.25em] text-[#454543]">
          XGBoost · SHAP · ChromaDB · Walk-forward CV
        </p>
      </div>

      <style jsx global>{`
        @keyframes ticker {
          from {
            transform: translateX(0);
          }
          to {
            transform: translateX(-33.333%);
          }
        }
      `}</style>
    </div>
  );
}