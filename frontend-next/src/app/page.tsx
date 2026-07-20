import Link from 'next/link';
import { ArrowRight, Zap } from 'lucide-react';
import LiveTicker from '@/components/Landing/LiveTicker';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center bg-[#040405] text-[#e8e4dc] p-6 relative overflow-hidden">
      {/* ── Grain texture overlay ── */}
      <svg className="fixed inset-0 w-full h-full pointer-events-none opacity-[0.022]" aria-hidden="true">
        <filter id="grain">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
          <feColorMatrix type="saturation" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" />
      </svg>

      {/* ── Gold vault light — top-left, warm ── */}
      <div
        className="absolute top-0 left-0 w-[800px] h-[550px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 30% 0%, rgba(212,175,55,0.08) 0%, rgba(212,175,55,0.04) 30%, rgba(212,175,55,0.01) 55%, transparent 75%)',
        }}
      />

      {/* ── Silver vault light — top-right, cool ── */}
      <div
        className="absolute top-0 right-0 w-[800px] h-[550px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 70% 0%, rgba(176,184,200,0.07) 0%, rgba(176,184,200,0.03) 30%, rgba(176,184,200,0.01) 55%, transparent 75%)',
        }}
      />

      {/* ── Convergence zone — where gold meets silver in the center ── */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[400px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 50% 0%, rgba(200,190,160,0.04) 0%, transparent 60%)',
        }}
      />

      {/* ── Depth glow behind dashboard ── */}
      <div
        className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at 50% 100%, rgba(16,185,129,0.04) 0%, transparent 70%)',
        }}
      />

      <div className="relative z-10 flex flex-col items-center text-center space-y-12 max-w-5xl w-full">
        {/* ── Eyebrow — premium pill ── */}
        <div className="flex items-center gap-2 px-4 py-1.5 rounded-full border border-[#d4af37]/20 bg-[#d4af37]/[0.04]">
          <Zap className="w-3.5 h-3.5 text-[#d4af37]" aria-hidden="true" />
          <span className="text-[11px] font-medium uppercase tracking-[0.22em] text-[#a89a6a]">
            Real-time XAU/XAG ML signals
          </span>
        </div>

        {/* ── Live price ticker ── */}
        <LiveTicker />

        {/* ── Hero headline ── */}
        <div className="space-y-6">
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

        {/* ── Dual CTA row ── */}
        <div className="flex flex-col items-center gap-5">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            {/* Gold CTA */}
            <Link
              href="/dashboard/gold"
              className="group px-9 py-4 bg-[#d4af37] hover:bg-[#e5c158] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_40px_-8px_rgba(212,175,55,0.3)] hover:shadow-[0_0_60px_-8px_rgba(212,175,55,0.45)] flex items-center justify-center gap-2"
            >
              🥇 Gold Dashboard
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" aria-hidden="true" />
            </Link>
            {/* Silver CTA */}
            <Link
              href="/dashboard/silver"
              className="group px-9 py-4 bg-[#b0b8c8] hover:bg-[#c4ccd8] text-[#0a0a05] font-bold rounded-xl transition-all duration-300 shadow-[0_0_40px_-8px_rgba(176,184,200,0.25)] hover:shadow-[0_0_60px_-8px_rgba(176,184,200,0.4)] flex items-center justify-center gap-2"
            >
              🥈 Silver Dashboard
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" aria-hidden="true" />
            </Link>
          </div>
          <Link
            href="https://github.com/Talha4565/MetalMind-SMCForge"
            className="text-sm font-medium text-[#8a8578] hover:text-[#d4af37] transition-colors duration-300"
          >
            View source on GitHub
          </Link>
        </div>

        {/* ── Hero destination cards: Gold & Silver ── */}
        <div className="w-full max-w-3xl pt-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* ── Gold ── */}
            <Link
              href="/dashboard/gold"
              className="group flex flex-col rounded-xl border border-[#d4af37]/25 bg-[#0a0b0f] px-8 py-8 text-left transition-all duration-500 hover:border-[#d4af37]/60 hover:shadow-[0_0_40px_-8px_rgba(212,175,55,0.18)] hover:scale-[1.02]"
            >
              <span className="text-[10px] uppercase tracking-[0.2em] text-[#d4af37] font-semibold">🥇 GOLD</span>
              <h2 className="font-black font-mono text-4xl text-[#e8e4dc] mt-3">XAU/USD</h2>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm font-semibold text-[#16b979]">82.7% accuracy</span>
                <span className="text-[10px] text-[#8a8578]/60">·</span>
                <span className="text-[10px] text-[#8a8578]/70">100 features</span>
              </div>
              <p className="mt-2 text-sm text-[#8a8578]/80 leading-relaxed">XGBoost · Smart Money Concepts · 4-year training window</p>
              <span className="mt-auto pt-5 text-sm font-medium text-[#d4af37] group-hover:brightness-125 transition-all duration-300">
                Open Gold Dashboard →
              </span>
            </Link>

            {/* ── Silver ── */}
            <Link
              href="/dashboard/silver"
              className="group flex flex-col rounded-xl border border-[#b0b8c8]/25 bg-[#0a0b0f] px-8 py-8 text-left transition-all duration-500 hover:border-[#b0b8c8]/60 hover:shadow-[0_0_40px_-8px_rgba(176,184,200,0.14)] hover:scale-[1.02]"
            >
              <span className="text-[10px] uppercase tracking-[0.2em] text-[#b0b8c8] font-semibold">🥈 SILVER</span>
              <h2 className="font-black font-mono text-4xl text-[#e8e4dc] mt-3">XAG/USD</h2>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm font-semibold text-[#f59e0b]">73.9% accuracy</span>
                <span className="text-[10px] text-[#8a8578]/60">·</span>
                <span className="text-[10px] text-[#8a8578]/70">89 features</span>
              </div>
              <p className="mt-2 text-sm text-[#8a8578]/80 leading-relaxed">Same engine · Separate parameters · Silver-specific tuning</p>
              <span className="mt-auto pt-5 text-sm font-medium text-[#b0b8c8] group-hover:brightness-125 transition-all duration-300">
                Open Silver Dashboard →
              </span>
            </Link>
          </div>
        </div>

        {/* ── Risk disclaimer ── */}
        <p className="text-[11px] text-[#8a8578]/50 max-w-md">
          Past performance does not guarantee future results. For educational purposes only.
        </p>

        {/* ── Dashboard screenshot peek ── */}
        <div className="relative w-full max-w-4xl mt-2">
          <div className="absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-[#040405] via-[#040405]/80 to-transparent z-10 pointer-events-none" />
          <div className="rounded-2xl border border-[#d4af37]/20 bg-[#0a0b0f] overflow-hidden shadow-[0_0_80px_-20px_rgba(212,175,55,0.06)]">
            {/* Title bar */}
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-white/[0.04] bg-[#0c0d12]">
              <span className="w-2.5 h-2.5 rounded-full bg-[#e84040]/70" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#d4af37]/50" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#16b979]/50" />
              <span className="ml-2 text-[10px] font-mono text-[#8a8578]/60 tracking-[0.15em] uppercase">MetalMind SMCForge</span>
            </div>
            {/* Terminal body */}
            <div className="relative h-[300px] md:h-[380px] bg-[#050508] flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 p-5 grid grid-cols-[1fr] sm:grid-cols-[200px_1fr_180px] gap-0.5 opacity-70">
                {/* Left panel */}
                <div className="hidden sm:flex flex-col border border-white/[0.03] rounded-lg bg-[#08090d] p-3 space-y-2.5">
                  <div className="h-1.5 w-14 bg-[#d4af37]/20 rounded-full" />
                  <div className="h-7 w-full bg-[#16b979]/[0.06] rounded-md border border-[#16b979]/10 flex items-center px-2.5">
                    <span className="text-[9px] font-mono font-bold text-[#16b979] tracking-wider">BUY</span>
                  </div>
                  <div className="space-y-2 mt-2">
                    {[0.42, 0.31, 0.26, 0.19, 0.14].map((w, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className="h-1 flex-1 bg-white/[0.03] rounded-full overflow-hidden">
                          <div className="h-full bg-[#16b979]/30 rounded-full transition-all" style={{ width: `${w * 100}%` }} />
                        </div>
                        <span className="text-[7px] font-mono text-[#8a8578]/60 w-7 text-right tabular-nums">{(w * 0.82).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>
                </div>
                {/* Center chart */}
                <div className="border border-white/[0.03] rounded-lg bg-[#08090d] relative overflow-hidden">
                  <svg className="absolute inset-0 w-full h-full" viewBox="0 0 600 300" preserveAspectRatio="none" aria-hidden="true">
                    <defs>
                      <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#16b979" stopOpacity="0.12" />
                        <stop offset="100%" stopColor="#16b979" stopOpacity="0" />
                      </linearGradient>
                      <linearGradient id="lineGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#16b979" stopOpacity="0.3" />
                        <stop offset="50%" stopColor="#16b979" stopOpacity="0.8" />
                        <stop offset="100%" stopColor="#d4af37" stopOpacity="0.6" />
                      </linearGradient>
                    </defs>
                    <path d="M0,200 C50,185 100,165 150,175 C200,185 250,125 300,105 C350,85 400,115 450,95 C500,75 550,65 600,55 L600,300 L0,300 Z" fill="url(#areaGrad)" />
                    <path d="M0,200 C50,185 100,165 150,175 C200,185 250,125 300,105 C350,85 400,115 450,95 C500,75 550,65 600,55" fill="none" stroke="url(#lineGrad)" strokeWidth="1.5" />
                  </svg>
                  <div className="absolute bottom-6 left-5 right-5 flex items-end gap-[1px] opacity-25">
                    {Array.from({ length: 48 }, (_, i) => {
                      const h = 18 + Math.sin(i * 0.35) * 28 + Math.sin(i * 0.17) * 14;
                      const up = Math.sin(i * 0.35 + 1.2) > -0.1;
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center gap-px">
                          <div className="w-px bg-white/15" style={{ height: `${h * 0.25}px` }} />
                          <div className="w-full max-w-[5px] rounded-[1px]" style={{ height: `${h}px`, backgroundColor: up ? 'rgba(22,185,121,0.35)' : 'rgba(232,64,64,0.25)' }} />
                          <div className="w-px bg-white/15" style={{ height: `${h * 0.2}px` }} />
                        </div>
                      );
                    })}
                  </div>
                </div>
                {/* Right panel */}
                <div className="hidden sm:flex flex-col border border-white/[0.03] rounded-lg bg-[#08090d] p-3 space-y-2.5">
                  <div className="h-1.5 w-10 bg-white/10 rounded-full" />
                  <div className="grid grid-cols-2 gap-1.5">
                    {['3.27K', '0.81', 'BUY', '+0.34'].map((v, i) => (
                      <div key={i} className="h-8 bg-white/[0.02] rounded-md border border-white/[0.03] flex items-center justify-center">
                        <span className="text-[8px] font-mono text-[#8a8578]/70">{v}</span>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-1.5 mt-1.5">
                    {[0.58, 0.42, 0.28].map((w, i) => (
                      <div key={i} className="h-1.5 bg-white/[0.03] rounded-full overflow-hidden">
                        <div className="h-full bg-[#d4af37]/20 rounded-full transition-all" style={{ width: `${w * 100}%` }} />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
