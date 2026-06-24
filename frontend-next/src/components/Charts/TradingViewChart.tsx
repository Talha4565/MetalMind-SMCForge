'use client';

import { AssetType } from '@/lib/api-types';
import { useEffect, useRef, useState } from 'react';

const symbolMap: Record<AssetType, { tv: string; label: string; desc: string }> = {
  gold:   { tv: 'OANDA:XAUUSD', label: 'XAU/USD', desc: 'Gold Spot · USD' },
  silver: { tv: 'OANDA:XAGUSD', label: 'XAG/USD', desc: 'Silver Spot · USD' },
};

const intervals = ['1', '5', '15', '30', '60', '240', 'D'] as const;
const intervalLabels: Record<string, string> = {
  '1': '1m', '5': '5m', '15': '15m', '30': '30m',
  '60': '1h', '240': '4h', 'D': '1D',
};

interface TradingViewChartProps {
  asset: AssetType;
}

export default function TradingViewChart({ asset }: TradingViewChartProps) {
  const [mounted, setMounted]       = useState(false);
  const [interval, setInterval]     = useState<string>('60');
  const containerRef                = useRef<HTMLDivElement>(null);

  useEffect(() => { setMounted(true); }, []);

  const sym = symbolMap[asset];

  const src = `https://www.tradingview.com/widgetembed/?symbol=${encodeURIComponent(sym.tv)}&interval=${interval}&hidesidetoolbar=0&symboledit=0&saveimage=0&toolbarbg=0a0b0d&studies=[]&theme=dark&style=1&timezone=exchange&locale=en&hide_top_toolbar=0&allow_symbol_change=0&details=0&hotlist=0&calendar=0`;

  return (
    <div ref={containerRef} className="flex flex-col h-full bg-background">
      {/* ── Terminal chart toolbar ── */}
      <div className="flex items-center justify-between px-3 py-1 border-b border-terminal-rule bg-terminal-panel shrink-0">
        <div className="flex items-center gap-3">
          {/* Symbol */}
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-terminal-buy animate-pulse" />
            <span className="text-[9px] font-mono font-black text-terminal-value tracking-widest">
              {sym.label}
            </span>
            <span className="text-[8px] font-mono text-terminal-label">{sym.desc}</span>
          </div>

          {/* Divider */}
          <span className="w-px h-3 bg-terminal-rule" />

          {/* Interval switcher */}
          <div className="flex items-center gap-0">
            {intervals.map((iv) => (
              <button
                key={iv}
                onClick={() => setInterval(iv)}
                className={`px-2 py-0.5 text-[8px] font-mono font-bold tracking-widest transition-colors ${
                  interval === iv
                    ? 'text-terminal-hold bg-terminal-hold/10'
                    : 'text-terminal-label hover:text-terminal-value'
                }`}
              >
                {intervalLabels[iv]}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-[8px] font-mono text-terminal-label tracking-widest">
            TRADINGVIEW · OANDA · LIVE
          </span>
        </div>
      </div>

      {/* ── Iframe ── */}
      <div className="flex-1 min-h-0 relative">
        {mounted ? (
          <iframe
            key={`${asset}-${interval}`}
            src={src}
            className="w-full h-full border-0"
            scrolling="no"
            allowFullScreen
            title={`${sym.label} Chart`}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-terminal-panel">
            <p className="text-[10px] font-mono text-terminal-label tracking-widest animate-pulse">
              LOADING CHART...
            </p>
          </div>
        )}
      </div>

      {/* ── Footer strip ── */}
      <div className="flex items-center gap-4 px-3 py-1 border-t border-terminal-rule bg-terminal-panel shrink-0">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-terminal-buy animate-pulse" />
          <span className="text-[8px] font-mono text-terminal-buy tracking-widest">LIVE DATA</span>
        </div>
        <span className="text-[8px] font-mono text-terminal-label">SOURCE: TRADINGVIEW · OANDA</span>
        <span className="text-[8px] font-mono text-terminal-label ml-auto">
          DELAYED 15MIN · NOT FINANCIAL ADVICE
        </span>
      </div>
    </div>
  );
}
