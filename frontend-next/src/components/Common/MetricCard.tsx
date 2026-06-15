'use client';

import { ReactNode } from 'react';
import { ArrowUp, ArrowDown } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  change?: number;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  onClick?: () => void;
  className?: string;
}

export function MetricCard({
  label,
  value,
  change,
  icon,
  trend = 'neutral',
  onClick,
  className,
}: MetricCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        'group relative overflow-hidden rounded-xl border border-border/50 bg-gradient-to-br from-card/50 via-card/30 to-background/50 p-6 backdrop-blur-xl transition-all duration-300 cursor-pointer hover:border-blue-600/30 hover:shadow-lg hover:shadow-blue-600/10',
        className
      )}
    >
      {/* Gradient Background */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
        <div className="absolute top-0 right-0 w-32 h-32 bg-blue-600/10 blur-3xl" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400 mb-2">{label}</p>
          <div className="flex items-end gap-3">
            <h3 className="text-3xl font-bold text-white">{value}</h3>
            {change !== undefined && (
              <div
                className={cn(
                  'flex items-center gap-1 px-2 py-1 rounded-lg text-sm font-semibold mb-1',
                  trend === 'up'
                    ? 'bg-green-600/20 text-green-400'
                    : trend === 'down'
                      ? 'bg-red-600/20 text-red-400'
                      : 'bg-slate-700/20 text-slate-400'
                )}
              >
                {trend === 'up' && <ArrowUp className="w-3 h-3" />}
                {trend === 'down' && <ArrowDown className="w-3 h-3" />}
                {trend === 'up' ? '+' : ''}{change}%
              </div>
            )}
          </div>
        </div>
        {icon && (
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-blue-600/20 to-purple-600/20 flex items-center justify-center text-blue-400 group-hover:text-blue-300 transition-colors">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
