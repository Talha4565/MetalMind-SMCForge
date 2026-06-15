'use client';

import React from 'react';
import Header from './Header';
import Sidebar from '@/components/Navigation/Sidebar';
import Footer from './Footer';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * Main layout for authenticated pages.
 * Includes Sidebar, Header, and Footer with responsive design.
 * Matches the Phase 3 plan specifications.
 */
export default function DashboardLayout({ children, className }: DashboardLayoutProps) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <Header />
        <div className={cn("flex-1 overflow-auto", className)}>
          <div className="max-w-7xl mx-auto p-6">
            {children}
          </div>
        </div>
        <div className="flex-shrink-0">
          <Footer />
        </div>
      </main>
    </div>
  );
}
