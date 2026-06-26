'use client';

import { useState, useEffect, useCallback } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { apiClient } from '@/lib/api-client';
import { SignalHistoryRecord, SignalHistorySummary } from '@/lib/api-types';
import { cn } from '@/lib/utils';
import { RefreshCcw, ChevronLeft, ChevronRight, TrendingUp, TrendingDown, Minus, Target, BarChart3 } from 'lucide-react';

export default function SignalsPage() {
  const [records, setRecords] = useState<SignalHistoryRecord[]>([]);
  const [summary, setSummary] = useState<SignalHistorySummary | null>(null);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [assetFilter, setAssetFilter] = useState('all');
  const [signalFilter, setSignalFilter] = useState('all');
  const [days, setDays] = useState(7);

  const fetchHistory = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    try {
      const data = await apiClient.getSignalHistory({
        asset: assetFilter,
        signal: signalFilter,
        days,
        page,
        per_page: 50,
      });
      setRecords(data.predictions);
      setSummary(data.summary);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error('Failed to load signal history', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [assetFilter, signalFilter, days, page]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  useEffect(() => { setPage(1); }, [assetFilter, signalFilter, days]);

  const signalBadge = (signal: number, signal_text?: string) => {
    const text = signal_text || (signal === 1 ? 'BUY' : signal === -1 ? 'SELL' : 'HOLD');
    return (
      <span className={cn(
        'px-2 py-0.5 text-[10px] font-mono font-black tracking-widest border',
        text === 'BUY' && 'border-terminal-buy/40 text-terminal-buy bg-terminal-buy/5',
        text === 'SELL' && 'border-terminal-sell/40 text-terminal-sell bg-terminal-sell/5',
        text === 'HOLD' && 'border-terminal-hold/40 text-terminal-hold bg-terminal-hold/5',
      )}>
        {text}
      </span>
    );
  };

  const outcomeBadge = (outcome: string | null, pnl: number | null) => {
    if (!outcome) return <span className="text-[10px] font-mono text-terminal-label">PENDING</span>;
    const isWin = outcome.includes('WIN');
    const isTp = outcome === 'WIN_TP';
    const isSl = outcome === 'LOSS_SL';
    const label = isTp ? 'WIN TP' : isSl ? 'LOSS SL' : outcome.replace('_', ' ');
    return (
      <div className="flex items-center gap-1.5">
        <span className={cn(
          'px-1.5 py-0.5 text-[9px] font-mono font-bold tracking-wider border',
          isWin ? 'border-terminal-buy/30 text-terminal-buy bg-terminal-buy/5' : 'border-terminal-sell/30 text-terminal-sell bg-terminal-sell/5',
        )}>
          {label}
        </span>
        {pnl !== null && (
          <span className={cn('text-[10px] font-mono font-bold tabular-nums', pnl >= 0 ? 'text-terminal-buy' : 'text-terminal-sell')}>
            {pnl >= 0 ? '+' : ''}{pnl}%
          </span>
        )}
      </div>
    );
  };

  return (
    <DashboardLayout fullHeight>
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-terminal-rule bg-terminal-panel px-4 py-2">
        <div className="flex items-center gap-2">
          <span className="text-[8px] font-mono font-black text-terminal-hold bg-terminal-hold/10 px-1.5 py-0.5 tracking-widest">SIG</span>
          <span className="text-[10px] font-mono font-bold text-terminal-label tracking-widest">SIGNAL HISTORY</span>
        </div>
        <button
          onClick={() => fetchHistory(true)}
          className={cn('p-1 text-terminal-label hover:text-terminal-hold transition-all', refreshing && 'animate-spin text-terminal-hold')}
          title="Refresh"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4 px-4 py-2 border-b border-terminal-rule bg-terminal-panel/50 flex-wrap">
        <div className="flex items-center gap-1">
          <span className="text-[8px] font-mono text-terminal-label tracking-widest mr-1">ASSET</span>
          {['all', 'gold', 'silver'].map((a) => (
            <button
              key={a}
              onClick={() => setAssetFilter(a)}
              className={cn(
                'px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest transition-all border-b',
                assetFilter === a ? 'text-terminal-hold border-terminal-hold' : 'text-terminal-label border-transparent hover:text-terminal-value'
              )}
            >
              {a === 'all' ? 'ALL' : a === 'gold' ? 'XAU' : 'XAG'}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <span className="text-[8px] font-mono text-terminal-label tracking-widest mr-1">SIGNAL</span>
          {['all', 'buy', 'sell'].map((s) => (
            <button
              key={s}
              onClick={() => setSignalFilter(s)}
              className={cn(
                'px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest transition-all border-b',
                signalFilter === s ? 'text-terminal-hold border-terminal-hold' : 'text-terminal-label border-transparent hover:text-terminal-value'
              )}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1">
          <span className="text-[8px] font-mono text-terminal-label tracking-widest mr-1">DAYS</span>
          {[3, 7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={cn(
                'px-2 py-0.5 text-[9px] font-mono font-bold tracking-widest transition-all border-b',
                days === d ? 'text-terminal-hold border-terminal-hold' : 'text-terminal-label border-transparent hover:text-terminal-value'
              )}
            >
              {d}
            </button>
          ))}
        </div>

        <span className="ml-auto text-[9px] font-mono text-terminal-label tracking-widest">{total} RESULTS</span>
      </div>

      {/* Summary cards */}
      {summary && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-px border-b border-terminal-rule">
          <SummaryCard label="TOTAL" value={String(summary.total)} icon={<BarChart3 className="w-3 h-3" />} />
          <SummaryCard label="BUYS" value={String(summary.buys)} color="text-terminal-buy" icon={<TrendingUp className="w-3 h-3" />} />
          <SummaryCard label="SELLS" value={String(summary.sells)} color="text-terminal-sell" icon={<TrendingDown className="w-3 h-3" />} />
          <SummaryCard label="HOLDS" value={String(summary.holds)} color="text-terminal-hold" icon={<Minus className="w-3 h-3" />} />
          <SummaryCard label="WIN RATE" value={`${summary.win_rate}%`} color={summary.win_rate >= 50 ? 'text-terminal-buy' : 'text-terminal-sell'} icon={<Target className="w-3 h-3" />} />
          <SummaryCard label="WINS" value={String(summary.wins)} color="text-terminal-buy" />
          <SummaryCard label="AVG PNL" value={`${summary.avg_pnl >= 0 ? '+' : ''}${summary.avg_pnl}%`} color={summary.avg_pnl >= 0 ? 'text-terminal-buy' : 'text-terminal-sell'} />
        </div>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <p className="text-[10px] font-mono text-terminal-label tracking-widest animate-pulse">LOADING SIGNALS...</p>
          </div>
        ) : records.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-40 gap-2">
            <p className="text-[10px] font-mono text-terminal-label tracking-widest">NO SIGNALS FOUND</p>
            <p className="text-[9px] font-mono text-terminal-label/50">Adjust filters or check back later</p>
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-terminal-rule bg-terminal-panel sticky top-0 z-10">
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">TIME</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">ASSET</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">SIGNAL</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">CONF</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">PRICE</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">TP</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">SL</th>
                <th className="px-3 py-2 text-[8px] font-mono font-bold text-terminal-label tracking-[0.2em]">OUTCOME</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r, i) => (
                <tr key={i} className="border-b border-terminal-rule/50 hover:bg-terminal-panel/30 transition-colors">
                  <td className="px-3 py-2 text-[10px] font-mono text-terminal-value tabular-nums whitespace-nowrap">
                    {formatTime(r.timestamp)}
                  </td>
                  <td className="px-3 py-2 text-[10px] font-mono text-terminal-label">
                    {r.asset === 'gold' ? 'XAU' : 'XAG'}
                  </td>
                  <td className="px-3 py-2">{signalBadge(r.signal, r.signal_text)}</td>
                  <td className="px-3 py-2 text-[10px] font-mono font-bold tabular-nums text-terminal-value">
                    {(r.confidence * 100).toFixed(1)}%
                  </td>
                  <td className="px-3 py-2 text-[10px] font-mono text-terminal-value tabular-nums">
                    ${r.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="px-3 py-2">
                    {r.tp_level ? (
                      <div className="flex flex-col">
                        <span className="text-[10px] font-mono text-terminal-buy font-bold">
                          ${r.tp_level.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        <span className="text-[8px] font-mono text-terminal-label">
                          +{r.tp_distance}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-[10px] font-mono text-terminal-label">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {r.sl_level ? (
                      <div className="flex flex-col">
                        <span className="text-[10px] font-mono text-terminal-sell font-bold">
                          ${r.sl_level.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </span>
                        <span className="text-[8px] font-mono text-terminal-label">
                          -{r.sl_distance}%
                        </span>
                      </div>
                    ) : (
                      <span className="text-[10px] font-mono text-terminal-label">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2">{outcomeBadge(r.actual_outcome, r.actual_pnl)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-2 border-t border-terminal-rule bg-terminal-panel">
          <span className="text-[9px] font-mono text-terminal-label tracking-widest">
            PAGE {page} OF {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className={cn('p-1 transition-colors', page <= 1 ? 'text-terminal-label/30' : 'text-terminal-label hover:text-terminal-hold')}
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = Math.max(1, Math.min(page - 2, totalPages - 4)) + i;
              if (pageNum > totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  className={cn(
                    'w-6 h-6 text-[10px] font-mono font-bold transition-all',
                    pageNum === page
                      ? 'bg-terminal-hold text-black'
                      : 'text-terminal-label hover:text-terminal-value hover:bg-terminal-rule'
                  )}
                >
                  {pageNum}
                </button>
              );
            })}
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className={cn('p-1 transition-colors', page >= totalPages ? 'text-terminal-label/30' : 'text-terminal-label hover:text-terminal-hold')}
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

function SummaryCard({ label, value, color, icon }: { label: string; value: string; color?: string; icon?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center py-3 px-2 bg-terminal-panel hover:bg-terminal-rule/30 transition-colors">
      <div className="flex items-center gap-1 mb-1">
        {icon && <span className="text-terminal-label">{icon}</span>}
        <span className="text-[7px] font-mono font-bold text-terminal-label tracking-[0.25em]">{label}</span>
      </div>
      <span className={cn('text-[14px] font-mono font-black tabular-nums', color || 'text-terminal-value')}>{value}</span>
    </div>
  );
}

function formatTime(ts: string): string {
  try {
    const d = new Date(ts);
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    const hours = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');
    return `${month}/${day} ${hours}:${mins}`;
  } catch {
    return ts;
  }
}
