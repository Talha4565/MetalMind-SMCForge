'use client';

import { useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { usePredictionHistory } from '@/lib/hooks/usePredictionHistory';
import { PredictionLogItem } from '@/lib/api-types';
import { TrendingUp, TrendingDown, Minus, Clock, RefreshCcw } from 'lucide-react';
import { cn } from '@/lib/utils';

const DAYS_OPTIONS = [7, 14, 30];
const ASSET_OPTIONS = [
  { value: '', label: 'All Assets' },
  { value: 'gold', label: 'Gold' },
  { value: 'silver', label: 'Silver' },
];

function outcomeBadge(outcome: string | null) {
  if (!outcome) return <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-zinc-800 text-zinc-500">PENDING</span>;
  if (outcome.includes('WIN')) return <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/20">{outcome}</span>;
  return <span className="text-[9px] font-mono px-2 py-0.5 rounded bg-red-500/15 text-red-400 border border-red-500/20">{outcome}</span>;
}

function signalIcon(signal: number) {
  if (signal === 1) return <TrendingUp className="w-3.5 h-3.5 text-emerald-400" />;
  if (signal === -1) return <TrendingDown className="w-3.5 h-3.5 text-red-400" />;
  return <Minus className="w-3.5 h-3.5 text-zinc-500" />;
}

function signalColor(signal: number) {
  if (signal === 1) return 'text-emerald-400';
  if (signal === -1) return 'text-red-400';
  return 'text-zinc-500';
}

export default function TradeLogPage() {
  const [days, setDays] = useState(7);
  const [asset, setAsset] = useState('');
  const { data, isLoading, refetch, isRefetching } = usePredictionHistory(days, asset || undefined);

  const predictions = data?.predictions ?? [];
  const summary = data?.summary;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground">Trade Log</h1>
            <p className="text-muted-foreground mt-1">Historical prediction signals with outcome tracking.</p>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-border w-fit"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCcw className={cn('w-4 h-4 mr-2', isRefetching && 'animate-spin')} />
            Refresh
          </Button>
        </div>

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Total</p>
                <p className="text-2xl font-black font-mono text-card-foreground mt-1 tabular-nums">{summary.total_predictions}</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Buy</p>
                <p className="text-2xl font-black font-mono text-emerald-400 mt-1 tabular-nums">{summary.buy_signals}</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Sell</p>
                <p className="text-2xl font-black font-mono text-red-400 mt-1 tabular-nums">{summary.sell_signals}</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Wins</p>
                <p className="text-2xl font-black font-mono text-emerald-400 mt-1 tabular-nums">{summary.wins}</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Losses</p>
                <p className="text-2xl font-black font-mono text-red-400 mt-1 tabular-nums">{summary.losses}</p>
              </CardContent>
            </Card>
            <Card className="bg-card border-border">
              <CardContent className="p-4">
                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Avg Conf</p>
                <p className="text-2xl font-black font-mono text-card-foreground mt-1 tabular-nums">
                  {summary.avg_confidence > 0 ? `${(summary.avg_confidence * 100).toFixed(1)}%` : '—'}
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex bg-background p-1 rounded-lg border border-border">
            {DAYS_OPTIONS.map((d) => (
              <button
                key={d}
                onClick={() => setDays(d)}
                className={cn(
                  'px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-widest transition-all',
                  days === d ? 'bg-card text-card-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {d}d
              </button>
            ))}
          </div>
          <div className="flex bg-background p-1 rounded-lg border border-border">
            {ASSET_OPTIONS.map((a) => (
              <button
                key={a.value}
                onClick={() => setAsset(a.value)}
                className={cn(
                  'px-4 py-1.5 rounded-md text-xs font-bold uppercase tracking-widest transition-all',
                  asset === a.value ? 'bg-card text-card-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {a.label}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <Card className="bg-card border-border">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Time</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Asset</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Signal</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Confidence</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Entry</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">TP</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">SL</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Outcome</th>
                    <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-widest text-muted-foreground">PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {isLoading ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-12 text-center text-muted-foreground">
                        <RefreshCcw className="w-5 h-5 animate-spin mx-auto mb-2 text-muted-foreground" />
                        Loading predictions...
                      </td>
                    </tr>
                  ) : predictions.length === 0 ? (
                    <tr>
                      <td colSpan={9} className="px-4 py-12 text-center text-muted-foreground italic">
                        No actionable trades yet. The model has logged {summary?.hold_signals ?? 0} HOLD predictions — waiting for BUY/SELL signals above 65% confidence.
                      </td>
                    </tr>
                  ) : (
                    predictions.map((p: PredictionLogItem, i: number) => (
                      <tr key={i} className="border-b border-border/50 hover:bg-accent/30 transition-colors">
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5 text-card-foreground">
                            <Clock className="w-3 h-3 text-muted-foreground" />
                            <span className="font-mono text-xs tabular-nums">
                              {new Date(p.timestamp).toLocaleString('en-US', {
                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false,
                              })}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={cn(
                            'text-xs font-bold uppercase tracking-wider',
                            p.asset === 'gold' ? 'text-amber-400' : 'text-slate-300'
                          )}>
                            {p.asset}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            {signalIcon(p.signal)}
                            <span className={cn('text-xs font-bold font-mono', signalColor(p.signal))}>
                              {p.signal_text}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-3 font-mono text-xs tabular-nums text-card-foreground">
                          {(p.confidence * 100).toFixed(1)}%
                        </td>
                        <td className="px-4 py-3 font-mono text-xs tabular-nums text-card-foreground">
                          ${p.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs tabular-nums text-emerald-400">
                          {p.tp_price ? `$${p.tp_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs tabular-nums text-red-400">
                          {p.sl_price ? `$${p.sl_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                        </td>
                        <td className="px-4 py-3">
                          {outcomeBadge(p.actual_outcome)}
                        </td>
                        <td className="px-4 py-3 font-mono text-xs tabular-nums">
                          {p.actual_pnl != null ? (
                            <span className={cn(p.actual_pnl >= 0 ? 'text-emerald-400' : 'text-red-400')}>
                              {p.actual_pnl >= 0 ? '+' : ''}{p.actual_pnl.toFixed(2)}%
                            </span>
                          ) : (
                            <span className="text-zinc-600">—</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
