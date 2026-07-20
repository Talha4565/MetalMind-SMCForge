'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalButton } from '@/components/Common/TerminalCard';
import { Activity, Database, Cpu, RefreshCcw, Play, Clock, GitBranch, TrendingUp } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface PipelineDetails {
  pipelines: {
    etl: { name: string; status: string; schedule: string; last_run: string; description: string };
    features: { name: string; status: string; schedule: string; features_count: number; description: string };
    training: { name: string; status: string; schedule: string; last_run: string; description: string };
  };
  data: {
    gold: { is_fresh: boolean; last_date: string; age_hours: number; rows: number; message: string };
    silver: { is_fresh: boolean; last_date: string; age_hours: number; rows: number; message: string };
  };
  models: {
    gold: { exists: boolean; version: string; size_mb: number; last_modified: string; features: number };
    silver: { exists: boolean; version: string; size_mb: number; last_modified: string; features: number };
  };
  health: { status: string; uptime: string; last_incident: string | null };
}

const PIPELINE_ICONS: Record<string, typeof Activity> = { etl: Database, features: GitBranch, training: Cpu };
const PIPELINE_COLORS: Record<string, string> = { etl: 'text-terminal-data', features: 'text-terminal-hold', training: 'text-terminal-buy' };

export default function PipelinePage() {
  const [details, setDetails] = useState<PipelineDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);

  const fetchDetails = async () => {
    try { setDetails(await apiClient.getPipelineDetails()); } catch { setDetails(null); } finally { setLoading(false); }
  };

  useEffect(() => { fetchDetails(); const interval = setInterval(fetchDetails, 60000); return () => clearInterval(interval); }, []);

  const handleTrigger = async (type: string, asset: string) => {
    const key = `${type}-${asset}`;
    setRunning(key);
    try { await apiClient.triggerPipeline(type, asset); await fetchDetails(); } catch { /* ignore */ } finally { setRunning(null); }
  };

  if (loading) {
    return <DashboardLayout><div className="flex items-center justify-center min-h-96"><RefreshCcw className="w-8 h-8 animate-spin text-terminal-label" /></div></DashboardLayout>;
  }

  if (!details) {
    return <DashboardLayout><div className="text-center py-12 font-mono text-terminal-label">Failed to load pipeline details</div></DashboardLayout>;
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono">PIPELINE</h1>
            <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">Data flow · feature engineering · model training</p>
          </div>
          <TerminalButton variant="secondary" size="sm" onClick={fetchDetails}>
            <RefreshCcw className="w-3 h-3" /> REFRESH
          </TerminalButton>
        </div>

        {/* System Health */}
        <div className={cn("border px-4 py-3", details.health?.status === 'healthy' ? "border-terminal-buy/20 bg-terminal-buy/5" : "border-terminal-hold/20 bg-terminal-hold/5")}>
          <div className="flex items-center gap-3">
            <div className={cn("w-3 h-3 rounded-full animate-pulse", details.health?.status === 'healthy' ? "bg-terminal-buy" : "bg-terminal-hold")} />
            <div>
              <p className="text-sm font-mono font-bold text-terminal-value">System {details.health?.status === 'healthy' ? 'Healthy' : 'Degraded'}</p>
              <p className="text-[9px] font-mono text-terminal-label">Uptime: {details.health?.uptime || 'N/A'}</p>
            </div>
          </div>
        </div>

        {/* 3 Pipeline Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {details.pipelines && Object.entries(details.pipelines).map(([key, pipeline]) => {
            const Icon = PIPELINE_ICONS[key] || Activity;
            const color = PIPELINE_COLORS[key] || 'text-terminal-label';
            return (
              <TerminalCard key={key} title={pipeline.name} code={key.slice(0, 3).toUpperCase()}>
                <div className="space-y-2">
                  <p className="text-[10px] font-mono text-terminal-label">{pipeline.description}</p>
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-terminal-label">
                    <Clock className="w-3 h-3" />{pipeline.schedule}
                  </div>
                  {'last_run' in pipeline && pipeline.last_run && (
                    <div className="text-[9px] font-mono text-terminal-label">Last: {new Date(pipeline.last_run).toLocaleString()}</div>
                  )}
                  {'features_count' in pipeline && (
                    <div className="text-[9px] font-mono text-terminal-label">Features: {pipeline.features_count}</div>
                  )}
                  <span className={cn('inline-block px-2 py-0.5 text-[9px] font-mono font-bold border',
                    pipeline.status === 'active' ? 'border-terminal-buy/20 text-terminal-buy' : 'border-terminal-hold/20 text-terminal-hold')}>
                    {pipeline.status}
                  </span>
                </div>
              </TerminalCard>
            );
          })}
        </div>

        {/* Data Freshness + Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {['gold', 'silver'].map(asset => {
            const data = details?.data?.[asset as keyof typeof details.data];
            const model = details?.models?.[asset as keyof typeof details.models];
            if (!data) return null;
            return (
              <TerminalCard key={asset} title={asset.toUpperCase()} code={asset === 'gold' ? 'XAU' : 'XAG'}
                right={<span className={cn('text-[9px] font-mono font-bold', data.is_fresh ? 'text-terminal-buy' : 'text-terminal-sell')}>{data.is_fresh ? 'FRESH' : 'STALE'}</span>}>
                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="p-2 border border-terminal-rule bg-terminal-panel">
                    <p className="text-[8px] font-mono text-terminal-label">Data Age</p>
                    <p className="text-lg font-mono font-bold text-terminal-value">{data.age_hours}h</p>
                  </div>
                  <div className="p-2 border border-terminal-rule bg-terminal-panel">
                    <p className="text-[8px] font-mono text-terminal-label">Rows</p>
                    <p className="text-lg font-mono font-bold text-terminal-value">{data.rows != null ? data.rows.toLocaleString() : '—'}</p>
                  </div>
                </div>
                {model && (
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div className="p-2 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono text-terminal-label">Model</p>
                      <p className="text-[10px] font-mono text-terminal-value">{model.exists ? `${model.size_mb} MB` : 'Missing'}</p>
                    </div>
                    <div className="p-2 border border-terminal-rule bg-terminal-panel">
                      <p className="text-[8px] font-mono text-terminal-label">Features</p>
                      <p className="text-[10px] font-mono text-terminal-value">{model.features}</p>
                    </div>
                  </div>
                )}
                <div className="flex gap-2">
                  <TerminalButton variant="secondary" size="sm" onClick={() => handleTrigger('update', asset)} disabled={running === `update-${asset}`} isLoading={running === `update-${asset}`}>
                    <Play className="w-3 h-3" /> UPDATE
                  </TerminalButton>
                  <TerminalButton variant="primary" size="sm" onClick={() => handleTrigger('retrain', asset)} disabled={running === `retrain-${asset}`} isLoading={running === `retrain-${asset}`}>
                    <Cpu className="w-3 h-3" /> RETRAIN
                  </TerminalButton>
                </div>
              </TerminalCard>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
