'use client';

import { useEffect, useState } from 'react';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';

interface PipelineStatus {
  status: 'active' | 'degraded';
  data_freshness: {
    gold:   { is_fresh: boolean; age_hours: number; rows: number };
    silver: { is_fresh: boolean; age_hours: number; rows: number };
  };
  models: {
    gold:   { exists: boolean; version: string; features: number };
    silver: { exists: boolean; version: string; features: number };
  };
  last_update: string;
}

interface PillProps {
  label: string;
  value: string;
  ok?: boolean;
  neutral?: boolean;
}

function StatusPill({ label, value, ok, neutral }: PillProps) {
  return (
    <div className="flex items-center gap-1.5 border-r border-terminal-rule pr-4 last:border-0">
      <span
        className={cn('w-1.5 h-1.5 rounded-full shrink-0', {
          'bg-terminal-buy': ok === true,
          'bg-terminal-sell': ok === false,
          'bg-terminal-hold': neutral,
          'bg-terminal-label': ok === undefined && !neutral,
        })}
      />
      <span className="text-[8px] font-mono text-terminal-label tracking-widest">{label}</span>
      <span className={cn('text-[9px] font-mono font-bold tracking-wide', {
        'text-terminal-buy': ok === true,
        'text-terminal-sell': ok === false,
        'text-terminal-hold': neutral,
        'text-terminal-value': ok === undefined && !neutral,
      })}>
        {value}
      </span>
    </div>
  );
}

export default function PipelineSummary() {
  const [status, setStatus] = useState<PipelineStatus | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const data = await apiClient.getPipelineStatus();
        setStatus(data);
      } catch {
        setStatus(null);
      }
    };
    fetch();
    const id = setInterval(fetch, 60000);
    return () => clearInterval(id);
  }, []);

  // Fallback strip while loading or on error
  if (!status) {
    return (
      <div className="flex items-center gap-4 px-4 py-1.5 border-b border-terminal-rule bg-terminal-panel">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-terminal-label animate-pulse" />
          <span className="text-[8px] font-mono text-terminal-label tracking-widest">PIPELINE STATUS LOADING...</span>
        </div>
      </div>
    );
  }

  const isActive   = status.status === 'active';
  const goldFresh  = status.data_freshness.gold.is_fresh;
  const silverFresh = status.data_freshness.silver.is_fresh;
  const goldModel  = status.models.gold;
  const silverModel = status.models.silver;

  return (
    <div className="flex flex-wrap items-center gap-4 px-4 py-1.5 border-b border-terminal-rule bg-terminal-panel overflow-x-auto">
      {/* Overall */}
      <StatusPill
        label="PIPELINE"
        value={isActive ? 'OPERATIONAL' : 'DEGRADED'}
        ok={isActive}
      />

      {/* Data freshness */}
      <StatusPill
        label="XAU DATA"
        value={goldFresh ? `FRESH · ${status.data_freshness.gold.rows.toLocaleString()} rows` : `STALE · ${status.data_freshness.gold.age_hours.toFixed(1)}h`}
        ok={goldFresh}
      />
      <StatusPill
        label="XAG DATA"
        value={silverFresh ? `FRESH · ${status.data_freshness.silver.rows.toLocaleString()} rows` : `STALE · ${status.data_freshness.silver.age_hours.toFixed(1)}h`}
        ok={silverFresh}
      />

      {/* Models */}
      <StatusPill
        label="XAU MODEL"
        value={goldModel.exists ? goldModel.version || 'LOADED' : 'MISSING'}
        ok={goldModel.exists}
      />
      <StatusPill
        label="XAG MODEL"
        value={silverModel.exists ? silverModel.version || 'LOADED' : 'MISSING'}
        ok={silverModel.exists}
      />

      {/* Features */}
      <StatusPill
        label="FEATURES"
        value={`${goldModel.features || 89}`}
        neutral
      />

      {/* Last update */}
      <div className="ml-auto flex items-center gap-1.5">
        <span className="text-[8px] font-mono text-terminal-label tracking-widest">REFRESHED</span>
        <span className="text-[8px] font-mono text-terminal-value">
          {new Date(status.last_update).toLocaleTimeString('en-US', { hour12: false })}
        </span>
      </div>
    </div>
  );
}
