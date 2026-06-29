'use client';

import { useEffect, useState } from 'react';
import DashboardLayout from '@/components/Common/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Activity, Database, Cpu, RefreshCcw, Play, CheckCircle2, AlertCircle, Clock } from 'lucide-react';
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
    const interval = setInterval(fetchDetails, 30000);
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
        <div>
          <h1 className="text-3xl font-black tracking-tight text-card-foreground">Pipeline Orchestrator</h1>
          <p className="text-muted-foreground mt-1">Monitor and control data pipelines, feature engineering, and model training.</p>
        </div>

        {/* Health Status */}
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={cn(
                  "w-3 h-3 rounded-full",
                  details?.health?.status === 'healthy' ? "bg-green-500 animate-pulse" : "bg-yellow-500"
                )} />
                <div>
                  <p className="text-sm font-bold text-card-foreground">System Health: {details?.health?.status ?? 'unknown'}</p>
                  <p className="text-[10px] text-muted-foreground">Uptime: {details?.health?.uptime ?? '--'}</p>
                </div>
              </div>
              <Button variant="outline" size="sm" onClick={fetchDetails} className="border-border">
                <RefreshCcw className="w-4 h-4 mr-2" /> Refresh
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Pipeline Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {details?.pipelines && Object.entries(details.pipelines).map(([key, pipeline]) => (
            <Card key={key} className="bg-card border-border">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-bold">{pipeline.name}</CardTitle>
                  <span className={cn(
                    "px-2 py-0.5 rounded-full text-[10px] font-bold",
                    pipeline.status === 'active' ? "bg-green-500/20 text-green-400" : "bg-yellow-500/20 text-yellow-400"
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
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Data Freshness */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {['gold', 'silver'].map(asset => {
            const data = details?.data?.[asset as keyof typeof details.data];
            if (!data) return null;
            return (
              <Card key={asset} className="bg-card border-border">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-bold uppercase">{asset} Data</CardTitle>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold",
                      data.is_fresh ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    )}>
                      {data.is_fresh ? 'Fresh' : 'Stale'}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Rows</span>
                    <span className="text-card-foreground font-mono">{data.rows.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Age</span>
                    <span className="text-card-foreground font-mono">{data.age_hours}h</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Last Update</span>
                    <span className="text-card-foreground font-mono text-[10px]">
                      {data.last_date ? new Date(data.last_date).toLocaleString() : 'N/A'}
                    </span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full mt-2 border-border"
                    onClick={() => handleTrigger('update', asset)}
                    disabled={running === `update-${asset}`}
                  >
                    {running === `update-${asset}` ? (
                      <RefreshCcw className="w-3 h-3 mr-2 animate-spin" />
                    ) : (
                      <Play className="w-3 h-3 mr-2" />
                    )}
                    Update Data
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Model Info */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {['gold', 'silver'].map(asset => {
            const model = details?.models?.[asset as keyof typeof details.models];
            if (!model) return null;
            return (
              <Card key={asset} className="bg-card border-border">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-bold uppercase">{asset} Model</CardTitle>
                    <span className={cn(
                      "px-2 py-0.5 rounded-full text-[10px] font-bold",
                      model.exists ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                    )}>
                      {model.exists ? 'Loaded' : 'Missing'}
                    </span>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Version</span>
                    <span className="text-card-foreground font-mono">{model.version || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Features</span>
                    <span className="text-card-foreground font-mono">{model.features}</span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Size</span>
                    <span className="text-card-foreground font-mono">{model.size_mb} MB</span>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="w-full mt-2 border-border"
                    onClick={() => handleTrigger('retrain', asset)}
                    disabled={running === `retrain-${asset}`}
                  >
                    {running === `retrain-${asset}` ? (
                      <RefreshCcw className="w-3 h-3 mr-2 animate-spin" />
                    ) : (
                      <Cpu className="w-3 h-3 mr-2" />
                    )}
                    Retrain Model
                  </Button>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
