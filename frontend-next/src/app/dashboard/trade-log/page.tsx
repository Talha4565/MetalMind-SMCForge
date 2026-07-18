'use client';

import { useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalButton } from '@/components/Common/TerminalCard';
import { usePredictionHistory } from '@/lib/hooks/usePredictionHistory';
import { PredictionLogItem } from '@/lib/api-types';
import { TrendingUp, TrendingDown, Minus, Clock, RefreshCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

const DAYS_OPTIONS = [7, 14, 30];
const ASSET_OPTIONS = [
  { value: '', label: 'ALL' },
  { value: 'gold', label: 'GOLD' },
  { value: 'silver', label: 'SILVER' },
];

function outcomeBadge(outcome: string | null) {
  if (!outcome) return <span className="text-[9px] font-mono px-2 py-0.5 border border-terminal-rule text-terminal-label">PENDING</span>;
  if (outcome.includes('WIN')) return <span className="text-[9px] font-mono px-2 py-0.5 border border-terminal-buy/20 bg-terminal-buy/5 text-terminal-buy">{outcome}</span>;
  return <span className="text-[9px] font-mono px-2 py-0.5 border border-terminal-sell/20 bg-terminal-sell/5 text-terminal-sell">{outcome}</span>;
}

function signalIcon(signal: number) {
  if (signal === 1) return <TrendingUp className="w-3.5 h-3.5 text-terminal-buy" />;
  if (signal === -1) return <TrendingDown className="w-3.5 h-3.5 text-terminal-sell" />;
  return <Minus className="w-3.5 h-3.5 text-terminal-label" />;
}

function signalColor(signal: number) {
  if (signal === 1) return 'text-terminal-buy';
  if (signal === -1) return 'text-terminal-sell';
  return 'text-terminal-label';
}

export default function TradeLogPage() {
  const [days, setDays] = useState(7);
  const [asset, setAsset] = useState('');
  const { data, isLoading, refetch, isRefetching } = usePredictionHistory(days, asset || undefined);

  const predictions = data?.predictions ?? [];
  const summary = data?.summary;

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono">TRADE LOG</h1>
            <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">
              Historical signals · outcome tracking · PnL audit
            </p>
          </div>
          <TerminalButton variant="secondary" size="sm" onClick={() => refetch()} disabled={isRefetching} isLoading={isRefetching}>
            <RefreshCcw className="w-3 h-3" /> REFRESH
          </TerminalButton>
        </div>

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
            {[
              { label: 'TOTAL', value: summary.total_predictions, cls: 'text-terminal-value' },
              { label: 'BUY', value: summary.buy_signals, cls: 'text-terminal-buy' },
              { label: 'SELL', value: summary.sell_signals, cls: 'text-terminal-sell' },
              { label: 'WINS', value: summary.wins, cls: 'text-terminal-buy' },
              { label: 'LOSSES', value: summary.losses, cls: 'text-terminal-sell' },
              { label: 'AVG CONF', value: summary.avg_confidence > 0 ? `${(summary.avg_confidence * 100).toFixed(1)}%` : '—', cls: 'text-terminal-data' },
            ].map(s => (
              <div key={s.label} className="border border-terminal-rule bg-terminal-panel p-3">
                <p className="text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">{s.label}</p>
                <p className={cn('text-xl font-black font-mono mt-1 tabular-nums', s.cls)}>{s.value}</p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex border border-terminal-rule">
            {DAYS_OPTIONS.map((d) => (
              <button key={d} onClick={() => setDays(d)}
                className={cn('px-4 py-1.5 text-[9px] font-mono font-bold uppercase tracking-widest transition-all border-r border-terminal-rule last:border-0',
                  days === d ? 'bg-terminal-hold text-black' : 'text-terminal-label hover:text-terminal-value')}>
                {d}D
              </button>
            ))}
          </div>
          <div className="flex border border-terminal-rule">
            {ASSET_OPTIONS.map((a) => (
              <button key={a.value} onClick={() => setAsset(a.value)}
                className={cn('px-4 py-1.5 text-[9px] font-mono font-bold uppercase tracking-widest transition-all border-r border-terminal-rule last:border-0',
                  asset === a.value ? 'bg-terminal-hold text-black' : 'text-terminal-label hover:text-terminal-value')}>
                {a.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <TerminalCard title="SIGNAL HISTORY" code="LOG" noPadding>
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-terminal-rule">
                  {['TIME', 'ASSET', 'SIGNAL', 'CONF', 'ENTRY', 'TP', 'SL', 'OUTCOME', 'PNL'].map(h => (
                    <th key={h} className="px-4 py-2.5 text-left text-[8px] font-mono font-bold uppercase tracking-widest text-terminal-label">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={9} className="px-4 py-12 text-center font-mono text-xs text-terminal-label">
                    <RefreshCcw className="w-4 h-4 animate-spin mx-auto mb-2" />Loading...
                  </td></tr>
                ) : predictions.length === 0 ? (
                  <tr><td colSpan={9} className="px-4 py-12 text-center font-mono text-xs text-terminal-label">
                    No trades yet. {summary?.hold_signals ?? 0} HOLD predictions logged — awaiting signals above threshold.
                  </td></tr>
                ) : (
                  predictions.map((p: PredictionLogItem, i: number) => (
                    <tr key={i} className="border-b border-terminal-rule hover:bg-terminal-hold/5 transition-colors">
                      <td className="px-4 py-2.5 font-mono text-[10px] text-terminal-value tabular-nums whitespace-nowrap">
                        {new Date(p.timestamp).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false })}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={cn('text-[10px] font-mono font-bold uppercase tracking-wider', p.asset === 'gold' ? 'text-terminal-hold' : 'text-terminal-label')}>{p.asset}</span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">{signalIcon(p.signal)}<span className={cn('text-[10px] font-mono font-bold', signalColor(p.signal))}>{p.signal_text}</span></div>
                      </td>
                      <td className="px-4 py-2.5 font-mono text-[10px] tabular-nums text-terminal-value">{(p.confidence * 100).toFixed(1)}%</td>
                      <td className="px-4 py-2.5 font-mono text-[10px] tabular-nums text-terminal-value">${p.price != null ? p.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-[10px] tabular-nums text-terminal-buy">{p.tp_price ? `$${p.tp_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}</td>
                      <td className="px-4 py-2.5 font-mono text-[10px] tabular-nums text-terminal-sell">{p.sl_price ? `$${p.sl_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}</td>
                      <td className="px-4 py-2.5">{outcomeBadge(p.actual_outcome)}</td>
                      <td className="px-4 py-2.5 font-mono text-[10px] tabular-nums">
                        {p.actual_pnl != null ? (
                          <span className={p.actual_pnl >= 0 ? 'text-terminal-buy' : 'text-terminal-sell'}>
                            {p.actual_pnl >= 0 ? '+' : ''}{p.actual_pnl.toFixed(2)}%
                          </span>
                        ) : <span className="text-terminal-label">—</span>}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </TerminalCard>
      </div>
    </DashboardLayout>
  );
}
