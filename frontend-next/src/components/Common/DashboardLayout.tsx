'use client';

import React from 'react';
import Header from './Header';
import Sidebar from '@/components/Navigation/Sidebar';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  className?: string;
  /** When true, content fills the full remaining height (no scroll padding) */
  fullHeight?: boolean;
}

/**
 * Bloomberg Terminal layout.
 * Sidebar (fixed 192px) + main column (Header sticky top + scrollable content).
 * No footer — terminal UIs use all available screen space.
 */
export default function DashboardLayout({ children, className, fullHeight }: DashboardLayoutProps) {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      <Sidebar />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <Header />

        <div
          className={cn(
            'flex-1 flex flex-col min-h-0',
            fullHeight ? 'p-0 overflow-hidden' : 'p-4 overflow-y-auto overflow-x-hidden',
            className
          )}
        >
          {children}
        </div>
      </div>
    </div>
  );
}
