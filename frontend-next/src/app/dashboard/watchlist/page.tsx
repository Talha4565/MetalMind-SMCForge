'use client';

import DashboardLayout from '@/components/Common/DashboardLayout';
import WatchlistTable from '@/components/Watchlist/WatchlistTable';

export default function WatchlistPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="rounded-3xl border border-border bg-card p-6 shadow-lg shadow-black/20">
          <div className="max-w-4xl">
            <p className="text-sm uppercase tracking-[0.28em] text-slate-500">Dashboard</p>
            <h1 className="mt-2 text-3xl font-black text-card-foreground">Watchlist management</h1>
            <p className="mt-3 text-slate-400">
              Manage your asset watchlist, preview signal and price updates, and keep your trades organized with live analytics.
            </p>
          </div>
        </div>

        <WatchlistTable />
      </div>
    </DashboardLayout>
  );
}
