'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard, { TerminalButton } from '@/components/Common/TerminalCard';
import {
  Activity, Database, Cpu, RefreshCcw, CheckCircle2,
  Clock, HardDrive, Shield, TrendingUp, Zap, BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrchestratorData {
  pipeline: {
    health: {
      last_update: string | null; last_retrain: string | null;
      update_status: string; retrain_status: string;
      update_error: string | null; retrain_error: string | null;
      consecutive_failures: number; uptime_since: string;
    };
    status: {
      jobs: Record<string, any>;
      summary: { total_jobs: number; running: number; success: number; failed: number; health: string };
    };
    freshness: {
      gold: { is_fresh: boolean; age_hours: number; rows: number; last_date: string };
      silver: { is_fresh: boolean; age_hours: number; rows: number; last_date: string };
    };
    backups: Array<{ name: string; asset: string; timestamp: string; size_mb: number }>;
  };
  mt5_cache: { exists: boolean; fresh: boolean; age_seconds: number | null; updated_at?: string; error?: string };
  chromadb: { connected: boolean; signal_count: number; error?: string };
  retrain: { outcomes_available: number; win_rate: number; should_retrain: boolean; last_run: string | null; error?: string };
  timestamp: string;
}

function StatusPill({ label, value, ok, icon: Icon }: { label: string; value: string; ok?: boolean; icon?: typeof Activity }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 border border-terminal-rule bg-terminal-panel">
      <span className={cn('w-2 h-2 rounded-full', ok === true ? 'bg-terminal-buy' : ok === false ? 'bg-terminal-sell' : 'bg-terminal-label')} />
      {Icon && <Icon className={cn('w-3 h-3', ok === true ? 'text-terminal-buy' : ok === false ? 'text-terminal-sell' : 'text-terminal-label')} />}
      <span className="text-[9px] font-mono font-bold uppercase tracking-widest text-terminal-label">{label}</span>
      <span className="text-[10px] font-mono font-bold text-terminal-value ml-auto">{value}</span>
    </div>
  );
}

