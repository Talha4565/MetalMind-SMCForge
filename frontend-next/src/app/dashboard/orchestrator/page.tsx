'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';
import {
  Activity, Database, Cpu, RefreshCcw, CheckCircle2, AlertCircle,
  Clock, HardDrive, Shield, TrendingUp, TrendingDown, Zap, BarChart3
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrchestratorData {
  pipeline: {
    health: {
      last_update: string | null;
      last_retrain: string | null;
      update_status: string;
      retrain_status: string;
      update_error: string | null;
      retrain_error: string | null;
      consecutive_failures: number;
      uptime_since: string;
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
  mt5_cache: {
    exists: boolean;
    fresh: boolean;
    age_seconds: number | null;
    updated_at?: string;
    error?: string;
  };
  chromadb: {
    connected: boolean;
    signal_count: number;
    error?: string;
  };
  retrain: {
    outcomes_available: number;
    win_rate: number;
    should_retrain: boolean;
    last_run: string | null;
    error?: string;
  };
  timestamp: string;
}

function StatusPill({ label, value, ok, icon: Icon }: { label: string; value: string; ok?: boolean; icon?: typeof Activity }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background">
      <span className={cn('w-2 h-2 rounded-full', ok === true ? 'bg-emerald-500' : ok === false ? 'bg-red-500' : 'bg-zinc-500')} />
      {Icon && <Icon className={cn('w-3 h-3', ok === true ? 'text-emerald-500' : ok === false ? 'text-red-500' : 'text-zinc-500')} />}
      <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</span>
      <span className="text-xs font-mono font-bold text-card-foreground ml-auto">{value}</span>
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
        <div key={key} className="flex items-center gap-3 px-3 py-2 rounded-lg border border-border bg-background">
          <span className={cn(
            "w-2 h-2 rounded-full",
            job.status === 'success' ? 'bg-emerald-500' : job.status === 'failed' ? 'bg-red-500' : 'bg-amber-500'
          )} />
          <div className="flex-1 min-w-0">
            <p className="text-xs font-bold text-card-foreground truncate">{key}</p>
            <p className="text-[10px] text-muted-foreground">
              {job.started_at ? new Date(job.started_at).toLocaleString() : 'N/A'}
            </p>
          </div>
          <div className="text-right">
            {job.result?.accuracy && (
              <p className="text-xs font-mono text-emerald-400">{(job.result.accuracy * 100).toFixed(1)}%</p>
            )}
            {job.result?.records_added !== undefined && (
              <p className="text-xs font-mono text-card-foreground">+{job.result.records_added}</p>
            )}
            {job.error && (
              <p className="text-[10px] text-red-400 truncate max-w-[100px]">{job.error}</p>
            )}
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
      if (resp.ok) {
        const orchData = await resp.json();
        setData(orchData);
      }
    } catch (e) {
      console.error('Failed to fetch orchestrator status:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000); // Poll every 60s to avoid rate limits
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-96">
          <RefreshCcw className="w-8 h-8 animate-spin text-muted-foreground" />
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
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground flex items-center gap-3">
              <Cpu className="w-8 h-8 text-emerald-500" />
              Orchestrator
            </h1>
            <p className="text-muted-foreground mt-1">Advanced monitoring: health, jobs, backups, and system status.</p>
          </div>
          <Button variant="outline" size="sm" className="border-border w-fit" onClick={fetchStatus}>
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>

        {/* Health Banner */}
        <Card className={cn(
          "border",
          health?.consecutive_failures === 0 ? "bg-emerald-500/5 border-emerald-500/20" : "bg-red-500/5 border-red-500/20"
        )}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Shield className={cn(
                  "w-5 h-5",
                  health?.consecutive_failures === 0 ? "text-emerald-500" : "text-red-500"
                )} />
                <div>
                  <p className="text-sm font-bold text-card-foreground">
                    System {health?.consecutive_failures === 0 ? 'Healthy' : `${health?.consecutive_failures} Consecutive Failures`}
                  </p>
                  <p className="text-[10px] text-muted-foreground">
                    Uptime since {health?.uptime_since ? new Date(health.uptime_since).toLocaleDateString() : 'N/A'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-[10px] text-muted-foreground">Last Update</p>
                <p className="text-xs font-mono text-card-foreground">
                  {health?.last_update ? new Date(health.last_update).toLocaleTimeString() : 'Never'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatusPill
            label="MT5 Cache"
            value={data?.mt5_cache?.fresh ? 'FRESH' : 'STALE'}
            ok={data?.mt5_cache?.fresh}
            icon={HardDrive}
          />
          <StatusPill
            label="ChromaDB"
            value={data?.chromadb?.connected ? `${data.chromadb.signal_count} signals` : 'Disconnected'}
            ok={data?.chromadb?.connected}
            icon={Database}
          />
          <StatusPill
            label="Win Rate"
            value={data?.retrain?.win_rate ? `${(data.retrain.win_rate * 100).toFixed(1)}%` : '—'}
            ok={data?.retrain?.win_rate != null && data.retrain.win_rate >= 0.55}
            icon={TrendingUp}
          />
          <StatusPill
            label="Outcomes"
            value={String(data?.retrain?.outcomes_available ?? 0)}
            icon={BarChart3}
          />
        </div>

        {/* Data Freshness */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" /> Data Freshness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill
                label="Gold 15m"
                value={data?.pipeline?.freshness?.gold?.is_fresh ? 'Fresh' : 'Stale'}
                ok={data?.pipeline?.freshness?.gold?.is_fresh}
              />
              <StatusPill
                label="Gold Age"
                value={data?.pipeline?.freshness?.gold?.age_hours != null ? `${data.pipeline.freshness.gold.age_hours}h` : '—'}
              />
              <StatusPill
                label="Silver 15m"
                value={data?.pipeline?.freshness?.silver?.is_fresh ? 'Fresh' : 'Stale'}
                ok={data?.pipeline?.freshness?.silver?.is_fresh}
              />
              <StatusPill
                label="Silver Age"
                value={data?.pipeline?.freshness?.silver?.age_hours != null ? `${data.pipeline.freshness.silver.age_hours}h` : '—'}
              />
            </div>
          </CardContent>
        </Card>

        {/* Job History */}
        {Object.keys(jobs).length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <Activity className="w-4 h-4 text-amber-400" /> Job History
                </CardTitle>
                {jobSummary && (
                  <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                    <span className="text-emerald-400">{jobSummary.success} success</span>
                    {jobSummary.failed > 0 && <span className="text-red-400">{jobSummary.failed} failed</span>}
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <JobTimeline jobs={jobs} />
            </CardContent>
          </Card>
        )}

        {/* Self-Learning */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400" /> Self-Learning
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill
                label="Outcomes"
                value={String(data?.retrain?.outcomes_available ?? 0)}
              />
              <StatusPill
                label="Win Rate"
                value={data?.retrain?.win_rate != null ? `${(data.retrain.win_rate * 100).toFixed(1)}%` : '—'}
                ok={data?.retrain?.win_rate != null && data.retrain.win_rate >= 0.55}
              />
              <StatusPill
                label="Retrain Ready"
                value={data?.retrain?.should_retrain ? 'YES' : 'NO'}
                ok={!data?.retrain?.should_retrain}
              />
              <StatusPill
                label="Threshold"
                value="50 outcomes / 55%"
              />
            </div>
          </CardContent>
        </Card>

        {/* Model Backups */}
        {backups.length > 0 && (
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-400" /> Model Backups
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {backups.map((backup, i) => (
                  <div key={i} className="flex items-center gap-3 px-3 py-2 rounded-lg border border-border bg-background">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-mono text-card-foreground truncate">{backup.name}</p>
                      <p className="text-[10px] text-muted-foreground">{backup.asset} model</p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-mono text-card-foreground">{backup.size_mb} MB</p>
                      <p className="text-[10px] text-muted-foreground">{backup.timestamp}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Health History */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-purple-400" /> Health History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill
                label="Update Status"
                value={health?.update_status || 'unknown'}
                ok={health?.update_status === 'success'}
              />
              <StatusPill
                label="Retrain Status"
                value={health?.retrain_status || 'unknown'}
                ok={health?.retrain_status === 'success'}
              />
              <StatusPill
                label="Last Retrain"
                value={health?.last_retrain ? new Date(health.last_retrain).toLocaleDateString() : 'Never'}
              />
              <StatusPill
                label="Failures"
                value={String(health?.consecutive_failures ?? 0)}
                ok={health?.consecutive_failures === 0}
              />
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
