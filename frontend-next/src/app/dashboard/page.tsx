'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { usePredictions } from '@/lib/hooks/usePredictions';
import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { PredictionItem } from '@/lib/api-types';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TradingViewChart from '@/components/Charts/TradingViewChart';
import PipelineSummary from '@/components/Dashboard/PipelineSummary';
import TerminalSignalPanel from '@/components/Dashboard/TerminalSignalPanel';
import TerminalStatsBar from '@/components/Dashboard/TerminalStatsBar';
import { AssetType } from '@/lib/api-types';
import { apiClient } from '@/lib/api-client';
import { RefreshCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

// Static mock used when backend is offline (preview / no API)
const MOCK_PREDICTIONS: Record<AssetType, import('@/lib/api-types').PredictionItem> = {
  gold: {
    asset: 'gold',
    signal: 'HOLD',
    confidence: 0.509,
    probability: 0.509,
    price: 4025.00,
    tp_price: 4043.11,
    sl_price: 4018.96,
    timestamp: new Date().toISOString(),
    shap_values: [
      { feature: 'htf_1h_dist_high',          contribution:  0.565 },
      { feature: 'htf_30m_dist_low',          contribution: -0.272 },
      { feature: 'htf_1h_dist_low',           contribution: -0.180 },
      { feature: 'trend_adx',                 contribution: -0.174 },
      { feature: 'htf_30m_dist_high',         contribution:  0.154 },
    ],
  },
  silver: {
    asset: 'silver',
    signal: 'HOLD',
    confidence: 0.509,
    probability: 0.509,
    price: 58.00,
    tp_price: 58.17,
    sl_price: 57.91,
    timestamp: new Date().toISOString(),
    shap_values: [
      { feature: 'htf_1h_dist_high',          contribution:  0.450 },
      { feature: 'htf_30m_dist_low',          contribution: -0.220 },
      { feature: 'VWAPd_96',                  contribution:  0.180 },
      { feature: 'trend_adx',                 contribution: -0.150 },
      { feature: 'htf_1h_dist_low',           contribution: -0.120 },
    ],
  },
};

export default function DashboardPage() {
  const [activeAsset, setActiveAsset] = useState<AssetType>('gold');
  const { data: rawPrediction, isLoading, isError, refetch, isRefetching } = usePredictions(activeAsset);
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const { status } = useSession();

  // WebSocket as primary data source (real-time updates)
  const { data: wsData, isConnected, emit } = useWebSocket<PredictionItem>('predictions');

  // Use WebSocket data if available, otherwise use REST API, otherwise mock
  const apiPrediction = rawPrediction?.predictions?.slice(-1)[0];
  const wsPrediction = wsData?.asset === activeAsset ? wsData : null;
  const prediction = wsPrediction ?? apiPrediction ?? ((!isLoading || isError) ? MOCK_PREDICTIONS[activeAsset] : undefined);
  const isUsingMock = !wsPrediction && !apiPrediction && prediction !== undefined;

  useEffect(() => {
    if (isConnected) emit('subscribe_predictions', { asset: activeAsset });
  }, [isConnected, activeAsset]);

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
        <div className="flex items-center gap-0" role="tablist" aria-label="Asset selector">
          {(['gold', 'silver'] as AssetType[]).map((asset) => (
            <button
              key={asset}
              onClick={() => setActiveAsset(asset)}
              role="tab"
              aria-selected={activeAsset === asset}
              aria-label={`Switch to ${asset === 'gold' ? 'Gold XAU/USD' : 'Silver XAG/USD'}`}
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

      {(status === 'unauthenticated' || isUsingMock) && (
        <div className="flex items-center gap-2 border-b border-terminal-rule px-4 py-1.5 bg-terminal-hold/5">
          <span className="w-1.5 h-1.5 bg-terminal-hold rounded-full" />
          <p className="text-[9px] font-mono text-terminal-hold tracking-widest">
            {status === 'unauthenticated'
              ? 'PREVIEW MODE — SIGN IN TO ACCESS WATCHLIST AND SAVED PREFERENCES'
              : 'API OFFLINE — SHOWING DEMO DATA'}
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