function JobTimeline({ jobs }: { jobs: Record<string, any> }) {
  const sortedJobs = Object.entries(jobs).sort((a, b) =>
    (b[1].started_at || '').localeCompare(a[1].started_at || '')
  );
  return (
    <div className="space-y-2">
      {sortedJobs.slice(0, 5).map(([key, job]) => (
        <div key={key} className="flex items-center gap-3 px-3 py-2 border border-terminal-rule bg-terminal-panel">
          <span className={cn("w-2 h-2 rounded-full",
            job.status === 'success' ? 'bg-terminal-buy' : job.status === 'failed' ? 'bg-terminal-sell' : 'bg-terminal-hold')} />
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-mono font-bold text-terminal-value truncate">{key}</p>
            <p className="text-[8px] font-mono text-terminal-label">{job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}</p>
          </div>
          <div className="text-right">
            {job.result?.accuracy && <p className="text-[10px] font-mono text-terminal-buy">{(job.result.accuracy * 100).toFixed(1)}%</p>}
            {job.result?.records_added !== undefined && <p className="text-[10px] font-mono text-terminal-value">+{job.result.records_added}</p>}
            {job.error && <p className="text-[9px] text-terminal-sell truncate max-w-[100px]">{job.error}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function OrchestratorPage() {
  const [data, setData] = useState<OrchestratorData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
      const resp = await fetch(`${API_BASE}/api/orchestrator/status`);
      if (resp.ok) setData(await resp.json());
    } catch (e) {
      console.error('Failed to fetch orchestrator status:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-96">
          <RefreshCcw className="w-8 h-8 animate-spin text-terminal-label" />
        </div>
      </DashboardLayout>
    );
  }

  const health = data?.pipeline?.health;
  const jobs = data?.pipeline?.status?.jobs || {};
  const jobSummary = data?.pipeline?.status?.summary;
  const backups = data?.pipeline?.backups || [];

  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono flex items-center gap-3">
              <Cpu className="w-7 h-7 text-terminal-hold" />
              ORCHESTRATOR
            </h1>
            <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">
              System health · job monitor · backup registry
            </p>
          </div>
          <TerminalButton variant="secondary" size="sm" onClick={fetchStatus}>
            <RefreshCcw className="w-3 h-3" /> REFRESH
          </TerminalButton>
        </div>

        {/* Health Banner */}
        <div className={cn("border px-4 py-3", health?.consecutive_failures === 0 ? "border-terminal-buy/20 bg-terminal-buy/5" : "border-terminal-sell/20 bg-terminal-sell/5")}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className={cn("w-5 h-5", health?.consecutive_failures === 0 ? "text-terminal-buy" : "text-terminal-sell")} />
              <div>
                <p className="text-sm font-mono font-bold text-terminal-value">
                  System {health?.consecutive_failures === 0 ? 'Healthy' : `${health?.consecutive_failures} Consecutive Failures`}
                </p>
                <p className="text-[9px] font-mono text-terminal-label">
                  Uptime since {health?.uptime_since ? new Date(health.uptime_since).toLocaleDateString() : 'N/A'}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-[9px] font-mono text-terminal-label">Last Update</p>
              <p className="text-[10px] font-mono text-terminal-value">{health?.last_update ? new Date(health.last_update).toLocaleTimeString() : 'Never'}</p>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <StatusPill label="MT5 Cache" value={data?.mt5_cache?.fresh ? 'FRESH' : 'STALE'} ok={data?.mt5_cache?.fresh} icon={HardDrive} />
          <StatusPill label="ChromaDB" value={data?.chromadb?.connected ? `${data.chromadb.signal_count} signals` : 'Offline'} ok={data?.chromadb?.connected} icon={Database} />
          <StatusPill label="Win Rate" value={data?.retrain?.win_rate ? `${(data.retrain.win_rate * 100).toFixed(1)}%` : '—'} ok={data?.retrain?.win_rate != null && data.retrain.win_rate >= 0.55} icon={TrendingUp} />
          <StatusPill label="Outcomes" value={String(data?.retrain?.outcomes_available ?? 0)} icon={BarChart3} />
        </div>

        {/* Data Freshness */}
        <TerminalCard title="DATA FRESHNESS" code="DFH">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatusPill label="Gold 15m" value={data?.pipeline?.freshness?.gold?.is_fresh ? 'Fresh' : 'Stale'} ok={data?.pipeline?.freshness?.gold?.is_fresh} />
            <StatusPill label="Gold Age" value={data?.pipeline?.freshness?.gold?.age_hours != null ? `${data.pipeline.freshness.gold.age_hours}h` : '—'} />
            <StatusPill label="Silver 15m" value={data?.pipeline?.freshness?.silver?.is_fresh ? 'Fresh' : 'Stale'} ok={data?.pipeline?.freshness?.silver?.is_fresh} />
            <StatusPill label="Silver Age" value={data?.pipeline?.freshness?.silver?.age_hours != null ? `${data.pipeline.freshness.silver.age_hours}h` : '—'} />
          </div>
        </TerminalCard>

        {/* Job History */}
        {Object.keys(jobs).length > 0 && (
          <TerminalCard title="JOB HISTORY" code="JOB" right={jobSummary ? (
            <span className="text-[9px] font-mono tracking-widest">
              <span className="text-terminal-buy">{jobSummary.success} OK</span>
              {jobSummary.failed > 0 && <span className="text-terminal-sell ml-2">{jobSummary.failed} FAIL</span>}
            </span>
          ) : undefined}>
            <JobTimeline jobs={jobs} />
          </TerminalCard>
        )}

        {/* Self-Learning */}
        <TerminalCard title="SELF-LEARNING" code="LRN">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatusPill label="Outcomes" value={String(data?.retrain?.outcomes_available ?? 0)} />
            <StatusPill label="Win Rate" value={data?.retrain?.win_rate != null ? `${(data.retrain.win_rate * 100).toFixed(1)}%` : '—'} ok={data?.retrain?.win_rate != null && data.retrain.win_rate >= 0.55} />
            <StatusPill label="Retrain Ready" value={data?.retrain?.should_retrain ? 'YES' : 'NO'} ok={!data?.retrain?.should_retrain} />
            <StatusPill label="Threshold" value="50 / 55%" />
          </div>
        </TerminalCard>

        {/* Model Backups */}
        {backups.length > 0 && (
          <TerminalCard title="MODEL BACKUPS" code="BAK">
            <div className="space-y-2">
              {backups.map((backup, i) => (
                <div key={i} className="flex items-center gap-3 px-3 py-2 border border-terminal-rule bg-terminal-panel">
                  <CheckCircle2 className="w-4 h-4 text-terminal-buy" />
                  <div className="flex-1 min-w-0">
                    <p className="text-[10px] font-mono text-terminal-value truncate">{backup.name}</p>
                    <p className="text-[8px] font-mono text-terminal-label">{backup.asset} model</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] font-mono text-terminal-value">{backup.size_mb} MB</p>
                    <p className="text-[8px] font-mono text-terminal-label">{backup.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>
          </TerminalCard>
        )}

        {/* Health History */}
        <TerminalCard title="HEALTH HISTORY" code="HLTH">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <StatusPill label="Update Status" value={health?.update_status || 'unknown'} ok={health?.update_status === 'success'} />
            <StatusPill label="Retrain Status" value={health?.retrain_status || 'unknown'} ok={health?.retrain_status === 'success'} />
            <StatusPill label="Last Retrain" value={health?.last_retrain ? new Date(health.last_retrain).toLocaleDateString() : 'Never'} />
            <StatusPill label="Failures" value={String(health?.consecutive_failures ?? 0)} ok={health?.consecutive_failures === 0} />
          </div>
        </TerminalCard>
      </div>
    </DashboardLayout>
  );
}
