'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { usePredictions } from '@/lib/hooks/usePredictions';
import DashboardLayout from '@/components/Common/DashboardLayout';
import SignalCard from '@/components/Dashboard/SignalCard';
import TradingViewChart from '@/components/Charts/TradingViewChart';
import { AssetType } from '@/lib/api-types';
import { apiClient } from '@/lib/api-client';
import { 
  RefreshCcw
} from 'lucide-react';
import { cn } from '@/lib/utils';

// Expert Pattern: Lazy load SHAP explainer for better performance
const SHAPExplainer = dynamic(() => import('@/components/Dashboard/SHAPExplainer'), {
  ssr: false,
  loading: () => (
    <div className="h-[300px] w-full rounded-2xl bg-slate-900 border border-slate-800 animate-pulse flex items-center justify-center">
      <p className="text-slate-500 text-sm">Loading Feature Analysis...</p>
    </div>
  ),
});

export default function DashboardPage() {
  const [activeAsset, setActiveAsset] = useState<AssetType>('gold');
  const { data: rawPrediction, isLoading, refetch, isRefetching } = usePredictions(activeAsset);
  const prediction = rawPrediction?.predictions?.[0];
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

  return (
    <DashboardLayout>
      <div className="space-y-8">
        {status === 'unauthenticated' && (
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 p-4 text-sm text-amber-200">
            Preview mode. Sign in to access your watchlist and saved preferences.
          </div>
        )}

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-slate-500 mb-1">
              {activeAsset === 'gold' ? 'XAU / USD' : 'XAG / USD'}
            </p>
            {livePrice !== null && (
              <h1 className="text-4xl md:text-5xl font-black font-mono text-slate-100 tracking-tight">
                ${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h1>
            )}
            <p className="text-sm text-slate-500 mt-1">
              Real-time Smart Money Concept signals
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => refetch()}
              className={cn(
                "p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-all",
                isRefetching && "animate-spin text-emerald-400"
              )}
            >
              <RefreshCcw className="w-4 h-4" />
            </button>
            <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800">
              {(['gold', 'silver'] as AssetType[]).map((asset) => (
                <button
                  key={asset}
                  onClick={() => setActiveAsset(asset)}
                  className={cn(
                    "px-5 py-2 rounded-md text-xs font-bold uppercase tracking-widest transition-all",
                    activeAsset === asset
                      ? "bg-slate-800 text-white shadow-sm"
                      : "text-slate-500 hover:text-slate-300"
                  )}
                >
                  {asset}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Stats Grid — each card has a distinct visual weight */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Signal"
            value={prediction?.signal === 1 || prediction?.signal === 'BUY' ? 'BUY' : prediction?.signal === -1 || prediction?.signal === 'SELL' ? 'SELL' : 'HOLD'}
            accent={prediction?.signal === 1 || prediction?.signal === 'BUY' ? 'emerald' : prediction?.signal === -1 || prediction?.signal === 'SELL' ? 'red' : 'slate'}
          />
          <StatCard
            label="Confidence"
            value={prediction?.confidence != null ? `${(prediction.confidence * 100).toFixed(0)}%` : '—'}
            accent="blue"
          />
          <StatCard
            label="Confidence"
            value={`${((prediction?.confidence || 0) * 100).toFixed(0)}%`}
            accent="blue"
          />
          <StatCard
            label="Volatility"
            value="High"
            accent="amber"
          />
          <StatCard
            label="SMC Score"
            value="84"
            suffix="/100"
            accent="violet"
          />
        </div>

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

            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/50">
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">
                Insight
              </p>
              <p className="text-sm text-slate-400 leading-relaxed">
                Order flow suggests a liquidity grab below recent lows.
                Watch for displacement higher before committing to longs.
              </p>
            </div>
          </div>

          <div className="lg:col-span-2">
            <TradingViewChart asset={activeAsset} />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

interface StatCardProps {
  label: string;
  value: string;
  suffix?: string;
  accent: 'emerald' | 'blue' | 'amber' | 'violet' | 'slate' | 'red';
}

const accentMap = {
  emerald: 'text-emerald-400 border-emerald-500/20',
  blue: 'text-blue-400 border-blue-500/20',
  amber: 'text-amber-400 border-amber-500/20',
  violet: 'text-violet-400 border-violet-500/20',
  slate: 'text-slate-400 border-slate-700/20',
  red: 'text-red-400 border-red-500/20',
};

function StatCard({ label, value, suffix, accent }: StatCardProps) {
  return (
    <div className={cn(
      "p-4 rounded-xl bg-slate-900/60 border transition-colors",
      accentMap[accent]
    )}>
      <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-slate-500 mb-2">
        {label}
      </p>
      <p className="text-2xl font-black font-mono text-slate-100">
        {value}
        {suffix && <span className="text-sm text-slate-500 font-normal">{suffix}</span>}
      </p>
    </div>
  );
}
