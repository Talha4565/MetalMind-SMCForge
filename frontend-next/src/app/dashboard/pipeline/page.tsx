'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, Database, Cpu, RefreshCcw, Play, CheckCircle2, AlertCircle, Clock, Zap, GitBranch, TrendingUp } from 'lucide-react';
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

const PIPELINE_ICONS: Record<string, typeof Activity> = {
  etl: Database,
  features: GitBranch,
  training: Cpu,
};

const PIPELINE_COLORS: Record<string, string> = {
  etl: 'text-blue-400',
  features: 'text-purple-400',
  training: 'text-amber-400',
};

export default function PipelinePage() {
  const [details, setDetails] = useState<PipelineDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);

  const fetchDetails = async () => {
    try {
      const data = await apiClient.getPipelineDetails();
      setDetails(data);
    } catch {
      setDetails(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetails();
    const interval = setInterval(fetchDetails, 60000); // Poll every 60s to avoid rate limits
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async (type: string, asset: string) => {
    const key = `${type}-${asset}`;
    setRunning(key);
    try {
      await apiClient.triggerPipeline(type, asset);
      await fetchDetails();
    } catch {
      // ignore
    } finally {
      setRunning(null);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-96">
          <RefreshCcw className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      </DashboardLayout>
    );
  }

  if (!details) {
    return (
      <DashboardLayout>
        <div className="text-center py-12 text-muted-foreground">Failed to load pipeline details</div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-black tracking-tight text-card-foreground">Pipeline</h1>
            <p className="text-muted-foreground mt-1">Data flow, feature engineering, and model training pipelines.</p>
          </div>
          <Button variant="outline" size="sm" className="border-border w-fit" onClick={fetchDetails}>
            <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
          </Button>
        </div>

        {/* System Health Banner */}
        <Card className={cn(
          "border",
          details.health?.status === 'healthy' ? "bg-emerald-500/5 border-emerald-500/20" : "bg-amber-500/5 border-amber-500/20"
        )}>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className={cn(
                "w-3 h-3 rounded-full animate-pulse",
                details.health?.status === 'healthy' ? "bg-emerald-500" : "bg-amber-500"
              )} />
              <div>
                <p className="text-sm font-bold text-card-foreground">
                  System {details.health?.status === 'healthy' ? 'Healthy' : 'Degraded'}
                </p>
                <p className="text-[10px] text-muted-foreground">
                  Uptime: {details.health?.uptime || 'N/A'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 3 Pipeline Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {details.pipelines && Object.entries(details.pipelines).map(([key, pipeline]) => {
            const Icon = PIPELINE_ICONS[key] || Activity;
            const color = PIPELINE_COLORS[key] || 'text-muted-foreground';
            return (
              <Card key={key} className="bg-card border-border">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-bold flex items-center gap-2">
                      <Icon className={cn("w-4 h-4", color)} />
                      {pipeline.name}
                    </CardTitle>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold",
                      pipeline.status === 'active' ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"
                    )}>
                      {pipeline.status}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-xs text-muted-foreground">{pipeline.description}</p>
                  <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    <span>{pipeline.schedule}</span>
                  </div>
                  {'last_run' in pipeline && pipeline.last_run && (
                    <div className="text-[10px] text-muted-foreground">
                      Last: {new Date(pipeline.last_run).toLocaleString()}
                    </div>
                  )}
                  {'features_count' in pipeline && (
                    <div className="text-[10px] text-muted-foreground">
                      Features: {pipeline.features_count}
                    </div>
                  )}
                </CardContent>
              </Card>
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
              <Card key={asset} className="bg-card border-border">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-bold uppercase flex items-center gap-2">
                      {asset === 'gold' ? <TrendingUp className="w-4 h-4 text-amber-400" /> : <TrendingUp className="w-4 h-4 text-slate-400" />}
                      {asset}
                    </CardTitle>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold",
                      data.is_fresh ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"
                    )}>
                      {data.is_fresh ? 'Fresh' : 'Stale'}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-[10px] text-muted-foreground">Data Age</p>
                      <p className="text-lg font-mono font-bold text-card-foreground">{data.age_hours}h</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-muted-foreground">Rows</p>
                      <p className="text-lg font-mono font-bold text-card-foreground">{data.rows.toLocaleString()}</p>
                    </div>
                  </div>
                  {model && (
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-[10px] text-muted-foreground">Model</p>
                        <p className="text-xs font-mono text-card-foreground">{model.exists ? `${model.size_mb} MB` : 'Missing'}</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-muted-foreground">Features</p>
                        <p className="text-xs font-mono text-card-foreground">{model.features}</p>
                      </div>
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 border-border"
                      onClick={() => handleTrigger('update', asset)}
                      disabled={running === `update-${asset}`}
                    >
                      {running === `update-${asset}` ? (
                        <RefreshCcw className="w-3 h-3 mr-1 animate-spin" />
                      ) : (
                        <Play className="w-3 h-3 mr-1" />
                      )}
                      Update Data
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 border-border"
                      onClick={() => handleTrigger('retrain', asset)}
                      disabled={running === `retrain-${asset}`}
                    >
                      {running === `retrain-${asset}` ? (
                        <RefreshCcw className="w-3 h-3 mr-1 animate-spin" />
                      ) : (
                        <Cpu className="w-3 h-3 mr-1" />
                      )}
                      Retrain
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
