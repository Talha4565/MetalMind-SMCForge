'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { apiClient } from '@/lib/api-client';
import { Activity, Database, Cpu, RefreshCcw, CheckCircle2, AlertCircle, Clock, HardDrive } from 'lucide-react';
import { cn } from '@/lib/utils';

interface OrchestratorData {
  pipeline: any;
  mt5_cache: { exists: boolean; fresh: boolean; age_seconds: number | null; updated_at?: string; error?: string };
  chromadb: { connected: boolean; signal_count: number; error?: string };
  retrain: { outcomes_available: number; win_rate: number; should_retrain: boolean; error?: string };
  timestamp: string;
}

function StatusPill({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-background">
      <span className={cn('w-2 h-2 rounded-full', ok === true ? 'bg-emerald-500' : ok === false ? 'bg-red-500' : 'bg-zinc-500')} />
      <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{label}</span>
      <span className="text-xs font-mono font-bold text-card-foreground ml-auto">{value}</span>
    </div>
  );
}

export default function OrchestratorPage() {
  const [data, setData] = useState<OrchestratorData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStatus = async () => {
    try {
      const result = await apiClient.getPipelineStatus();
      // Fetch orchestrator-specific data
      const resp = await fetch('/api/orchestrator/status');
      if (resp.ok) {
        const orchData = await resp.json();
        setData(orchData);
      }
    } catch {
      // Use pipeline status as fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground flex items-center gap-3">
              <Cpu className="w-8 h-8 text-emerald-500" />
              Orchestrator
            </h1>
            <p className="text-muted-foreground mt-1">Pipeline health, data freshness, model status, and retrain monitoring.</p>
          </div>
          <Button variant="outline" size="sm" className="border-border w-fit" onClick={fetchStatus}>
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>

        {/* MT5 Cache Status */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-emerald-400" /> MT5 Price Cache
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill label="Status" value={data?.mt5_cache?.fresh ? 'FRESH' : 'STALE'} ok={data?.mt5_cache?.fresh} />
              <StatusPill label="Age" value={data?.mt5_cache?.age_seconds != null ? `${data.mt5_cache.age_seconds}s` : '—'} ok={data?.mt5_cache?.age_seconds != null && data.mt5_cache.age_seconds < 60} />
              <StatusPill label="Source" value="MT5" ok />
              <StatusPill label="Updated" value={data?.mt5_cache?.updated_at ? new Date(data.mt5_cache.updated_at).toLocaleTimeString() : '—'} />
            </div>
          </CardContent>
        </Card>

        {/* ChromaDB Status */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" /> ChromaDB Signal Memory
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <StatusPill label="Connection" value={data?.chromadb?.connected ? 'Connected' : 'Disconnected'} ok={data?.chromadb?.connected} />
              <StatusPill label="Signals" value={String(data?.chromadb?.signal_count ?? 0)} />
              <StatusPill label="Collection" value="signal_patterns" />
            </div>
          </CardContent>
        </Card>

        {/* Retrain Status */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Activity className="w-4 h-4 text-amber-400" /> Self-Learning
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill label="Outcomes" value={String(data?.retrain?.outcomes_available ?? 0)} />
              <StatusPill label="Win Rate" value={data?.retrain?.win_rate != null ? `${(data.retrain.win_rate * 100).toFixed(1)}%` : '—'} ok={data?.retrain?.win_rate != null && data.retrain.win_rate >= 0.55} />
              <StatusPill label="Retrain Ready" value={data?.retrain?.should_retrain ? 'YES' : 'NO'} ok={data?.retrain?.should_retrain} />
              <StatusPill label="Threshold" value="50 outcomes / 55%" />
            </div>
          </CardContent>
        </Card>

        {/* Data Freshness */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" /> Data Freshness
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill label="Gold 15m" value={data?.pipeline?.freshness?.gold?.is_fresh ? 'Fresh' : 'Stale'} ok={data?.pipeline?.freshness?.gold?.is_fresh} />
              <StatusPill label="Gold Age" value={data?.pipeline?.freshness?.gold?.age_hours != null ? `${data.pipeline.freshness.gold.age_hours}h` : '—'} />
              <StatusPill label="Silver 15m" value={data?.pipeline?.freshness?.silver?.is_fresh ? 'Fresh' : 'Stale'} ok={data?.pipeline?.freshness?.silver?.is_fresh} />
              <StatusPill label="Silver Age" value={data?.pipeline?.freshness?.silver?.age_hours != null ? `${data.pipeline.freshness.silver.age_hours}h` : '—'} />
            </div>
          </CardContent>
        </Card>

        {/* Model Status */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-sm font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Model Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <StatusPill label="Gold Model" value={data?.pipeline?.freshness?.gold?.is_fresh ? 'Loaded' : 'Unknown'} ok={data?.pipeline?.freshness?.gold?.is_fresh} />
              <StatusPill label="Silver Model" value={data?.pipeline?.freshness?.silver?.is_fresh ? 'Loaded' : 'Unknown'} ok={data?.pipeline?.freshness?.silver?.is_fresh} />
              <StatusPill label="Framework" value="XGBoost + SMC" />
              <StatusPill label="Features" value="89" />
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
