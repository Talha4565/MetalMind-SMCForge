'use client';

import { PredictionItem } from '@/lib/api-types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Info, Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';
import { useWebSocket } from '@/lib/hooks/useWebSocket';
import { friendlyName } from '@/lib/shap-labels';

interface SignalCardProps {
  prediction: PredictionItem;
  isLoading?: boolean;
  livePrice?: number | null;
}

export default function SignalCard({ prediction, isLoading, livePrice }: SignalCardProps) {
  const { data: wsData, isConnected, emit } = useWebSocket<PredictionItem>('predictions');

  useEffect(() => {
    if (isConnected) {
      emit('subscribe_predictions', { asset: prediction.asset });
    }
  }, [isConnected, prediction.asset, emit]);

  const currentPrediction = (wsData && wsData.asset === prediction.asset) ? wsData : prediction;

  if (isLoading) {
    return (
      <Card className="bg-card border-border animate-pulse">
        <div className="h-48" />
      </Card>
    );
  }

  const signalValue = typeof currentPrediction.signal === 'string'
    ? currentPrediction.signal.toUpperCase()
    : currentPrediction.signal;

  const isBuy = signalValue === 'BUY' || (typeof signalValue === 'number' && signalValue === 1);
  const isSell = signalValue === 'SELL' || (typeof signalValue === 'number' && signalValue === -1);

  const Icon = isBuy ? TrendingUp : isSell ? TrendingDown : Minus;
  const colorClass = isBuy
    ? "text-green-500 bg-green-500/10 border-green-500/20"
    : isSell
      ? "text-red-500 bg-red-500/10 border-red-500/20"
      : "text-slate-400 bg-slate-400/10 border-slate-400/20";

  const shapValues = currentPrediction.shap_values || [];
  const maxAbs = Math.max(...shapValues.map(s => Math.abs(s.contribution)), 0.001);

  return (
    <Card className={cn("bg-card border-border overflow-hidden group transition-all hover:border-border/80", {
      "border-l-4 border-l-green-500": isBuy,
      "border-l-4 border-l-red-500": isSell,
      "border-l-4 border-l-slate-500": !isBuy && !isSell,
    })}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className={cn("p-2 rounded-lg", colorClass)}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg uppercase tracking-wider text-card-foreground">
                {currentPrediction.asset}
              </h3>
              <p className="text-[10px] text-muted-foreground flex items-center gap-1">
                Latest Signal
                {isConnected && <Wifi className="w-3 h-3 text-green-500" />}
                {!isConnected && <WifiOff className="w-3 h-3 text-red-500" />}
              </p>
            </div>
          </div>
          <Badge className={cn("rounded-full px-3 py-1 text-xs font-bold", {
            "bg-green-600 hover:bg-green-700": isBuy,
            "bg-red-600 hover:bg-red-700": isSell,
            "bg-slate-600 hover:bg-slate-700": !isBuy && !isSell,
          })}>
            {isBuy ? 'BUY' : isSell ? 'SELL' : 'HOLD'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="flex justify-between items-end">
          <div>
            <p className="text-3xl font-black text-card-foreground">
              ${livePrice !== null && livePrice !== undefined
                ? livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : currentPrediction.price.toLocaleString()
              }
            </p>
            <p className="text-[10px] text-muted-foreground mt-1">
              {livePrice !== null && livePrice !== undefined ? 'Live price' : 'Last close'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Confidence</p>
            <p className={cn("text-xl font-bold", isBuy ? "text-green-400" : isSell ? "text-red-400" : "text-muted-foreground")}>
              {currentPrediction.confidence != null ? `${(currentPrediction.confidence * 100).toFixed(1)}%` : '—'}
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-border">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-4 h-4 text-blue-400" />
            <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Key Drivers (SHAP)</span>
          </div>
          <div className="space-y-3">
            {shapValues.length > 0 ? (
              shapValues.slice(0, 3).map((shap, i) => {
                const normalizedWidth = Math.min((Math.abs(shap.contribution) / maxAbs) * 50, 50);
                const isPositive = shap.contribution > 0;
                return (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted-foreground truncate mr-2" title={shap.feature}>{friendlyName(shap.feature)}</span>
                      <span className={cn("w-12 text-right font-mono text-[10px]", isPositive ? "text-green-400" : "text-red-400")}>
                        {isPositive ? '+' : ''}{shap.contribution.toFixed(2)}
                      </span>
                    </div>
                    <div className="relative h-2 bg-muted rounded-full overflow-hidden">
                      <div className="absolute inset-0 flex">
                        <div className="w-1/2 flex justify-end">
                          {!isPositive && (
                            <div
                              className="h-full bg-red-500 rounded-l-full"
                              style={{ width: `${normalizedWidth}%` }}
                            />
                          )}
                        </div>
                        <div className="w-px bg-slate-500" />
                        <div className="w-1/2">
                          {isPositive && (
                            <div
                              className="h-full bg-green-500 rounded-r-full"
                              style={{ width: `${normalizedWidth}%` }}
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <p className="text-[10px] text-muted-foreground italic">No explainability data available for this signal.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
