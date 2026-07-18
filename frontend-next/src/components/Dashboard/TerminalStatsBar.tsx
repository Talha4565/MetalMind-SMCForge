'use client';

import { PredictionItem, AssetType } from '@/lib/api-types';
import { cn } from '@/lib/utils';
import { TerminalStatRow, TerminalSectionHeader } from '@/components/Common/TerminalCard';

interface Props {
  activeAsset: AssetType;
  livePrice: number | null;
  prediction?: PredictionItem;
  signalText: string;
  confidence: string | null;
  isLoading?: boolean;
}

function SkeletonStatRow() {
  return (
    <div className="flex items-center justify-between py-2 border-b border-terminal-rule last:border-0">
      <div className="h-3 w-16 bg-terminal-rule animate-pulse" />
      <div className="h-3 w-20 bg-terminal-rule animate-pulse" />
    </div>
  );
}

function SkeletonSection({ labelWidth = 16, rows = 3 }: { labelWidth?: number; rows?: number }) {
  return (
    <>
      <div className="pt-3 pb-1">
        <div className="h-3 bg-terminal-rule animate-pulse" style={{ width: `${labelWidth * 4}px` }} />
      </div>
      {Array.from({ length: rows }).map((_, i) => (
        <SkeletonStatRow key={i} />
      ))}
    </>
  );
}

export default function TerminalStatsBar({
  activeAsset,
  livePrice,
  prediction,
  signalText,
  confidence,
  isLoading,
}: Props) {
  if (isLoading) {
    return (
      <div className="space-y-0">
        <SkeletonSection labelWidth={20} rows={4} />
        <SkeletonSection rows={2} />
        <SkeletonSection rows={3} />
        <SkeletonSection rows={3} />
        <SkeletonSection rows={2} />
        <SkeletonSection rows={2} />
      </div>
    );
  }
  const signalClass =
    signalText === 'BUY' ? 'text-terminal-buy' :
    signalText === 'SELL' ? 'text-terminal-sell' : 'text-terminal-hold';

  const assetLabel = activeAsset === 'gold' ? 'XAU/USD' : 'XAG/USD';
  const assetFull  = activeAsset === 'gold' ? 'Gold Spot' : 'Silver Spot';

  // Derived from prediction shap if available
  const shapArr = Array.isArray(prediction?.shap_values) ? prediction.shap_values : [];
  const shapCount = shapArr.length;
  const topDriverPos = shapArr.filter(s => s.contribution > 0)
    .sort((a, b) => b.contribution - a.contribution)[0];
  const topDriverNeg = shapArr.filter(s => s.contribution < 0)
    .sort((a, b) => a.contribution - b.contribution)[0];

  return (
    <div className="space-y-0">
      {/* Asset identity */}
      <TerminalSectionHeader label="Instrument" />
      <TerminalStatRow label="SYMBOL" value={assetLabel} />
      <TerminalStatRow label="NAME" value={assetFull} />

      {/* Pricing */}
      <TerminalSectionHeader label="Pricing" />
      <TerminalStatRow
        label="LIVE PRICE"
        value={livePrice != null ? `$${livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
        valueClass="text-terminal-value"
      />
      <TerminalStatRow
        label="MODEL PRICE"
        value={prediction?.price ? `$${prediction.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
      />

      {/* Signal */}
      <TerminalSectionHeader label="AI Signal" />
      <TerminalStatRow label="DIRECTION" value={signalText} valueClass={signalClass} />
      <TerminalStatRow label="CONFIDENCE" value={confidence ? `${confidence}%` : '—'} valueClass={signalClass} />
      <TerminalStatRow
        label="PROBABILITY"
        value={prediction?.probability != null ? `${(prediction.probability * 100).toFixed(1)}%` : '—'}
        valueClass="text-terminal-data"
      />

      {/* Model */}
      <TerminalSectionHeader label="Model" />
      <TerminalStatRow label="ALGORITHM" value="XGBoost" />
      <TerminalStatRow label="FEATURES" value="89" />
      <TerminalStatRow label="SHAP VALUES" value={shapCount > 0 ? `${shapCount}` : '—'} />
      <TerminalStatRow label="FRAMEWORK" value="SMCForge v1" />

      {/* Drivers */}
      {(topDriverPos || topDriverNeg) && (
        <>
          <TerminalSectionHeader label="Key Drivers" />
          {topDriverPos && (
            <TerminalStatRow
              label="TOP BULLISH"
              value={topDriverPos.feature.replace(/_/g, ' ').slice(0, 16).toUpperCase()}
              valueClass="text-terminal-buy"
            />
          )}
          {topDriverNeg && (
            <TerminalStatRow
              label="TOP BEARISH"
              value={topDriverNeg.feature.replace(/_/g, ' ').slice(0, 16).toUpperCase()}
              valueClass="text-terminal-sell"
            />
          )}
        </>
      )}

      {/* Timestamp */}
      <TerminalSectionHeader label="Timestamp" />
      <TerminalStatRow
        label="SIGNAL AT"
        value={prediction?.timestamp
          ? new Date(prediction.timestamp).toLocaleTimeString('en-US', { hour12: false })
          : '—'}
      />
      <TerminalStatRow
        label="DATE"
        value={prediction?.timestamp
          ? new Date(prediction.timestamp).toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).toUpperCase()
          : '—'}
      />
    </div>
  );
}
