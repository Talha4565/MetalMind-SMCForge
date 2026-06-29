'use client';

import dynamic from 'next/dynamic';
import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { usePredictions } from '@/lib/hooks/usePredictions';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TradingViewChart from '@/components/Charts/TradingViewChart';
import PipelineSummary from '@/components/Dashboard/PipelineSummary';
import TerminalSignalPanel from '@/components/Dashboard/TerminalSignalPanel';
import TerminalStatsBar from '@/components/Dashboard/TerminalStatsBar';
import { AssetType } from '@/lib/api-types';
import { apiClient } from '@/lib/api-client';
import { RefreshCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

const SHAPExplainer = dynamic(() => import('@/components/Dashboard/SHAPExplainer'), {
  ssr: false,
  loading: () => (
    <div className="h-40 w-full bg-terminal-panel border border-terminal-rule flex items-center justify-center">
      <p className="text-terminal-label font-mono text-[10px] tracking-widest">LOADING SHAP...</p>
    </div>
  ),
});

// Static mock used when backend is offline (preview / no API)
const MOCK_PREDICTIONS: Record<AssetType, import('@/lib/api-types').PredictionItem> = {
  gold: {
    asset: 'gold',
    signal: 'BUY',
    confidence: 0.813,
    probability: 0.813,
    price: 3268.45,
    timestamp: new Date().toISOString(),
    shap_values: [
      { feature: 'premium_discount_position', contribution:  0.412 },
      { feature: 'CVD_16',                    contribution:  0.331 },
      { feature: 'htf_1h_momentum',           contribution:  0.287 },
      { feature: 'VWAPd_96',                  contribution:  0.215 },
      { feature: 'session_london',            contribution:  0.198 },
      { feature: 'htf_1h_atr',               contribution: -0.174 },
      { feature: 'distance_from_equilibrium', contribution: -0.143 },
      { feature: 'Imbal_16',                  contribution: -0.097 },
    ],
  },
  silver: {
    asset: 'silver',
    signal: 'HOLD',
    confidence: 0.621,
    probability: 0.621,
    price: 32.71,
    timestamp: new Date().toISOString(),
    shap_values: [
      { feature: 'htf_1h_momentum',           contribution:  0.189 },
      { feature: 'CVD_4',                     contribution:  0.143 },
      { feature: 'premium_discount_position', contribution: -0.201 },
      { feature: 'VWAPd_16',                  contribution: -0.162 },
      { feature: 'session_ny',                contribution:  0.111 },
      { feature: 'Ret_4',                     contribution: -0.088 },
    ],
  },
};

export default function DashboardPage() {
  const [activeAsset, setActiveAsset] = useState<AssetType>('gold');
  const { data: rawPrediction, isLoading, isError, refetch, isRefetching } = usePredictions(activeAsset);
  // Fall back to static mock when API is unreachable (offline / preview mode)
  const apiPrediction = rawPrediction?.predictions?.slice(-1)[0];
  const prediction = apiPrediction ?? ((!isLoading || isError) ? MOCK_PREDICTIONS[activeAsset] : undefined);
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

  const signalText =
    prediction?.signal === 1 || prediction?.signal === 'BUY' ? 'BUY' :
    prediction?.signal === -1 || prediction?.signal === 'SELL' ? 'SELL' : 'HOLD';

  const confidence = prediction?.confidence != null
    ? (prediction.confidence * 100).toFixed(1)
    : null;

  const signalColor =
    signalText === 'BUY' ? 'text-terminal-buy' :
    signalText === 'SELL' ? 'text-terminal-sell' : 'text-terminal-hold';

  return (
    <DashboardLayout fullHeight>
      {/* ── Zone 1: Ticker/status bar ── */}
      <div className="flex items-center justify-between border-b border-terminal-rule bg-terminal-panel px-4 py-2 mb-0">
        {/* Asset selector */}
        <div className="flex items-center gap-0">
          {(['gold', 'silver'] as AssetType[]).map((asset) => (
            <button
              key={asset}
              onClick={() => setActiveAsset(asset)}
              aria-label={`Switch to ${asset === 'gold' ? 'Gold XAU/USD' : 'Silver XAG/USD'}`}
              aria-pressed={activeAsset === asset}
              className={cn(
                'px-3 py-1 text-[10px] font-mono font-bold tracking-[0.2em] uppercase transition-all border-b-2',
                activeAsset === asset
                  ? 'text-terminal-hold border-terminal-hold'
                  : 'text-terminal-label border-transparent hover:text-terminal-value'
              )}
            >
              {asset === 'gold' ? 'XAU/USD' : 'XAG/USD'}
            </button>
          ))}
        </div>

        {/* Live price strip */}
        <div className="flex items-center gap-6">
          {livePrice !== null && (
            <div className="flex items-center gap-2">
              <span className="text-[9px] font-mono text-terminal-label tracking-widest">
                {activeAsset === 'gold' ? 'XAU/USD' : 'XAG/USD'}
              </span>
              <span className="text-[15px] font-mono font-black text-terminal-value tabular-nums">
                ${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
          )}

          <div role="status" aria-live="polite" aria-label={`Current signal: ${signalText}`} className={cn('px-2 py-0.5 border font-mono font-black text-[11px] tracking-widest', {
            'border-terminal-buy/40 text-terminal-buy bg-terminal-buy/5': signalText === 'BUY',
            'border-terminal-sell/40 text-terminal-sell bg-terminal-sell/5': signalText === 'SELL',
            'border-terminal-hold/40 text-terminal-hold bg-terminal-hold/5': signalText === 'HOLD',
          })}>
            {isLoading ? '...' : signalText}
          </div>

          {confidence && (
            <div className="flex items-center gap-1.5">
              <span className="text-[9px] font-mono text-terminal-label tracking-widest">CONF</span>
              <span className={cn('text-[11px] font-mono font-bold tabular-nums', signalColor)}>
                {confidence}%
              </span>
            </div>
          )}

          <button
            onClick={() => refetch()}
            aria-label="Refresh trading signals"
            className={cn(
              'p-1 text-terminal-label hover:text-terminal-hold transition-all',
              isRefetching && 'animate-spin text-terminal-hold'
            )}
            title="Refresh signals"
          >
            <RefreshCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {status === 'unauthenticated' && (
        <div className="flex items-center gap-2 border-b border-terminal-rule px-4 py-1.5 bg-terminal-hold/5">
          <span className="w-1.5 h-1.5 bg-terminal-hold rounded-full" />
          <p className="text-[9px] font-mono text-terminal-hold tracking-widest">
            PREVIEW MODE — SIGN IN TO ACCESS WATCHLIST AND SAVED PREFERENCES
          </p>
        </div>
      )}

      {/* ── Zone 2: Pipeline status bar ── */}
      <PipelineSummary />

      {/* ── Zone 3: Main 3-column terminal grid ── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-[300px_1fr_260px] min-h-0 overflow-hidden border-t border-terminal-rule">

        {/* ── Left panel: Signal + SHAP ── */}
        <div className="border-r border-terminal-rule flex flex-col overflow-y-auto min-h-0">
          <TerminalPanelHeader label="SIGNAL ANALYSIS" code="SIG" />
          <div className="flex-1 p-3 space-y-3">
            <TerminalSignalPanel
              prediction={prediction ?? MOCK_PREDICTIONS[activeAsset]}
              isLoading={isLoading && !isError && !prediction}
              livePrice={livePrice}
            />

            {prediction && prediction.shap_values && prediction.shap_values.length > 0 && (
              <>
                <div className="border-t border-terminal-rule pt-3">
                  <p className="text-[9px] font-mono font-bold text-terminal-label tracking-widest mb-2">
                    INSIGHT
                  </p>
                  <p className="text-[11px] font-mono text-terminal-label leading-relaxed">
                    {(() => {
                      const top = [...prediction.shap_values]
                        .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
                        .slice(0, 3);
                      const bullish = top.filter(f => f.contribution > 0);
                      const bearish = top.filter(f => f.contribution < 0);
                      const parts: string[] = [];
                      if (bullish.length > 0) parts.push(`Bullish: ${bullish.map(f => f.feature.replace(/_/g, ' ')).join(', ')}`);
                      if (bearish.length > 0) parts.push(`Bearish: ${bearish.map(f => f.feature.replace(/_/g, ' ')).join(', ')}`);
                      return parts.join(' · ') || 'Analyzing market conditions...';
                    })()}
                  </p>
                </div>

                <SHAPExplainer prediction={prediction} />
              </>
            )}
          </div>
        </div>

        {/* ── Center panel: Chart ── */}
        <div className="flex flex-col min-h-0 border-r border-terminal-rule overflow-hidden">
          <TerminalPanelHeader
            label={activeAsset === 'gold' ? 'XAU/USD — GOLD FUTURES' : 'XAG/USD — SILVER FUTURES'}
            code="CHT"
            right={
              <span className="text-[9px] font-mono text-terminal-data tracking-widest">
                TRADINGVIEW · SMC
              </span>
            }
          />
          <div className="flex-1 min-h-0 h-full" style={{ minHeight: '480px' }}>
            <TradingViewChart asset={activeAsset} />
          </div>
        </div>

        {/* ── Right panel: Stats & model info ── */}
        <div className="flex flex-col min-h-0 overflow-y-auto">
          <TerminalPanelHeader label="MARKET STATS" code="MKT" />
          <div className="flex-1 p-3">
            <TerminalStatsBar
              activeAsset={activeAsset}
              livePrice={livePrice}
              prediction={prediction}
              signalText={signalText}
              confidence={confidence}
            />
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

/* ── Shared panel header ── */
function TerminalPanelHeader({
  label,
  code,
  right,
}: {
  label: string;
  code: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between px-3 py-1.5 border-b border-terminal-rule bg-terminal-panel shrink-0">
      <div className="flex items-center gap-2">
        <span className="text-[8px] font-mono font-black text-terminal-hold bg-terminal-hold/10 px-1.5 py-0.5 tracking-widest">
          {code}
        </span>
        <span className="text-[9px] font-mono font-bold text-terminal-label tracking-widest">{label}</span>
      </div>
      {right && <div>{right}</div>}
    </div>
  );
}
