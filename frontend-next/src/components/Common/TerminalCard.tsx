'use client';

import React from 'react';
import { cn } from '@/lib/utils';

interface TerminalCardProps {
  children: React.ReactNode;
  /** Terminal-style header label (e.g. "SIGNAL ANALYSIS") */
  title?: string;
  /** 3-4 char code displayed in terminal badge (e.g. "SIG", "MKT") */
  code?: string;
  /** Optional right-aligned content in the header */
  right?: React.ReactNode;
  /** Additional class names */
  className?: string;
  /** When true, removes header even if title/code are provided */
  noHeader?: boolean;
  /** When true, removes inner padding */
  noPadding?: boolean;
}

/**
 * Terminal-styled card matching the Bloomberg aesthetic.
 * Sharp corners, terminal-rule borders, monospace headers with code badges.
 * Use this instead of shadcn <Card> on all dashboard sub-pages.
 */
export default function TerminalCard({
  children,
  title,
  code,
  right,
  className,
  noHeader = false,
  noPadding = false,
}: TerminalCardProps) {
  const hasHeader = !noHeader && (title || code || right);

  return (
    <div className={cn('border border-terminal-rule bg-terminal-panel', className)}>
      {hasHeader && (
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-terminal-rule bg-terminal-panel shrink-0">
          <div className="flex items-center gap-2">
            {code && (
              <span className="text-[8px] font-mono font-black text-terminal-hold bg-terminal-hold/10 px-1.5 py-0.5 tracking-widest">
                {code}
              </span>
            )}
            {title && (
              <span className="text-[9px] font-mono font-bold text-terminal-label tracking-widest">
                {title}
              </span>
            )}
          </div>
          {right && <div>{right}</div>}
        </div>
      )}
      <div className={noPadding ? '' : 'p-4'}>{children}</div>
    </div>
  );
}

/* ── Terminal-styled stat row (label + value) ── */

interface StatRowProps {
  label: string;
  value: string;
  valueClass?: string;
}

export function TerminalStatRow({ label, value, valueClass }: StatRowProps) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-terminal-rule last:border-0">
      <span className="text-[9px] font-mono text-terminal-label tracking-widest">{label}</span>
      <span className={cn('text-[10px] font-mono font-bold tabular-nums text-terminal-value', valueClass)}>
        {value}
      </span>
    </div>
  );
}

/* ── Terminal section header ── */

export function TerminalSectionHeader({ label }: { label: string }) {
  return (
    <div className="pt-3 pb-1">
      <p className="text-[8px] font-mono font-black text-terminal-label tracking-[0.3em] uppercase border-b border-terminal-rule pb-1">
        {label}
      </p>
    </div>
  );
}

/* ── Terminal-styled button (amber primary, sharp) ── */

interface TerminalButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md';
  isLoading?: boolean;
  children: React.ReactNode;
}

export function TerminalButton({
  variant = 'primary',
  size = 'md',
  isLoading,
  children,
  className,
  disabled,
  ...props
}: TerminalButtonProps) {
  return (
    <button
      className={cn(
        'font-mono font-bold tracking-widest transition-all inline-flex items-center justify-center gap-2',
        variant === 'primary' && 'bg-terminal-hold text-black hover:bg-terminal-hold/80',
        variant === 'secondary' && 'border border-terminal-rule text-terminal-label hover:text-terminal-value hover:border-terminal-label',
        variant === 'danger' && 'border border-terminal-sell/30 text-terminal-sell hover:bg-terminal-sell/10',
        size === 'sm' && 'px-3 py-1.5 text-[9px]',
        size === 'md' && 'px-5 py-2.5 text-[10px]',
        (disabled || isLoading) && 'opacity-50 cursor-not-allowed',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && (
        <span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />
      )}
      {children}
    </button>
  );
}
