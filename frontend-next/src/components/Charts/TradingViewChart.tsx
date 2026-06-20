'use client';

import { AssetType } from '@/lib/api-types';
import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';

const symbolMap: Record<AssetType, string> = {
  gold: 'OANDA:XAUUSD',
  silver: 'OANDA:XAGUSD',
};

interface TradingViewChartProps {
  asset: AssetType;
}

export default function TradingViewChart({ asset }: TradingViewChartProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);
  const symbol = symbolMap[asset];

  return (
    <Card className="bg-card border-border overflow-hidden">
      <CardContent className="p-6">
        <div className="mb-4">
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Market Dashboard</p>
          <h2 className="mt-1 text-xl font-bold text-card-foreground font-sans">Live Candlestick Chart</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            Spot Reference — TradingView
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-border">
          <iframe
            key={asset}
            src={`https://www.tradingview.com/widgetembed/?symbol=${encodeURIComponent(symbol)}&interval=60&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=f1f3f6&studies=[]&theme=dark&style=1&timezone=exchange&locale=en`}
            style={{ width: '100%', height: '480px', border: 'none' }}
            scrolling="no"
            allowFullScreen
          />
        </div>

        <div className="mt-3 flex items-center gap-4 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse" />
            Live data
          </span>
          <span>Source: TradingView</span>
        </div>
      </CardContent>
    </Card>
  );
}
