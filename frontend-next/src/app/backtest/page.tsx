'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRunBacktest, useBacktestHistory } from '@/lib/hooks/useBacktest';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
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
import { Play, History, Download, Trash2, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { AssetType } from '@/lib/api-types';
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

  const runBacktest = useRunBacktest();
  const { data: history, isLoading: historyLoading } = useBacktestHistory();

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
      <div className="space-y-8">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-card-foreground flex items-center gap-3">
            Strategy Simulator
          </h1>
          <p className="text-muted-foreground mt-1">Verify performance against historical data using our SMC engine.</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Configuration Panel */}
          <Card className="lg:col-span-1 bg-card border-border h-fit">
            <CardHeader>
              <CardTitle className="text-sm font-bold uppercase tracking-widest text-slate-400">Configuration</CardTitle>
              <CardDescription>Setup your backtest parameters</CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleRun} className="space-y-6">
                <div className="space-y-2">
                  <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Asset Pair</Label>
                  <Select
                    value={asset}
                    onValueChange={(value) => {
                      if (value) setAsset(value as AssetType);
                    }}
                  >
                    <SelectTrigger className="bg-input/30 border-border">
                      <SelectValue placeholder="Select asset" />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border">
                      <SelectItem value="gold">XAUUSD (Gold)</SelectItem>
                      <SelectItem value="silver">XAGUSD (Silver)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Start Date</Label>
                    <Input
                      type="date"
                      value={startDate}
                      onChange={(e) => setStartDate(e.target.value)}
                      className="bg-input/30 border-border"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">End Date</Label>
                    <Input
                      type="date"
                      value={endDate}
                      onChange={(e) => setEndDate(e.target.value)}
                      className="bg-input/30 border-border"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Capital ($)</Label>
                  <Input
                    type="number"
                    value={capital}
                    onChange={(e) => setCapital(Number(e.target.value) || 0)}
                    className="bg-input/30 border-border"
                    min={100}
                    step={100}
                  />
                </div>

                {/* Progress Bar */}
                {(runBacktest.isPending || progress > 0) && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="text-slate-400">{progressLabel}</span>
                      <span className="text-slate-400 font-mono">{progress}%</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden"
                      role="progressbar"
                      aria-valuenow={progress}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-label={progressLabel || 'Progress'}
                    >
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          backtestError ? "bg-red-500" : backtestDone ? "bg-green-500" : "bg-blue-500"
                        )}
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    {backtestError && (
                      <p className="text-xs text-red-400 mt-1">{backtestError}</p>
                    )}
                    {backtestDone && (
                      <p className="text-xs text-green-400 mt-1 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Backtest completed successfully!
                      </p>
                    )}
                  </div>
                )}

                <Button
                  type="submit"
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-6 rounded-xl transition-all shadow-lg shadow-blue-600/20"
                  disabled={runBacktest.isPending || (progress > 0 && progress < 100)}
                >
                  {runBacktest.isPending || (progress > 0 && progress < 100) ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Simulating...
                    </>
                  ) : backtestDone ? (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      Run Again
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4 fill-current" />
                      Run Simulation
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Results History */}
          <Card className="lg:col-span-2 bg-card border-border">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-sm font-bold uppercase tracking-widest text-slate-400">Simulation History</CardTitle>
                <CardDescription>Previous backtest results</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="border-border hover:bg-accent"
                onClick={async () => {
                  try {
                    const data = await apiClient.getBacktestResults();
                    if (data.length === 0) return;
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `backtest-results-${new Date().toISOString().slice(0, 10)}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                  } catch {
                    // export failed silently
                  }
                }}
                disabled={!history || history.length === 0}
              >
                <Download className="w-4 h-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-xl border border-border overflow-hidden">
                <Table>
                  <TableHeader className="bg-slate-800/50">
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Asset</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Win Rate</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Profit Factor</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground text-right">Net Profit</TableHead>
                      <TableHead className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {historyLoading ? (
                      <TableRow><TableCell colSpan={5} className="text-center py-8">Loading history...</TableCell></TableRow>
                    ) : history && Array.isArray(history) && history.length > 0 ? (
                      history.map((result, i) => (
                        <TableRow key={i} className="border-border hover:bg-accent/50 transition-colors">
                          <TableCell className="font-bold text-foreground">{asset.toUpperCase()}</TableCell>
                          <TableCell className="text-green-400 font-mono">
                            {result.win_rate != null ? `${(result.win_rate * 100).toFixed(1)}%` : '—'}
                          </TableCell>
                          <TableCell className="text-blue-400 font-mono">
                            {result.profit_factor != null ? result.profit_factor.toFixed(2) : '—'}
                          </TableCell>
                          <TableCell className="text-right text-card-foreground font-black">
                            {result.net_profit != null ? `$${result.net_profit.toLocaleString()}` : '—'}
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end gap-2">
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground">
                                <History className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-red-400">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-12 text-muted-foreground italic">
                          No simulation history found. Run your first backtest!
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
