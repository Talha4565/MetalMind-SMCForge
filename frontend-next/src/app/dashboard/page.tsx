'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { usePredictions } from '@/lib/hooks/usePredictions';
import DashboardLayout from '@/components/Common/DashboardLayout';
import SignalCard from '@/components/Dashboard/SignalCard';
import TradingViewChart from '@/components/Charts/TradingViewChart';
import PipelineSummary from '@/components/Dashboard/PipelineSummary';
import { AssetType } from '@/lib/api-types';
import { apiClient } from '@/lib/api-client';
import { RefreshCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

const SHAPExplainer = dynamic(() => import('@/components/Dashboard/SHAPExplainer'), {
  ssr: false,
  loading: () => (
    <div className="h-[300px] w-full rounded-xl bg-card border border-border animate-pulse flex items-center justify-center">
      <p className="text-muted-foreground text-sm">Loading Feature Analysis...</p>
    </div>
  ),
});

export default function DashboardPage() {
  const [activeAsset, setActiveAsset] = useState<AssetType>('gold');
  const { data: rawPrediction, isLoading, refetch, isRefetching } = usePredictions(activeAsset);
  const prediction = rawPrediction?.predictions?.slice(-1)[0];
  const [livePrice, setLivePrice] = useState<number | null>(null);

  const { status } = useSession();

  useEffect(() => {
    let mounted = true;
    const fetchPrice = async () => {
      try {
        const data = await apiClient.getLivePrice(activeAsset);
        if (mounted) setLivePrice(data.price);
      } catch {
        if (mounted) setLivePrice(null);
      }
    };
    fetchPrice();
    const interval = setInterval(fetchPrice, 15000);
    return () => { mounted = false; clearInterval(interval); };
  }, [activeAsset]);

  const signalText = prediction?.signal === 1 || prediction?.signal === 'BUY'
    ? 'BUY'
    : prediction?.signal === -1 || prediction?.signal === 'SELL'
      ? 'SELL'
      : 'HOLD';

  const confidence = prediction?.confidence != null
    ? `${(prediction.confidence * 100).toFixed(1)}%`
    : '—';

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {status === 'unauthenticated' && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-200">
            Preview mode. Sign in to access your watchlist and saved preferences.
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground mb-1">
              {activeAsset === 'gold' ? 'GOLD FUTURES (Model Input)' : 'SILVER FUTURES (Model Input)'}
            </p>
            {livePrice !== null && (
              <h1 className="text-4xl md:text-5xl font-black font-mono text-card-foreground tracking-tight">
                ${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h1>
            )}
            <p className="text-xs text-muted-foreground mt-1">
              Real-time Smart Money Concept signals
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className={cn(
                "p-2.5 rounded-lg bg-card border border-border text-muted-foreground hover:text-foreground transition-all",
                isRefetching && "animate-spin text-emerald-400"
              )}
            >
              <RefreshCcw className="w-4 h-4" />
            </button>
            <div className="flex bg-card p-1 rounded-full border border-border">
              {(['gold', 'silver'] as AssetType[]).map((asset) => (
                <button
                  key={asset}
                  onClick={() => setActiveAsset(asset)}
                  className={cn(
                    "px-5 py-2 rounded-full text-[10px] font-bold uppercase tracking-widest transition-all",
                    activeAsset === asset
                      ? "bg-slate-800 text-white shadow-sm"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  {asset}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Stats Row — only Signal + Confidence (Fix 6: demoted Model/Features) */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-card border border-l-2 border-l-emerald-500/30 border-border">
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground mb-2">Signal</p>
            <p className={cn("text-2xl font-black font-mono", {
              "text-emerald-500": signalText === 'BUY',
              "text-red-500": signalText === 'SELL',
              "text-muted-foreground": signalText === 'HOLD',
            })}>
              {signalText}
            </p>
          </div>
          <div className="p-4 rounded-xl bg-card border border-l-2 border-l-blue-500/30 border-border">
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground mb-2">Confidence</p>
            <p className="text-2xl font-black font-mono text-card-foreground">{confidence}</p>
          </div>
        </div>
        <p className="text-[10px] text-muted-foreground -mt-4">
          Model: XGBoost
        </p>

        {/* Pipeline Status */}
        <PipelineSummary />

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 space-y-6">
            <SignalCard
              key={activeAsset}
              prediction={prediction || {
                asset: activeAsset,
                signal: 'HOLD',
                confidence: 0,
                probability: 0,
                price: 0,
                timestamp: new Date().toISOString(),
                shap_values: []
              }}
              isLoading={isLoading}
              livePrice={livePrice}
            />

            {prediction && (
              <SHAPExplainer prediction={prediction} />
            )}

            {prediction && prediction.shap_values && prediction.shap_values.length > 0 && (
              <div className="p-5 rounded-xl bg-card border border-l-2 border-l-emerald-500/30 border-border">
                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground mb-2">
                  Insight
                </p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {(() => {
                    const top = [...prediction.shap_values]
                      .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
                      .slice(0, 3);
                    const bullish = top.filter(f => f.contribution > 0);
                    const bearish = top.filter(f => f.contribution < 0);
                    const parts: string[] = [];
                    if (bullish.length > 0) {
                      parts.push(`Key bullish drivers: ${bullish.map(f => f.feature).join(', ')}`);
                    }
                    if (bearish.length > 0) {
                      parts.push(`Key bearish drivers: ${bearish.map(f => f.feature).join(', ')}`);
                    }
                    return parts.length > 0
                      ? parts.join('. ') + '.'
                      : 'Analyzing current market conditions...';
                  })()}
                </p>
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            <TradingViewChart asset={activeAsset} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
