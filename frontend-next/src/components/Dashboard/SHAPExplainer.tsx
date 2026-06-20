'use client';

import { PredictionItem } from '@/lib/api-types';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

const SHAP_LABELS: Record<string, string> = {
  'htf_1h_dist_low': 'Distance from recent low',
  'htf_1h_dist_high': 'Distance from recent high',
  'htf_1h_momentum': '1-hour momentum',
  'htf_1h_atr': '1-hour volatility',
  'premium_discount_position': 'Premium/discount zone',
  'distance_from_equilibrium': 'Distance from fair value',
  'VWAPd_4': 'Short-term price deviation',
  'VWAPd_16': 'Medium-term price deviation',
  'VWAPd_96': 'Long-term price deviation',
  'CVD_4': 'Short-term order flow',
  'CVD_16': 'Medium-term order flow',
  'CVD_96': 'Long-term order flow',
  'session_ny': 'New York session',
  'session_london': 'London session',
  'session_asia': 'Asia session',
  'session_overlap': 'Session overlap',
  'Std_4': 'Short-term variability',
  'Std_16': 'Medium-term variability',
  'Std_96': 'Long-term variability',
  'Ret_4': 'Short-term return',
  'Ret_16': 'Medium-term return',
  'Ret_96': 'Long-term return',
  'Imbal_4': 'Short-term imbalance',
  'Imbal_16': 'Medium-term imbalance',
  'Imbal_96': 'Long-term imbalance',
  'Wick_4': 'Short-term wick ratio',
  'Wick_16': 'Medium-term wick ratio',
  'Wick_96': 'Long-term wick ratio',
  'close': 'Current price',
  'high': 'Session high',
  'low': 'Session low',
  'volume': 'Trading volume',
};

function friendlyName(raw: string): string {
  return SHAP_LABELS[raw] || raw.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

interface SHAPExplainerProps {
  prediction: PredictionItem;
  className?: string;
}

export default function SHAPExplainer({ prediction, className }: SHAPExplainerProps) {
  const rawShap = prediction.shap_values;
  const shapArray = Array.isArray(rawShap) ? rawShap : rawShap ? [rawShap] : [];

  const sortedShapValues = [...shapArray]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 8);

  const maxAbsContribution = Math.max(
    ...sortedShapValues.map(shap => Math.abs(shap.contribution)),
    0.001
  );

  return (
    <Card className={cn("bg-card border-border", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-blue-400" />
          <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">
            Feature Importance Analysis
          </p>
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          SHAP values showing how each feature contributes to the {prediction.asset.toUpperCase()} prediction
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {sortedShapValues.length > 0 ? (
          <div className="space-y-3">
            {sortedShapValues.map((shap, index) => {
              const isPositive = shap.contribution > 0;
              const normalizedWidth = Math.min((Math.abs(shap.contribution) / maxAbsContribution) * 50, 50);

              return (
                <div key={shap.feature} className="space-y-1">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-muted-foreground font-medium truncate mr-2" title={shap.feature}>
                      {friendlyName(shap.feature)}
                    </span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge
                        variant="outline"
                        className={cn(
                          "rounded-full text-xs px-2 py-0.5",
                          isPositive
                            ? "border-green-500/50 text-green-400 bg-green-500/10"
                            : "border-red-500/50 text-red-400 bg-red-500/10"
                        )}
                      >
                        {isPositive ? '+' : ''}{shap.contribution.toFixed(3)}
                      </Badge>
                      {index === 0 && (
                        <Badge className="rounded-full bg-blue-600 text-white text-xs px-2 py-0.5">
                          Primary
                        </Badge>
                      )}
                    </div>
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
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <BarChart3 className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-muted-foreground text-sm">
              No SHAP explainability data available for this prediction
            </p>
            <p className="text-muted-foreground text-xs mt-1">
              SHAP values help explain how the model makes decisions
            </p>
          </div>
        )}

        {sortedShapValues.length > 0 && (
          <div className="pt-4 border-t border-border">
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Top Contributor</p>
                <p className="text-sm font-bold text-card-foreground mt-1">
                  {friendlyName(sortedShapValues[0]?.feature || '') || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.15em] text-muted-foreground">Impact Range</p>
                <p className="text-sm font-bold text-card-foreground mt-1">
                  {Math.min(...sortedShapValues.map(s => s.contribution)).toFixed(2)} to {Math.max(...sortedShapValues.map(s => s.contribution)).toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
