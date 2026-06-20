'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Activity, Database, Cpu, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface PipelineStatus {
  status: 'active' | 'degraded';
  data_freshness: {
    gold: { is_fresh: boolean; age_hours: number; rows: number };
    silver: { is_fresh: boolean; age_hours: number; rows: number };
  };
  models: {
    gold: { exists: boolean; version: string; features: number };
    silver: { exists: boolean; version: string; features: number };
  };
  last_update: string;
}

export default function PipelineSummary() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await apiClient.getPipelineStatus();
        setStatus(data);
      } catch {
        setStatus(null);
      } finally {
        setLoading(false);
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card className="bg-card border-border animate-pulse">
        <CardContent className="p-4">
          <div className="h-8 bg-muted rounded" />
        </CardContent>
      </Card>
    );
  }

  if (!status) return null;

  const isActive = status.status === 'active';
  const goldFresh = status.data_freshness.gold.is_fresh;
  const silverFresh = status.data_freshness.silver.is_fresh;

  return (
    <Card className="bg-card border-border">
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-2.5 h-2.5 rounded-full",
              isActive ? "bg-green-500 animate-pulse" : "bg-yellow-500"
            )} />
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Pipeline Status</p>
              <p className="text-sm font-bold text-card-foreground">
                {isActive ? 'All Systems Operational' : 'Degraded'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6 text-[10px] text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <Database className="w-3 h-3" />
              <span>Data: {goldFresh && silverFresh ? 'Fresh' : 'Stale'}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3 h-3" />
              <span>Model: {status.models.gold.version || 'N/A'}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Activity className="w-3 h-3" />
              <span>89 Features</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
