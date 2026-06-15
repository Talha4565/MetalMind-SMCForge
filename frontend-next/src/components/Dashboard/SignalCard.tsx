'use client';

import { PredictionItem } from '@/lib/api-types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Minus, Info, Wifi, WifiOff } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect } from 'react';
import { useWebSocket } from '@/lib/hooks/useWebSocket';

interface SignalCardProps {
  prediction: PredictionItem;
  isLoading?: boolean;
  livePrice?: number | null;
}

export default function SignalCard({ prediction, isLoading, livePrice }: SignalCardProps) {
  // WebSocket integration for real-time signal updates
  const { data: wsData, isConnected, emit } = useWebSocket<PredictionItem>('predictions');

  // Subscribe to predictions when connected
  useEffect(() => {
    if (isConnected) {
      emit('subscribe_predictions', { asset: prediction.asset });
    }
  }, [isConnected, prediction.asset, emit]);

  // Use live data if available and matches the asset, otherwise fall back to props
  const currentPrediction = (wsData && wsData.asset === prediction.asset) ? wsData : prediction;

  if (isLoading) {
    return (
      <Card className="bg-slate-900 border-slate-800 animate-pulse">
        <div className="h-48" />
      </Card>
    );
  }

  // Handle both string and numeric signals from backend
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

  return (
    <Card className={cn("bg-slate-900 border-slate-800 overflow-hidden group transition-all hover:border-slate-700", {
      "border-l-4 border-l-green-500": isBuy,
      "border-l-4 border-l-red-500": isSell,
    })}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-2">
            <div className={cn("p-2 rounded-lg", colorClass)}>
              <Icon className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-lg uppercase tracking-wider text-slate-200">
                {currentPrediction.asset}
              </h3>
              <p className="text-xs text-slate-500 flex items-center gap-1">
                Latest Signal
                {isConnected && <Wifi className="w-3 h-3 text-green-500" />}
                {!isConnected && <WifiOff className="w-3 h-3 text-red-500" />}
              </p>
            </div>
          </div>
          <Badge className={cn("px-3 py-1 font-bold", {
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
            <p className="text-3xl font-black text-slate-100">
              ${livePrice !== null && livePrice !== undefined
                ? livePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                : currentPrediction.price.toLocaleString()
              }
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {livePrice !== null && livePrice !== undefined ? 'Live price' : 'Last close'}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-slate-400">Confidence</p>
            <p className={cn("text-xl font-bold", isBuy ? "text-green-400" : isSell ? "text-red-400" : "text-slate-400")}>
              {currentPrediction.confidence != null ? `${(currentPrediction.confidence * 100).toFixed(1)}%` : '—'}
            </p>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-4 h-4 text-blue-400" />
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-widest">Key Drivers (SHAP)</span>
          </div>
          <div className="space-y-2">
            {/* Safe access to shap_values */}
            {(currentPrediction.shap_values || []).length > 0 ? (
              currentPrediction.shap_values.slice(0, 3).map((shap, i) => (
                <div key={i} className="flex justify-between items-center text-xs">
                  <span className="text-slate-500 truncate mr-2">{shap.feature}</span>
                  <div className="flex items-center gap-2 min-w-[100px]">
                    <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className={cn("h-full rounded-full", shap.contribution > 0 ? "bg-green-500" : "bg-red-500")}
                        style={{ width: `${Math.min(Math.abs(shap.contribution) * 100, 100)}%` }}
                      />
                    </div>
                    <span className={cn("w-8 text-right font-mono", shap.contribution > 0 ? "text-green-400" : "text-red-400")}>
                      {shap.contribution > 0 ? '+' : ''}{shap.contribution.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-[10px] text-slate-600 italic">No explainability data available for this signal.</p>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
