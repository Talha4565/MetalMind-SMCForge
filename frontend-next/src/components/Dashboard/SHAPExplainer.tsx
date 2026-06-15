'use client';

import { PredictionItem } from '@/lib/api-types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { BarChart3 } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SHAPExplainerProps {
  prediction: PredictionItem;
  className?: string;
}

/**
 * SHAP Explainer Component
 * Visualizes feature contributions to the ML model's prediction
 * Uses expert patterns for data visualization and accessibility
 */
export default function SHAPExplainer({ prediction, className }: SHAPExplainerProps) {
  // Normalize shap_values — handle array, single object, or missing
  const rawShap = prediction.shap_values;
  const shapArray = Array.isArray(rawShap) ? rawShap : rawShap ? [rawShap] : [];

  const sortedShapValues = [...shapArray]
    .sort((a, b) => Math.abs(b.contribution) - Math.abs(a.contribution))
    .slice(0, 8);

  const maxAbsContribution = Math.max(
    ...sortedShapValues.map(shap => Math.abs(shap.contribution)),
    0.001 // Prevent division by zero
  );

  return (
    <Card className={cn("bg-slate-900 border-slate-800", className)}>
      <CardHeader className="pb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          <CardTitle className="text-lg font-bold text-slate-200">
            Feature Importance Analysis
          </CardTitle>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          SHAP values showing how each feature contributes to the {prediction.asset.toUpperCase()} prediction
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {sortedShapValues.length > 0 ? (
          <div className="space-y-3">
            {sortedShapValues.map((shap, index) => {
              const isPositive = shap.contribution > 0;
              const contributionPercent = Math.abs(shap.contribution) / maxAbsContribution;
              const barWidth = Math.max(contributionPercent * 100, 2); // Minimum 2% width

              return (
                <div key={shap.feature} className="space-y-2">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-300 font-medium truncate mr-2">
                      {shap.feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs px-2 py-0.5",
                          isPositive
                            ? "border-green-500/50 text-green-400 bg-green-500/10"
                            : "border-red-500/50 text-red-400 bg-red-500/10"
                        )}
                      >
                        {isPositive ? '+' : ''}{shap.contribution.toFixed(3)}
                      </Badge>
                      {index === 0 && (
                        <Badge className="bg-blue-600 text-white text-xs px-2 py-0.5">
                          Primary
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Contribution Bar */}
                  <div className="relative">
                    <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          isPositive ? "bg-green-500" : "bg-red-500"
                        )}
                        style={{
                          width: `${barWidth}%`,
                          marginLeft: isPositive ? 'auto' : '0'
                        }}
                      />
                    </div>
                    {/* Zero line indicator */}
                    <div className="absolute top-0 left-1/2 w-px h-full bg-slate-600 transform -translate-x-px" />
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <BarChart3 className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-500 text-sm">
              No SHAP explainability data available for this prediction
            </p>
            <p className="text-slate-600 text-xs mt-1">
              SHAP values help explain how the model makes decisions
            </p>
          </div>
        )}

        {/* Summary Stats */}
        {sortedShapValues.length > 0 && (
          <div className="pt-4 border-t border-slate-800">
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-widest">Top Contributor</p>
                <p className="text-sm font-bold text-slate-200 mt-1">
                  {sortedShapValues[0]?.feature.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-widest">Impact Range</p>
                <p className="text-sm font-bold text-slate-200 mt-1">
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