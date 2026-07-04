'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface PriceData {
  price: number;
  change_pct?: number;
}

export default function LiveTicker() {
  const [prices, setPrices] = useState<Record<string, PriceData>>({});
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let mounted = true;

    const fetchPrices = async () => {
      try {
        const [gold, silver] = await Promise.all([
          apiClient.getLivePrice('gold'),
          apiClient.getLivePrice('silver'),
        ]);
        if (!mounted) return;
        setPrices({
          gold: { price: gold.price },
          silver: { price: silver.price },
        });
        setConnected(true);
      } catch {
        if (mounted) setConnected(false);
      }
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const fmt = (n: number) => n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

  return (
    <div className="flex items-center gap-5 px-5 py-2.5 rounded-full border border-white/10 bg-white/[0.03] backdrop-blur-sm text-[11px] font-mono tracking-wider">
      {/* Live indicator */}
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-zinc-600'}`} />
        <span className={connected ? 'text-emerald-400' : 'text-zinc-500'}>LIVE</span>
      </div>

      <span className="w-px h-3 bg-white/10" />

      {/* Gold */}
      <div className="flex items-center gap-2">
        <span className="text-slate-500">XAU/USD</span>
        <span className="text-slate-200 font-bold tabular-nums">
          {prices.gold ? `$${fmt(prices.gold.price)}` : '—'}
        </span>
      </div>

      <span className="w-px h-3 bg-white/10" />

      {/* Silver */}
      <div className="flex items-center gap-2">
        <span className="text-slate-500">XAG/USD</span>
        <span className="text-slate-200 font-bold tabular-nums">
          {prices.silver ? `$${fmt(prices.silver.price)}` : '—'}
        </span>
      </div>
    </div>
  );
}
