'use client';

import { PredictionItem } from '@/lib/api-types';
import { TrendingUp, TrendingDown, Minus, Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';
import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { SHAP_LABELS } from '@/lib/shap-labels';

function label(raw: string) {
  return SHAP_LABELS[raw] ?? raw.replace(/_/g, ' ').toUpperCase().slice(0, 18);
}

interface Props {
  prediction: PredictionItem;
  isLoading?: boolean;
  livePrice?: number | null;
}

export default function TerminalSignalPanel({ prediction, isLoading, livePrice }: Props) {
  const { data: wsData, isConnected, emit } = useWebSocket<PredictionItem>('predictions');

  useEffect(() => {
    if (isConnected) emit('subscribe_predictions', { asset: prediction.asset });
  }, [isConnected, prediction.asset, emit]);

  const current = wsData?.asset === prediction.asset ? wsData : prediction;

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-8 bg-terminal-panel border border-terminal-rule" />
        ))}
      </div>
    );
  }

  const rawSignal = typeof current.signal === 'string' ? current.signal.toUpperCase() : current.signal;
  const isBuy  = rawSignal === 'BUY'  || rawSignal === 1;
  const isSell = rawSignal === 'SELL' || rawSignal === -1;
  const signalLabel = isBuy ? 'BUY' : isSell ? 'SELL' : 'HOLD';

  const signalClass = isBuy
    ? 'text-terminal-buy border-terminal-buy/40 bg-terminal-buy/5'
    : isSell
      ? 'text-terminal-sell border-terminal-sell/40 bg-terminal-sell/5'
      : 'text-terminal-hold border-terminal-hold/40 bg-terminal-hold/5';

  const Icon = isBuy ? TrendingUp : isSell ? TrendingDown : Minus;

  const shap = current.shap_values ?? [];
  const maxAbs = Math.max(...shap.map(s => Math.abs(s.contribution)), 0.001);
  const topShap = [...shap].sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution)).slice(0, 6);

  const displayPrice = livePrice ?? current.price;

  return (
    <div className="space-y-3">
      {/* Signal hero row */}
      <div className={cn('flex items-center justify-between border px-3 py-2.5', signalClass)}>
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4" />
          <span className="text-[18px] font-mono font-black tracking-wider">{signalLabel}</span>
        </div>
        <div className="text-right">
          <p className="text-[9px] font-mono text-terminal-label tracking-widest">CONFIDENCE</p>
          <p className="text-[14px] font-mono font-black tabular-nums">
            {current.confidence != null ? `${(current.confidence * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
      </div>

      {/* Price row */}
      <div className="grid grid-cols-2 gap-px bg-terminal-rule">
        <div className="bg-terminal-panel px-3 py-2">
          <p className="text-[8px] font-mono text-terminal-label tracking-widest mb-1">
            {livePrice != null ? 'LIVE PRICE' : 'LAST CLOSE'}
          </p>
          <p className="text-[14px] font-mono font-black text-terminal-value tabular-nums">
            ${displayPrice > 0 ? displayPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—'}
          </p>
        </div>
        <div className="bg-terminal-panel px-3 py-2">
          <p className="text-[8px] font-mono text-terminal-label tracking-widest mb-1">PROBABILITY</p>
          <p className="text-[14px] font-mono font-black text-terminal-data tabular-nums">
            {current.probability != null ? `${(current.probability * 100).toFixed(1)}%` : '—'}
          </p>
        </div>
      </div>

      {/* Connection status */}
      <div className="flex items-center gap-1.5 px-1">
        {isConnected
          ? <Wifi className="w-3 h-3 text-terminal-buy" />
          : <WifiOff className="w-3 h-3 text-terminal-sell" />
        }
        <span className={cn('text-[8px] font-mono tracking-widest', isConnected ? 'text-terminal-buy' : 'text-terminal-sell')}>
          {isConnected ? 'WS CONNECTED — LIVE STREAM' : 'WS OFFLINE — POLLING FALLBACK'}
        </span>
      </div>

      {/* SHAP feature drivers */}
      {topShap.length > 0 && (
        <div className="border border-terminal-rule">
          <div className="flex items-center justify-between px-3 py-1.5 bg-terminal-panel border-b border-terminal-rule">
            <span className="text-[9px] font-mono font-bold text-terminal-label tracking-widest">SHAP KEY DRIVERS</span>
            <span className="text-[8px] font-mono text-terminal-label">TOP {topShap.length}</span>
          </div>
          <div className="divide-y divide-terminal-rule">
            {topShap.map((s, i) => {
              const barWidth = Math.min((Math.abs(s.contribution) / maxAbs) * 100, 100);
              const pos = s.contribution > 0;
              return (
                <div key={i} className="px-3 py-2">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-[9px] font-mono text-terminal-label truncate max-w-[130px]" title={s.feature}>
                      {label(s.feature)}
                    </span>
                    <span className={cn('text-[9px] font-mono font-bold tabular-nums', pos ? 'text-terminal-buy' : 'text-terminal-sell')}>
                      {pos ? '+' : ''}{s.contribution.toFixed(3)}
                    </span>
                  </div>
                  {/* Diverging bar */}
                  <div className="relative h-1 bg-terminal-panel flex">
                    <div className="w-1/2 flex justify-end">
                      {!pos && (
                        <div className="h-full bg-terminal-sell" style={{ width: `${barWidth}%` }} />
                      )}
                    </div>
                    <div className="w-px bg-terminal-label/30" />
                    <div className="w-1/2">
                      {pos && (
                        <div className="h-full bg-terminal-buy" style={{ width: `${barWidth}%` }} />
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Timestamp */}
      <div className="flex items-center gap-2 px-1">
        <span className="text-[8px] font-mono text-terminal-label tracking-widest">LAST UPDATE</span>
        <span className="text-[8px] font-mono text-terminal-value">
          {new Date(current.timestamp).toLocaleTimeString('en-US', { hour12: false })}
        </span>
      </div>
    </div>
  );
}
