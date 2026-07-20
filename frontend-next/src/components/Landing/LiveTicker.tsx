'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';

interface PriceData {
  price: number;
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
    <div className="flex items-center gap-5 px-5 py-2.5 rounded-full border border-[#d4af37]/20 bg-[#0a0b0f] text-[11px] font-mono tracking-wider">
      {/* Live indicator */}
      <div className="flex items-center gap-1.5">
        <span className={`w-1.5 h-1.5 rounded-full ${connected ? 'bg-[#d4af37] animate-pulse' : 'bg-[#8a8578]/40'}`} />
        <span className={connected ? 'text-[#d4af37]' : 'text-[#8a8578]/50'}>LIVE</span>
      </div>

      <span className="w-px h-3 bg-[#d4af37]/15" />

      {/* Gold */}
      <div className="flex items-center gap-2">
        <span className="text-[#8a8578]">XAU/USD</span>
        <span className="text-[#e8e4dc] font-bold tabular-nums">
          {prices.gold ? `$${fmt(prices.gold.price)}` : '—'}
        </span>
      </div>

      <span className="w-px h-3 bg-[#d4af37]/15" />

      {/* Silver */}
      <div className="flex items-center gap-2">
        <span className="text-[#8a8578]">XAG/USD</span>
        <span className="text-[#e8e4dc] font-bold tabular-nums">
          {prices.silver ? `$${fmt(prices.silver.price)}` : '—'}
        </span>
      </div>
    </div>
  );
}
