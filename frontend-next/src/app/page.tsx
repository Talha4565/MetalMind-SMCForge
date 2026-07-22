'use client';

import { useEffect, useRef, useState, useMemo } from 'react';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { ArrowRight, Zap, TrendingUp, Layers, Cpu, ChevronDown, BarChart3 } from 'lucide-react';
import LiveTicker from '@/components/Landing/LiveTicker';

/* ──────────────────────────────────────────────
   Intersection Observer — triggers on scroll
   ────────────────────────────────────────────── */
function useReveal(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

/* ──────────────────────────────────────────────
   Animated counter — counts up on reveal
   ────────────────────────────────────────────── */
function AnimatedNumber({ target, suffix = '', duration = 1800 }: { target: number; suffix?: string; duration?: number }) {
  const { ref, visible } = useReveal(0.3);
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!visible) return;
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); } else { setCount(start); }
    }, 16);
    return () => clearInterval(timer);
  }, [visible, target, duration]);
  return <span ref={ref}>{count}{suffix}</span>;
}

/* ──────────────────────────────────────────────
   Parallax — element moves with scroll
   ────────────────────────────────────────────── */
function useParallax(speed = 0.3) {
  const ref = useRef<HTMLDivElement>(null);
  const [offset, setOffset] = useState(0);
  useEffect(() => {
    const handleScroll = () => {
      if (!ref.current) return;
      const rect = ref.current.getBoundingClientRect();
      const scrolled = (window.innerHeight - rect.top) / window.innerHeight;
      setOffset(scrolled * speed * 100);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, [speed]);
  return { ref, offset };
}

/* ──────────────────────────────────────────────
   Floating dust particles — pre-computed, stable
   ────────────────────────────────────────────── */
function Particles({ color, count }: { color: 'gold' | 'silver'; count: number }) {
  const goldColors = ['rgba(212,175,55,0.18)', 'rgba(245,200,90,0.10)', 'rgba(180,150,50,0.08)'];
  const silverColors = ['rgba(176,184,200,0.14)', 'rgba(200,210,220,0.08)', 'rgba(150,160,180,0.06)'];
  const palette = color === 'gold' ? goldColors : silverColors;

  // Pre-compute stable particle positions — no Math.random() in render
  const particles = useMemo(() => {
    return Array.from({ length: count }).map((_, i) => ({
      id: i,
      size: 2 + ((i * 7 + 3) % 5),
      left: (i * 37 + 13) % 100,
      delay: (i * 3.7) % 9,
      duration: 6 + (i % 11),
      drift: -30 - ((i * 17) % 70),
      colorIdx: i % palette.length,
    }));
  }, [count, palette.length]);

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
      {particles.map(p => (
        <div
          key={p.id}
          className="absolute rounded-full"
          style={{
            width: `${p.size}px`, height: `${p.size}px`,
            left: `${p.left}%`, bottom: '-10px',
            backgroundColor: palette[p.colorIdx],
            animation: `float-up ${p.duration}s ${p.delay}s infinite linear`,
            '--drift': `${p.drift}px`,
            opacity: 0,
          } as React.CSSProperties}
        />
      ))}
    </div>
  );
}

/* ──────────────────────────────────────────────
   SECTION 1 — THE VAULT (hero)
   ────────────────────────────────────────────── */
function HeroSection({ isAuthenticated }: { isAuthenticated: boolean }) {
  const { offset: parallaxY } = useParallax(0.08);
  const goldHref = isAuthenticated ? '/dashboard/gold' : '/auth/login';
  const silverHref = isAuthenticated ? '/dashboard/silver' : '/auth/login';

  return (
    <section className="relative min-h-screen flex flex-col items-center justify-center bg-[#040405] text-[#e8e4dc] overflow-hidden">
      {/* Grain */}
      <svg className="fixed inset-0 w-full h-full pointer-events-none opacity-[0.022] z-50" aria-hidden="true">
        <filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" /><feColorMatrix type="saturation" values="0" /></filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>

      {/* Gold dust — left side */}
      <div className="absolute left-0 top-0 w-1/2 h-full pointer-events-none"><Particles color="gold" count={30} /></div>
      {/* Silver dust — right side */}
      <div className="absolute right-0 top-0 w-1/2 h-full pointer-events-none"><Particles color="silver" count={30} /></div>

      {/* Gold vault light — moves slightly with scroll */}
      <div className="absolute pointer-events-none transition-transform duration-700"
        style={{
          top: `${-parallaxY}px`, left: 0,
          width: '900px', height: '600px',
          background: 'radial-gradient(ellipse at 25% 5%, rgba(212,175,55,0.10) 0%, rgba(212,175,55,0.05) 25%, rgba(212,175,55,0.01) 50%, transparent 70%)',
        }} />

      {/* Silver vault light */}
      <div className="absolute pointer-events-none transition-transform duration-700"
        style={{
          top: `${-parallaxY}px`, right: 0,
          width: '900px', height: '600px',
          background: 'radial-gradient(ellipse at 75% 5%, rgba(176,184,200,0.09) 0%, rgba(176,184,200,0.04) 25%, rgba(176,184,200,0.01) 50%, transparent 70%)',
        }} />

      {/* Convergence */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[500px] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(200,190,160,0.05) 0%, transparent 55%)' }} />

      <div className="relative z-10 flex flex-col items-center text-center space-y-10 max-w-5xl w-full px-6">
        {/* Eyebrow */}
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#d4af37]/20 bg-[#d4af37]/[0.04] animate-in fade-in duration-1000">
          <Zap className="w-3.5 h-3.5 text-[#d4af37]" aria-hidden="true" />
          <span className="text-[11px] font-medium uppercase tracking-[0.22em] text-[#a89a6a]">Real-time XAU/XAG ML signals</span>
        </div>

        {/* Live Ticker */}
        <div className="animate-in fade-in slide-in-from-top-4 duration-1000 delay-300 fill-mode-both">
          <LiveTicker />
        </div>

        {/* Hero text */}
        <div className="space-y-6 animate-in fade-in slide-in-from-top-8 duration-1200 delay-500 fill-mode-both">
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-black tracking-[-0.025em] leading-[0.92]">
            Two metals.
            <br />
            <span className="bg-gradient-to-b from-[#e5c158] via-[#f8e9a8] via-25% via-[#bf9530] via-55% via-[#f8e9a8] via-80% to-[#c9a44b] bg-clip-text text-transparent">
              One engine.
            </span>
          </h1>
          <p className="text-lg md:text-xl text-[#8a8578] max-w-2xl mx-auto leading-relaxed tracking-wide">
            Gold and silver signals from XGBoost models trained on 20 years of tick data.
            Separate tuned parameters per metal. SHAP explainability on every prediction.
          </p>
        </div>

        {/* Dual CTAs */}
        <div className="flex flex-col sm:flex-row items-center gap-4 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-800 fill-mode-both">
          <Link href={goldHref}
            className="group px-9 py-4 bg-[#d4af37] hover:bg-[#e5c158] text-[#0a0a05] font-bold rounded-xl transition-all duration-500 shadow-[0_0_40px_-8px_rgba(212,175,55,0.3)] hover:shadow-[0_0_60px_-8px_rgba(212,175,55,0.5)] hover:scale-105 flex items-center gap-2">
            🥇 {isAuthenticated ? 'Gold Dashboard' : 'Sign In'} <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" aria-hidden="true" />
          </Link>
          <Link href={silverHref}
            className="group px-9 py-4 bg-[#b0b8c8] hover:bg-[#c4ccd8] text-[#0a0a05] font-bold rounded-xl transition-all duration-500 shadow-[0_0_40px_-8px_rgba(176,184,200,0.25)] hover:shadow-[0_0_60px_-8px_rgba(176,184,200,0.45)] hover:scale-105 flex items-center gap-2">
            🥈 {isAuthenticated ? 'Silver Dashboard' : 'Sign In'} <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" aria-hidden="true" />
          </Link>
        </div>

        {/* GitHub + Disclaimer */}
        <div className="flex flex-col items-center gap-3 animate-in fade-in duration-1000 delay-1000 fill-mode-both">
          <Link href="https://github.com/Talha4565/MetalMind-SMCForge"
            className="text-sm font-medium text-[#8a8578] hover:text-[#d4af37] transition-colors duration-300">
            View source on GitHub
          </Link>
          <p className="text-[11px] text-[#8a8578]/50">Past performance does not guarantee future results. For educational purposes only.</p>
        </div>

        {/* Scroll indicator */}
        <div className="pt-4 animate-in fade-in duration-1000 delay-1500 fill-mode-both">
          <ChevronDown className="w-5 h-5 text-[#8a8578]/40 animate-bounce" />
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────
   SECTION 2 — THE SPLIT (gold vs silver)
   ────────────────────────────────────────────── */
function SplitSection({ isAuthenticated }: { isAuthenticated: boolean }) {
  const { ref, visible } = useReveal(0.12);
  const goldHref = isAuthenticated ? '/dashboard/gold' : '/auth/login';
  const silverHref = isAuthenticated ? '/dashboard/silver' : '/auth/login';
  const centerLineRef = useRef<HTMLDivElement>(null);
  const [lineProgress, setLineProgress] = useState(0);

  useEffect(() => {
    if (!visible) return;
    const el = centerLineRef.current;
    if (!el) return;
    const onScroll = () => {
      const rect = el.getBoundingClientRect();
      const progress = Math.max(0, Math.min(1, 1 - rect.top / window.innerHeight));
      setLineProgress(progress);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [visible]);

  const barChartGold = useMemo(() => Array.from({ length: 24 }, (_, i) => ({
    h: 0.4 + Math.sin(i * 0.45 + 0.3) * 0.35 + Math.sin(i * 0.22) * 0.2,
    delay: i * 60,
  })), []);
  const barChartSilver = useMemo(() => Array.from({ length: 24 }, (_, i) => ({
    h: 0.35 + Math.sin(i * 0.42 + 1.8) * 0.3 + Math.sin(i * 0.19) * 0.2,
    delay: i * 60,
  })), []);

  return (
    <section ref={ref} className="relative min-h-screen bg-[#040405] flex items-center overflow-hidden">
      {/* Split background glows */}
      <div className="absolute inset-0 flex">
        <div className="w-1/2 h-full transition-all duration-[2000ms]"
          style={{ background: visible ? 'radial-gradient(ellipse at 80% 50%, rgba(212,175,55,0.06) 0%, transparent 60%)' : 'transparent' }} />
        <div className="w-1/2 h-full transition-all duration-[2000ms]"
          style={{ background: visible ? 'radial-gradient(ellipse at 20% 50%, rgba(176,184,200,0.05) 0%, transparent 60%)' : 'transparent' }} />
      </div>

      {/* Center divider — draws down on scroll */}
      <div ref={centerLineRef} className="absolute left-1/2 top-0 bottom-0 w-px pointer-events-none"
        style={{
          background: `linear-gradient(to bottom, transparent 0%, rgba(200,190,160,${0.35 * lineProgress}) ${lineProgress * 100}%, transparent ${lineProgress * 100}%)`,
          transition: 'background 0.3s ease',
        }} />

      <div className="relative z-10 w-full max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 gap-0">
        {/* ── Gold panel ── */}
        <div className="flex flex-col items-center text-center px-8 py-12 transition-all duration-[1400ms] ease-out"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateX(0)' : 'translateX(-80px)' }}>
          <span className="text-[10px] uppercase tracking-[0.25em] text-[#d4af37] font-bold mb-4">🥇 GOLD</span>
          <h2 className="font-black font-mono text-5xl md:text-6xl text-[#e8e4dc] mb-2">XAU/USD</h2>
          <div className="text-4xl font-black font-mono text-[#d4af37] tabular-nums my-4">
            <AnimatedNumber target={83} suffix="%" duration={2000} />
          </div>
          <p className="text-sm text-[#8a8578] mb-1">training accuracy</p>
          <div className="flex items-center gap-3 mt-1 mb-6">
            <span className="text-[10px] text-[#8a8578]/60">100 features</span>
            <span className="text-[10px] text-[#8a8578]/40">·</span>
            <span className="text-[10px] text-[#8a8578]/60">4-year window</span>
            <span className="text-[10px] text-[#8a8578]/40">·</span>
            <span className="text-[10px] text-[#8a8578]/60">AUC 0.74</span>
          </div>
          {/* Gold bar chart */}
          <div className="flex items-end gap-[2px] h-16 mb-6 opacity-40">
            {barChartGold.map((b, i) => (
              <div key={i} className="w-[6px] bg-[#d4af37]/60 transition-all duration-700 ease-out"
                style={{ height: visible ? `${Math.max(5, b.h * 100)}%` : '0%', transitionDelay: `${b.delay}ms` }} />
            ))}
          </div>
          <Link href={goldHref}
            className="inline-flex items-center gap-2 px-8 py-3 bg-[#d4af37] hover:bg-[#e5c158] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_30px_-6px_rgba(212,175,55,0.25)] hover:shadow-[0_0_50px_-6px_rgba(212,175,55,0.4)] hover:scale-105">
            {isAuthenticated ? 'Enter Gold Dashboard' : 'Sign In'} <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* ── Silver panel ── */}
        <div className="flex flex-col items-center text-center px-8 py-12 transition-all duration-[1400ms] ease-out"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateX(0)' : 'translateX(80px)' }}>
          <span className="text-[10px] uppercase tracking-[0.25em] text-[#b0b8c8] font-bold mb-4">🥈 SILVER</span>
          <h2 className="font-black font-mono text-5xl md:text-6xl text-[#e8e4dc] mb-2">XAG/USD</h2>
          <div className="text-4xl font-black font-mono text-[#b0b8c8] tabular-nums my-4">
            <AnimatedNumber target={74} suffix="%" duration={2000} />
          </div>
          <p className="text-sm text-[#8a8578] mb-1">training accuracy</p>
          <div className="flex items-center gap-3 mt-1 mb-6">
            <span className="text-[10px] text-[#8a8578]/60">89 features</span>
            <span className="text-[10px] text-[#8a8578]/40">·</span>
            <span className="text-[10px] text-[#8a8578]/60">4-year window</span>
            <span className="text-[10px] text-[#8a8578]/40">·</span>
            <span className="text-[10px] text-[#8a8578]/60">AUC 0.73</span>
          </div>
          {/* Silver bar chart */}
          <div className="flex items-end gap-[2px] h-16 mb-6 opacity-40">
            {barChartSilver.map((b, i) => (
              <div key={i} className="w-[6px] bg-[#b0b8c8]/60 transition-all duration-700 ease-out"
                style={{ height: visible ? `${Math.max(5, b.h * 100)}%` : '0%', transitionDelay: `${b.delay}ms` }} />
            ))}
          </div>
          <Link href={silverHref}
            className="inline-flex items-center gap-2 px-8 py-3 bg-[#b0b8c8] hover:bg-[#c4ccd8] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_30px_-6px_rgba(176,184,200,0.2)] hover:shadow-[0_0_50px_-6px_rgba(176,184,200,0.35)] hover:scale-105">
            {isAuthenticated ? 'Enter Silver Dashboard' : 'Sign In'} <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────
   SECTION 3 — THE ENGINE (pipeline)
   ────────────────────────────────────────────── */
function EngineSection() {
  const { ref, visible } = useReveal(0.15);
  const steps = [
    { icon: Layers, label: 'OHLCV Data', detail: '4 timeframes · 20 years · MT5 live feed' },
    { icon: Cpu, label: '100 Features', detail: 'SMC concepts · Volume micro · Multi-TF alignment' },
    { icon: TrendingUp, label: 'XGBoost', detail: 'Optuna-tuned · Walk-forward validated · 82.7% gold' },
    { icon: Zap, label: 'SHAP', detail: 'Per-prediction explainability · Feature attribution' },
    { icon: ArrowRight, label: 'Signal', detail: 'BUY / SELL / HOLD · TP & SL · Confidence score' },
  ];

  return (
    <section ref={ref} className="relative min-h-screen bg-[#060609] flex flex-col items-center justify-center py-24 overflow-hidden">
      {/* Section background distinction — slightly lighter than hero */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#040405] via-[#060609] to-[#040405] pointer-events-none" />
      {/* Center tech glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at center, rgba(16,185,129,0.04) 0%, transparent 60%)' }} />

      <div className="relative z-10 max-w-4xl w-full px-6">
        <div className="text-center mb-24 transition-all duration-1000"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(30px)' }}>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[#8a8578] font-bold mb-4">How it works</p>
          <h2 className="text-4xl md:text-5xl font-black text-[#e8e4dc] tracking-[-0.02em]">
            From tick data to trading signal
          </h2>
        </div>

        {/* Pipeline flow */}
        <div className="relative">
          {/* Connecting line — draws across on reveal */}
          <div className="absolute top-8 left-[8%] right-[8%] h-px transition-all duration-[2500ms] ease-out"
            style={{
              background: visible
                ? 'linear-gradient(to right, rgba(212,175,55,0.5), rgba(16,185,129,0.5), rgba(176,184,200,0.5))'
                : 'transparent',
            }} />

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={step.label}
                  className="flex flex-col items-center text-center transition-all duration-1000 ease-out"
                  style={{
                    opacity: visible ? 1 : 0,
                    transform: visible ? 'translateY(0) scale(1)' : 'translateY(40px) scale(0.9)',
                    transitionDelay: `${i * 200}ms`,
                  }}>
                  <div className="w-16 h-16 rounded-full border border-[#d4af37]/20 bg-[#0a0b0f] flex items-center justify-center mb-4 relative z-10 shadow-[0_0_20px_-4px_rgba(212,175,55,0.08)]">
                    <Icon className="w-6 h-6 text-[#d4af37]" />
                  </div>
                  <p className="text-sm font-bold font-mono text-[#e8e4dc] mb-1">{step.label}</p>
                  <p className="text-[10px] text-[#8a8578]/70 leading-relaxed max-w-[140px]">{step.detail}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────
   SECTION 4 — THE NUMBERS
   ────────────────────────────────────────────── */
function NumbersSection() {
  const { ref, visible } = useReveal(0.15);

  return (
    <section ref={ref} className="relative min-h-[80vh] bg-[#040405] flex flex-col items-center justify-center py-24">
      {/* Subtle emerald depth glow */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] pointer-events-none"
        style={{ background: 'radial-gradient(ellipse at 50% 100%, rgba(16,185,129,0.03) 0%, transparent 60%)' }} />

      <div className="relative z-10 max-w-4xl w-full px-6">
        <div className="text-center mb-20 transition-all duration-1000"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}>
          <p className="text-[10px] uppercase tracking-[0.3em] text-[#8a8578] font-bold mb-4">By the numbers</p>
          <h2 className="text-4xl md:text-5xl font-black text-[#e8e4dc] tracking-[-0.02em]">
            Real performance. Real data.
          </h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-20">
          {[
            { value: 20, suffix: 'yrs', label: 'Tick Data', sub: '1998–2026' },
            { value: 104, suffix: 'K', label: 'Gold Bars', sub: '15-minute candles' },
            { value: 100, suffix: '', label: 'Features', sub: 'per prediction' },
            { value: 245, suffix: '', label: 'Tests', sub: '100% pass rate' },
          ].map((stat, i) => (
            <div key={stat.label}
              className="flex flex-col items-center text-center transition-all duration-1000 ease-out"
              style={{
                opacity: visible ? 1 : 0,
                transform: visible ? 'translateY(0)' : 'translateY(30px)',
                transitionDelay: `${i * 150}ms`,
              }}>
              <div className="text-4xl md:text-5xl font-black font-mono text-[#d4af37] tabular-nums mb-2">
                <AnimatedNumber target={stat.value} suffix={stat.suffix} duration={2200} />
              </div>
              <p className="text-sm font-bold text-[#e8e4dc]">{stat.label}</p>
              <p className="text-[10px] text-[#8a8578]/60">{stat.sub}</p>
            </div>
          ))}
        </div>

        {/* Backtest card */}
        <div className="max-w-2xl mx-auto p-8 rounded-2xl border border-[#d4af37]/15 bg-[#0a0b0f] transition-all duration-[2000ms] ease-out"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'scale(1)' : 'scale(0.93)' }}>
          <div className="flex items-center gap-2 mb-6 justify-center">
            <BarChart3 className="w-4 h-4 text-[#d4af37]" />
            <span className="text-[10px] uppercase tracking-[0.2em] text-[#8a8578] font-bold">Walk-Forward Backtest</span>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { label: 'Gold Win Rate', value: '41.3%', color: 'text-[#d4af37]' },
              { label: 'Silver Win Rate', value: '50.0%', color: 'text-[#b0b8c8]' },
              { label: 'Profit Factor', value: '1.44', color: 'text-[#16b979]' },
              { label: 'Total Trades', value: '1,674', color: 'text-[#e8e4dc]' },
            ].map(m => (
              <div key={m.label} className="text-center">
                <p className="text-[9px] uppercase tracking-[0.2em] text-[#8a8578] font-bold mb-1">{m.label}</p>
                <p className={`text-2xl font-black font-mono ${m.color}`}>{m.value}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────
   SECTION 5 — CHOOSE YOUR METAL
   ────────────────────────────────────────────── */
function ChooseSection({ isAuthenticated }: { isAuthenticated: boolean }) {
  const { ref, visible } = useReveal(0.15);
  const goldHref = isAuthenticated ? '/dashboard/gold' : '/auth/login';
  const silverHref = isAuthenticated ? '/dashboard/silver' : '/auth/login';

  return (
    <section ref={ref} className="relative min-h-[70vh] bg-[#060609] flex flex-col items-center justify-center py-24 overflow-hidden">
      {/* Section bg distinction */}
      <div className="absolute inset-0 bg-gradient-to-b from-[#040405] via-[#060609] to-[#040405] pointer-events-none" />
      {/* Dual glow */}
      <div className="absolute inset-0 pointer-events-none"
        style={{
          background: visible
            ? 'radial-gradient(ellipse at 30% 50%, rgba(212,175,55,0.06) 0%, transparent 50%), radial-gradient(ellipse at 70% 50%, rgba(176,184,200,0.05) 0%, transparent 50%)'
            : 'transparent',
          transition: 'background 2s ease',
        }} />

      <div className="relative z-10 max-w-3xl w-full px-6 text-center">
        <div className="mb-14 transition-all duration-1000"
          style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateY(0)' : 'translateY(20px)' }}>
          <h2 className="text-4xl md:text-5xl font-black text-[#e8e4dc] tracking-[-0.02em] mb-4">
            Choose your metal
          </h2>
          <p className="text-lg text-[#8a8578]">Same engine. Separate tuned models. Pick where to start.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Gold */}
          <Link href={goldHref}
            className="group flex flex-col items-center rounded-2xl border border-[#d4af37]/30 bg-[#0a0b0f] px-10 py-12 transition-all duration-700 ease-out hover:border-[#d4af37]/60 hover:shadow-[0_0_60px_-12px_rgba(212,175,55,0.2)] hover:scale-[1.03]"
            style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateX(0)' : 'translateX(-50px)', transitionDelay: '200ms' }}>
            <span className="text-5xl mb-4">🥇</span>
            <span className="text-[10px] uppercase tracking-[0.25em] text-[#d4af37] font-bold mb-2">Gold</span>
            <span className="font-black font-mono text-3xl text-[#e8e4dc] mb-3">XAU/USD</span>
            <span className="text-sm text-[#16b979] font-semibold mb-4">82.7% accuracy</span>
            <span className="inline-flex items-center gap-2 px-8 py-3 bg-[#d4af37] hover:bg-[#e5c158] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_30px_-6px_rgba(212,175,55,0.25)]">
              {isAuthenticated ? 'Enter Dashboard' : 'Sign In'} <ArrowRight className="w-4 h-4" />
            </span>
          </Link>

          {/* Silver */}
          <Link href={silverHref}
            className="group flex flex-col items-center rounded-2xl border border-[#b0b8c8]/30 bg-[#0a0b0f] px-10 py-12 transition-all duration-700 ease-out hover:border-[#b0b8c8]/60 hover:shadow-[0_0_60px_-12px_rgba(176,184,200,0.15)] hover:scale-[1.03]"
            style={{ opacity: visible ? 1 : 0, transform: visible ? 'translateX(0)' : 'translateX(50px)', transitionDelay: '400ms' }}>
            <span className="text-5xl mb-4">🥈</span>
            <span className="text-[10px] uppercase tracking-[0.25em] text-[#b0b8c8] font-bold mb-2">Silver</span>
            <span className="font-black font-mono text-3xl text-[#e8e4dc] mb-3">XAG/USD</span>
            <span className="text-sm text-[#f59e0b] font-semibold mb-4">73.9% accuracy</span>
            <span className="inline-flex items-center gap-2 px-8 py-3 bg-[#b0b8c8] hover:bg-[#c4ccd8] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_30px_-6px_rgba(176,184,200,0.2)]">
              {isAuthenticated ? 'Enter Dashboard' : 'Sign In'} <ArrowRight className="w-4 h-4" />
            </span>
          </Link>
        </div>

        <p className="mt-10 text-[11px] text-[#8a8578]/40">Past performance does not guarantee future results. For educational purposes only.</p>
      </div>
    </section>
  );
}

/* ──────────────────────────────────────────────
   PAGE
   ────────────────────────────────────────────── */
export default function Home() {
  const { data: session, status } = useSession();
  const isAuthenticated = status === 'authenticated';

  return (
    <main className="bg-[#040405] text-[#e8e4dc]">
      {/* Session-aware top navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-[#040405]/80 backdrop-blur-md border-b border-white/[0.06]">
        <Link href="/" className="font-mono text-[11px] tracking-[0.3em] text-[#5C5C59] hover:text-[#B8935A] transition-colors">
          METALMIND
        </Link>
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <Link
              href="/dashboard"
              className="px-5 py-2 bg-[#d4af37] hover:bg-[#e5c158] text-[#0a0a05] text-sm font-bold rounded-lg transition-all duration-300 flex items-center gap-2"
            >
              Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <Link
              href="/auth/login"
              className="px-5 py-2 border border-[#B8935A]/40 hover:border-[#B8935A] text-[#B8935A] text-sm font-semibold rounded-lg transition-all duration-300"
            >
              Sign In
            </Link>
          )}
        </div>
      </nav>

      <style jsx global>{`
        @keyframes float-up {
          0%   { transform: translateY(0) translateX(0); opacity: 0; }
          10%  { opacity: 1; }
          85%  { opacity: 0.3; }
          100% { transform: translateY(-100vh) translateX(var(--drift, -20px)); opacity: 0; }
        }
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slide-in-from-top-4 { from { transform: translateY(-1rem); } to { transform: translateY(0); } }
        @keyframes slide-in-from-top-8 { from { transform: translateY(-2rem); } to { transform: translateY(0); } }
        @keyframes slide-in-from-bottom-4 { from { transform: translateY(1rem); } to { transform: translateY(0); } }
        .animate-in { animation-duration: 0.6s; animation-fill-mode: both; }
        .fade-in { animation-name: fade-in; }
        .slide-in-from-top-4 { animation-name: slide-in-from-top-4; }
        .slide-in-from-top-8 { animation-name: slide-in-from-top-8; }
        .slide-in-from-bottom-4 { animation-name: slide-in-from-bottom-4; }
        .delay-300 { animation-delay: 0.3s; }
        .delay-500 { animation-delay: 0.5s; }
        .delay-800 { animation-delay: 0.8s; }
        .delay-1000 { animation-delay: 1s; }
        .delay-1500 { animation-delay: 1.5s; }
        .duration-1000 { animation-duration: 1s; }
        .duration-1200 { animation-duration: 1.2s; }
        .fill-mode-both { animation-fill-mode: both; }
        html { scroll-behavior: smooth; }
      `}</style>

      <HeroSection isAuthenticated={isAuthenticated} />
      <SplitSection isAuthenticated={isAuthenticated} />
      <EngineSection />
      <NumbersSection />
      <ChooseSection isAuthenticated={isAuthenticated} />
    </main>
  );
}
