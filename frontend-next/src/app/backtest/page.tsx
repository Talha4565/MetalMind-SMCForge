'use client';

import { useState, useEffect, useCallback } from 'react';
import React from 'react';
import { useRunBacktest, useBacktestHistory } from '@/lib/hooks/useBacktest';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalButton } from '@/components/Common/TerminalCard';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '@/components/ui/table';
import { Play, History, Download, Trash2, Loader2, CheckCircle2 } from 'lucide-react';
import { AssetType, BacktestResponse } from '@/lib/api-types';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

const PROGRESS_STEPS = [
  { at: 10, label: 'Initializing...' },
  { at: 30, label: 'Loading data...' },
  { at: 50, label: 'Running simulation...' },
  { at: 70, label: 'Computing metrics...' },
  { at: 80, label: 'Generating results...' },
  { at: 100, label: 'Complete!' },
];

export default function BacktestPage() {
  const [asset, setAsset] = useState<AssetType>('gold');
  const [startDate, setStartDate] = useState('2026-01-01');
  const [endDate, setEndDate] = useState('2026-05-01');
  const [capital, setCapital] = useState(10000);
  const [progress, setProgress] = useState(0);
  const [progressLabel, setProgressLabel] = useState('');
  const [backtestError, setBacktestError] = useState<string | null>(null);
  const [backtestDone, setBacktestDone] = useState(false);
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [localHistory, setLocalHistory] = useState<BacktestResponse[] | null>(null);

  const runBacktest = useRunBacktest();
  const { data: history, isLoading: historyLoading } = useBacktestHistory();

  useEffect(() => {
    if (history) setLocalHistory(history);
  }, [history]);

  const pollStatus = useCallback(async () => {
    try {
      const status = await apiClient.getBacktestStatus();
      setProgress(status.progress);
      setBacktestError(status.error);

      const step = [...PROGRESS_STEPS].reverse().find(s => status.progress >= s.at);
      setProgressLabel(step?.label || '');

      if (!status.running && status.progress === 100) {
        setBacktestDone(true);
        setProgressLabel('Complete!');
        return false;
      }
      if (!status.running && status.error) {
        setProgressLabel('Failed');
        return false;
      }
      return true;
    } catch {
      return false;
    }
  }, []);

  useEffect(() => {
    if (!runBacktest.isPending) return;
    const interval = setInterval(async () => {
      const shouldContinue = await pollStatus();
      if (!shouldContinue) clearInterval(interval);
    }, 1500);
    return () => clearInterval(interval);
  }, [runBacktest.isPending, pollStatus]);

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setBacktestError(null);
    setBacktestDone(false);
    setProgress(0);
    setProgressLabel('Starting...');

    if (startDate >= endDate) {
      setBacktestError('Start date must be before end date');
      return;
    }

    try {
      await runBacktest.mutateAsync({
        asset,
        start_date: startDate,
        end_date: endDate,
        strategy: 'SMC_FORGE_V1',
        initial_capital: capital,
      });
    } catch (error) {
      const msg = error instanceof Error ? error.message : (error as { error?: string })?.error || 'Backtest failed';
      setBacktestError(msg);
      setProgressLabel('Failed');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono">BACKTEST</h1>
          <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">
            Strategy simulator · walk-forward validation · SMC engine
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Configuration Panel */}
          <TerminalCard title="CONFIGURATION" code="CFG" className="lg:col-span-1 h-fit">
            <form onSubmit={handleRun} className="space-y-5">
              <div className="space-y-2">
                <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Asset Pair</Label>
                <Select
                  value={asset}
                  onValueChange={(value) => { if (value) setAsset(value as AssetType); }}
                >
                  <SelectTrigger className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none">
                    <SelectValue placeholder="Select asset" />
                  </SelectTrigger>
                  <SelectContent className="bg-terminal-panel border-terminal-rule rounded-none">
                    <SelectItem value="gold">XAUUSD (Gold)</SelectItem>
                    <SelectItem value="silver">XAGUSD (Silver)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Start Date</Label>
                  <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)}
                    className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none" />
                </div>
                <div className="space-y-2">
                  <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">End Date</Label>
                  <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)}
                    className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none" />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Capital ($)</Label>
                <Input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value) || 0)}
                  className="bg-terminal-panel border-terminal-rule text-terminal-value font-mono text-xs rounded-none" min={100} step={100} />
              </div>

              {/* Error display — always visible, outside the progress gate */}
              {backtestError && (
                <div className="space-y-1 px-3 py-2 border border-terminal-sell/30 bg-terminal-sell/5">
                  <p className="text-[10px] font-mono text-terminal-sell font-bold">{backtestError}</p>
                </div>
              )}

              {(runBacktest.isPending || progress > 0) && (
                <div className="space-y-2">
                  <div className="flex justify-between text-[9px] font-mono">
                    <span className="text-terminal-label">{progressLabel}</span>
                    <span className="text-terminal-value">{progress}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-terminal-panel border border-terminal-rule overflow-hidden" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100} aria-label={progressLabel}>
                    <div className={cn("h-full transition-all duration-500", backtestError ? "bg-terminal-sell" : backtestDone ? "bg-terminal-buy" : "bg-terminal-hold")}
                      style={{ width: `${progress}%` }} />
                  </div>
                  {backtestDone && (
                    <p className="text-[9px] font-mono text-terminal-buy mt-1 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" /> Backtest completed
                    </p>
                  )}
                </div>
              )}

              <TerminalButton
                type="submit"
                className="w-full"
                disabled={runBacktest.isPending || (progress > 0 && progress < 100)}
                isLoading={runBacktest.isPending || (progress > 0 && progress < 100)}
              >
                {runBacktest.isPending ? 'Simulating...' : backtestDone ? 'Run Again' : 'Run Simulation'}
              </TerminalButton>
            </form>
          </TerminalCard>

          {/* Results History */}
          <TerminalCard title="SIMULATION HISTORY" code="HST" className="lg:col-span-2"
            right={
              <button
                className="text-[8px] font-mono text-terminal-label hover:text-terminal-value tracking-widest"
                onClick={async () => {
                  try {
                    const blob = await apiClient.exportBacktest('csv', 'all');
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `backtest-report-${new Date().toISOString().slice(0, 10)}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch { /* export failed silently */ }
                }}
                disabled={!localHistory || localHistory.length === 0}
              >
                <Download className="w-3 h-3 inline mr-1" />EXPORT
              </button>
            }
          >
            <div className="overflow-hidden">
              <Table>
                <TableHeader className="bg-terminal-panel">
                  <TableRow className="border-terminal-rule hover:bg-transparent">
                    <TableHead className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Asset</TableHead>
                    <TableHead className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Win Rate</TableHead>
                    <TableHead className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">Profit Factor</TableHead>
                    <TableHead className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label text-right">Net Profit</TableHead>
                    <TableHead className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {historyLoading ? (
                    <TableRow><TableCell colSpan={5} className="text-center py-8 font-mono text-xs text-terminal-label">Loading history...</TableCell></TableRow>
                  ) : localHistory && Array.isArray(localHistory) && localHistory.length > 0 ? (
                    localHistory.map((result, i) => {
                      const isExpanded = expandedRow === i;
                      return (
                        <React.Fragment key={i}>
                          <TableRow className="border-terminal-rule hover:bg-terminal-hold/5 transition-colors">
                            <TableCell className="font-mono font-bold text-xs text-terminal-value">{result.asset ? result.asset.toUpperCase() : '—'}</TableCell>
                            <TableCell className="text-terminal-buy font-mono text-xs">
                              {result.win_rate != null ? `${(result.win_rate * 100).toFixed(1)}%` : '—'}
                            </TableCell>
                            <TableCell className="text-terminal-data font-mono text-xs">
                              {result.profit_factor != null ? result.profit_factor.toFixed(2) : '—'}
                            </TableCell>
                            <TableCell className="text-right text-terminal-value font-mono font-bold text-xs">
                              {result.net_profit != null ? `$${result.net_profit.toLocaleString()}` : '—'}
                            </TableCell>
                            <TableCell className="text-right">
                              <div className="flex justify-end gap-1">
                                <button onClick={() => setExpandedRow(isExpanded ? null : i)}
                                  className="p-1.5 text-terminal-label hover:text-terminal-value transition-colors" title="View details">
                                  <History className="w-3.5 h-3.5" />
                                </button>
                                <button
                                  className="p-1.5 text-terminal-label hover:text-terminal-sell transition-colors"
                                  onClick={() => {
                                    if (window.confirm('Delete this backtest result?')) {
                                      setLocalHistory(prev => prev ? prev.filter((_, idx) => idx !== i) : null);
                                      setExpandedRow(null);
                                    }
                                  }}
                                  title="Delete result">
                                  <Trash2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </TableCell>
                          </TableRow>
                          {isExpanded && (
                            <TableRow key={`${i}-detail`} className="bg-terminal-panel">
                              <TableCell colSpan={5} className="p-4">
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                                  <div>
                                    <p className="text-terminal-label tracking-widest mb-1 text-[9px]">SHARPE</p>
                                    <p className="text-terminal-value font-bold">{result.sharpe_ratio?.toFixed(2) || '—'}</p>
                                  </div>
                                  <div>
                                    <p className="text-terminal-label tracking-widest mb-1 text-[9px]">SORTINO</p>
                                    <p className="text-terminal-value font-bold">{result.sortino_ratio?.toFixed(2) || '—'}</p>
                                  </div>
                                  <div>
                                    <p className="text-terminal-label tracking-widest mb-1 text-[9px]">MAX DD</p>
                                    <p className="text-terminal-sell font-bold">{result.max_drawdown != null ? `${result.max_drawdown.toFixed(2)}%` : '—'}</p>
                                  </div>
                                  <div>
                                    <p className="text-terminal-label tracking-widest mb-1 text-[9px]">TRADES</p>
                                    <p className="text-terminal-value font-bold">{result.total_trades || '—'}</p>
                                  </div>
                                </div>
                              </TableCell>
                            </TableRow>
                          )}
                        </React.Fragment>
                      );
                    })
                  ) : (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-12 font-mono text-xs text-terminal-label">
                        No simulation history found. Run your first backtest!
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          </TerminalCard>
        </div>
      </div>
    </DashboardLayout>
  );
}
