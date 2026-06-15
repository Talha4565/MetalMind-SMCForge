'use client';

import { useMemo, useState } from 'react';
import { Activity, AlertTriangle, BarChart3, PieChart, ShieldAlert, ShieldCheck, TrendingDown } from 'lucide-react';
import { MetricCard } from '@/components/Common/MetricCard';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';

const alertHistory = [
  {
    id: 'A-001',
    level: 'High',
    message: 'Concentration risk exceeded threshold for Gold',
    status: 'Active',
    timestamp: '2026-05-16 19:12',
  },
  {
    id: 'A-002',
    level: 'Medium',
    message: 'Silver exposure drifted above target range',
    status: 'Acknowledged',
    timestamp: '2026-05-16 14:48',
  },
  {
    id: 'A-003',
    level: 'Low',
    message: 'Trailing stop liquidity alert triggered',
    status: 'Resolved',
    timestamp: '2026-05-15 22:06',
  },
];

const riskPositions = [
  {
    name: 'Gold (XAU/USD)',
    exposure: '42%',
    risk: 'Moderate',
    pnl: '+2.8%',
  },
  {
    name: 'Silver (XAG/USD)',
    exposure: '25%',
    risk: 'High',
    pnl: '-1.6%',
  },
  {
    name: 'Macro-balanced basket',
    exposure: '33%',
    risk: 'Low',
    pnl: '+1.2%',
  },
];

const toleranceOptions = [
  { value: 'conservative', label: 'Conservative', description: 'Lower drawdown, smaller position sizing.' },
  { value: 'balanced', label: 'Balanced', description: 'Moderate exposure with diversified risk.' },
  { value: 'aggressive', label: 'Aggressive', description: 'Higher risk tolerance for larger gains.' },
];

