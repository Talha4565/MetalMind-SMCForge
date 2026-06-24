'use client';

import { PredictionItem, AssetType } from '@/lib/api-types';
import { cn } from '@/lib/utils';

interface Props {
  activeAsset: AssetType;
  livePrice: number | null;
  prediction?: PredictionItem;
  signalText: string;
  confidence: string | null;
}

function StatRow({ label, value, valueClass }: { label: string; value: string; valueClass?: string }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-terminal-rule last:border-0">
      <span className="text-[9px] font-mono text-terminal-label tracking-widest">{label}</span>
      <span className={cn('text-[10px] font-mono font-bold tabular-nums text-terminal-value', valueClass)}>
        {value}
      </span>
    </div>
  );
}

function SectionHeader({ label }: { label: string }) {
  return (
    <div className="pt-3 pb-1">
      <p className="text-[8px] font-mono font-black text-terminal-label tracking-[0.3em] uppercase border-b border-terminal-rule pb-1">
        {label}
      </p>
    </div>
  );
}

export default function TerminalStatsBar({
  activeAsset,
  livePrice,
  prediction,
  signalText,
  confidence,
}: Props) {
  const signalClass =
    signalText === 'BUY' ? 'text-terminal-buy' :
    signalText === 'SELL' ? 'text-terminal-sell' : 'text-terminal-hold';

  const assetLabel = activeAsset === 'gold' ? 'XAU/USD' : 'XAG/USD';
  const assetFull  = activeAsset === 'gold' ? 'Gold Futures' : 'Silver Futures';

  // Derived from prediction shap if available
  const shapCount = prediction?.shap_values?.length ?? 0;
  const topDriverPos = prediction?.shap_values
    ?.filter(s => s.contribution > 0)
    .sort((a, b) => b.contribution - a.contribution)[0];
  const topDriverNeg = prediction?.shap_values
    ?.filter(s => s.contribution < 0)
    .sort((a, b) => a.contribution - b.contribution)[0];

  return (
    <div className="space-y-0">
      {/* Asset identity */}
      <SectionHeader label="Instrument" />
      <StatRow label="SYMBOL" value={assetLabel} />
      <StatRow label="NAME" value={assetFull} />
      <StatRow label="CLASS" value="Precious Metals" />
      <StatRow label="QUOTE" value="USD" />

      {/* Pricing */}
      <SectionHeader label="Pricing" />
      <StatRow
        label="LIVE PRICE"
        value={livePrice != null ? `$${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
        valueClass="text-terminal-value"
      />
      <StatRow
        label="MODEL PRICE"
        value={prediction?.price ? `$${prediction.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
      />

      {/* Signal */}
      <SectionHeader label="AI Signal" />
      <StatRow label="DIRECTION" value={signalText} valueClass={signalClass} />
      <StatRow label="CONFIDENCE" value={confidence ? `${confidence}%` : '—'} valueClass={signalClass} />
      <StatRow
        label="PROBABILITY"
        value={prediction?.probability != null ? `${(prediction.probability * 100).toFixed(1)}%` : '—'}
        valueClass="text-terminal-data"
      />

      {/* Model */}
      <SectionHeader label="Model" />
      <StatRow label="ALGORITHM" value="XGBoost" />
      <StatRow label="FEATURES" value="89" />
      <StatRow label="SHAP VALUES" value={shapCount > 0 ? `${shapCount}` : '—'} />
      <StatRow label="FRAMEWORK" value="SMCForge v1" />

      {/* Drivers */}
      {(topDriverPos || topDriverNeg) && (
        <>
          <SectionHeader label="Key Drivers" />
          {topDriverPos && (
            <StatRow
              label="TOP BULLISH"
              value={topDriverPos.feature.replace(/_/g, ' ').slice(0, 16).toUpperCase()}
              valueClass="text-terminal-buy"
            />
          )}
          {topDriverNeg && (
            <StatRow
              label="TOP BEARISH"
              value={topDriverNeg.feature.replace(/_/g, ' ').slice(0, 16).toUpperCase()}
              valueClass="text-terminal-sell"
            />
          )}
        </>
      )}

      {/* Timestamp */}
      <SectionHeader label="Timestamp" />
      <StatRow
        label="SIGNAL AT"
        value={prediction?.timestamp
          ? new Date(prediction.timestamp).toLocaleTimeString('en-US', { hour12: false })
          : '—'}
      />
      <StatRow
        label="DATE"
        value={prediction?.timestamp
          ? new Date(prediction.timestamp).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).toUpperCase()
          : '—'}
      />
    </div>
  );
}
