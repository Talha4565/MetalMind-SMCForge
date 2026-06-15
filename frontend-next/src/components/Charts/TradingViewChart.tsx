'use client';

import { AssetType } from '@/lib/api-types';
import { useEffect, useState } from 'react';

const TIMEFRAMES = [
  { label: '1H', interval: '60' },
  { label: '4H', interval: '240' },
  { label: '1D', interval: 'D' },
  { label: '1W', interval: 'W' },
] as const;

const symbolMap: Record<AssetType, string> = {
  gold: 'OANDA:XAUUSD',
  silver: 'OANDA:XAGUSD',
};

interface TradingViewChartProps {
  asset: AssetType;
}

export default function TradingViewChart({ asset }: TradingViewChartProps) {
  const [interval, setInterval] = useState<string>('60');
  const [mounted, setMounted] = useState(false);
  const openFullChart = () => {
    const symbol = symbolMap[asset];
    const url = `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(symbol)}&interval=${interval}`;
    window.open(url, '_blank', 'noopener');
  };

  // Ensure client-only operations run after mount
  useEffect(() => setMounted(true), []);
  const symbol = symbolMap[asset];

  return (
    <section className="rounded-3xl border border-border bg-card p-6 shadow-lg shadow-black/20">
      <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Market dashboard</p>
          <h2 className="mt-2 text-3xl font-black text-card-foreground">Live candlestick chart</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
            Real-time price data powered by TradingView. Switch timeframes and inspect price action.
          </p>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf.interval}
              type="button"
              onClick={() => setInterval(tf.interval)}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                interval === tf.interval
                  ? 'bg-slate-100 text-slate-950'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
              }`}
            >
              {tf.label}
            </button>
          ))}
          {mounted && (
            <button
              type="button"
              onClick={openFullChart}
              className="ml-2 rounded-full px-4 py-2 text-sm font-semibold bg-transparent border border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Open full chart
            </button>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-[2rem] border border-border bg-background">
        <iframe
          key={`${asset}-${interval}`}
          src={`https://www.tradingview.com/widgetembed/?symbol=${encodeURIComponent(symbol)}&interval=${interval}&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=exchange&locale=en`}
          style={{ width: '100%', height: '480px', border: 'none' }}
          scrolling="no"
          allowFullScreen
        />
      </div>

      <div className="mt-4 flex items-center gap-4 text-xs text-slate-500">
        <span className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          Live data
        </span>
        <span>Source: TradingView</span>
      </div>
    </section>
  );
}