export default function RiskMetrics() {
  const [riskTolerance, setRiskTolerance] = useState('balanced');
  const [showOnlyActive, setShowOnlyActive] = useState(false);

  const filteredAlerts = useMemo(
    () => alertHistory.filter((alert) => !showOnlyActive || alert.status === 'Active'),
    [showOnlyActive]
  );

  return (
    <div className="space-y-8">
      <div className="rounded-3xl border border-border bg-card p-6 shadow-lg shadow-black/20">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Risk Monitor</p>
            <h1 className="mt-2 text-3xl font-black text-card-foreground">Portfolio risk dashboard</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Monitor tail risk, exposure, and alerts with the Risk Monitor agent. This dashboard surfaces portfolio risk and enables fast response to new events.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-3xl border border-border bg-background p-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <ShieldCheck className="h-5 w-5 text-emerald-400" />
                <span className="text-xs uppercase tracking-[0.25em]">Agent status</span>
              </div>
              <p className="mt-3 text-2xl font-black text-card-foreground">Online</p>
              <p className="text-sm text-slate-500">Risk monitor actively scanning exposure and alert triggers.</p>
            </div>
            <div className="rounded-3xl border border-border bg-background p-4">
              <div className="flex items-center gap-3 text-muted-foreground">
                <Activity className="h-5 w-5 text-sky-400" />
                <span className="text-xs uppercase tracking-[0.25em]">Next review</span>
              </div>
              <p className="mt-3 text-2xl font-black text-card-foreground">12 min</p>
              <p className="text-sm text-slate-500">Automated risk scan will refresh with the next batch of model outputs.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.4fr_0.95fr]">
        <section className="space-y-6">
          <div className="grid gap-6 md:grid-cols-3">
            <MetricCard
              label="Value at Risk (95%)"
              value="$78.2K"
              change={4.3}
              trend="down"
              icon={<TrendingDown className="w-5 h-5" />}
              className="col-span-1"
            />
            <MetricCard
              label="Max Drawdown"
              value="11.4%"
              change={2.1}
              trend="down"
              icon={<BarChart3 className="w-5 h-5" />}
              className="col-span-1"
            />
            <MetricCard
              label="Exposure"
              value="100%"
              change={0.9}
              trend="neutral"
              icon={<PieChart className="w-5 h-5" />}
              className="col-span-1"
            />
          </div>

          <div className="rounded-3xl border border-border bg-background p-6">
            <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-xl font-semibold text-card-foreground">Active risk positions</h2>
                <p className="text-sm text-slate-500">Current exposures that contribute most to portfolio risk.</p>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-card px-3 py-2 text-xs uppercase tracking-[0.24em] text-muted-foreground">
                <ShieldAlert className="h-4 w-4" /> High priority
              </div>
            </div>

            <Table className="min-w-full rounded-3xl border border-border bg-background">
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Exposure</TableHead>
                  <TableHead>Risk level</TableHead>
                  <TableHead>Unrealized P/L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {riskPositions.map((position) => (
                  <TableRow key={position.name}>
                    <TableCell className="text-card-foreground font-semibold">{position.name}</TableCell>
                    <TableCell>{position.exposure}</TableCell>
                    <TableCell>{position.risk}</TableCell>
                    <TableCell className={position.pnl.startsWith('-') ? 'text-rose-300' : 'text-emerald-300'}>{position.pnl}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          <div className="rounded-3xl border border-border bg-card p-6">
            <div className="mb-4 flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-card-foreground">Risk alert history</h2>
                <p className="text-sm text-slate-500">Recent alerts raised by the monitor agent.</p>
              </div>
              <Button
                variant="secondary"
                onClick={() => setShowOnlyActive((prev) => !prev)}
              >
                {showOnlyActive ? 'Show all alerts' : 'Show active only'}
              </Button>
            </div>

            <div className="overflow-hidden rounded-3xl border border-border bg-background">
              <Table className="min-w-full">
                <TableHeader>
                  <TableRow>
                    <TableHead>Alert</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAlerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell className="text-card-foreground font-semibold">{alert.message}</TableCell>
                      <TableCell>{alert.status}</TableCell>
                      <TableCell>{alert.level}</TableCell>
                      <TableCell>{alert.timestamp}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-3xl border border-border bg-background p-6">
            <div className="mb-4 flex items-center gap-3 text-muted-foreground">
              <ShieldAlert className="h-5 w-5 text-sky-400" />
              <span className="text-xs uppercase tracking-[0.25em]">Risk tolerance</span>
            </div>
            <p className="text-sm text-muted-foreground">Select a risk profile to adjust trade sizing, exposure, and alert thresholds.</p>
            <div className="mt-6 space-y-3">
              {toleranceOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setRiskTolerance(option.value)}
                  className={`w-full rounded-3xl border px-4 py-4 text-left transition ${riskTolerance === option.value ? 'border-blue-500 bg-card text-card-foreground shadow-lg shadow-blue-500/10' : 'border-border bg-background text-slate-300 hover:border-slate-700 hover:bg-card'}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-card-foreground">{option.label}</p>
                      <p className="mt-1 text-sm text-slate-500">{option.description}</p>
                    </div>
                    {riskTolerance === option.value && <span className="rounded-full bg-blue-500/10 px-2 py-1 text-xs uppercase tracking-[0.24em] text-blue-300">Selected</span>}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-3xl border border-border bg-background p-6">
            <div className="flex items-center gap-3 text-muted-foreground">
              <AlertTriangle className="h-5 w-5 text-amber-400" />
              <span className="text-xs uppercase tracking-[0.25em]">Risk controls</span>
            </div>
            <div className="mt-4 space-y-3 text-sm text-muted-foreground">
              <div className="rounded-2xl bg-card p-4">
                <p className="text-slate-300 font-semibold">Auto stop loss</p>
                <p className="mt-2 text-slate-500">Enabled for high-risk positions.</p>
              </div>
              <div className="rounded-2xl bg-card p-4">
                <p className="text-slate-300 font-semibold">Daily risk budget</p>
                <p className="mt-2 text-slate-500">Max 2.4% drawdown per session.</p>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
