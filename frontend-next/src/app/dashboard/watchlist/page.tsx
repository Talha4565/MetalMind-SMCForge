'use client';

import DashboardLayout from '@/components/Common/DashboardLayout';
import TerminalCard from '@/components/Common/TerminalCard';
import WatchlistTable from '@/components/Watchlist/WatchlistTable';

export default function WatchlistPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6 p-4">
        <div>
          <h1 className="text-2xl font-black tracking-tight text-terminal-value font-mono">WATCHLIST</h1>
          <p className="text-terminal-label text-xs mt-1 font-mono tracking-wider">
            Manage your asset watchlist · preview signals · live price updates
          </p>
        </div>

        <TerminalCard title="WATCHLIST MANAGEMENT" code="WCH">
          <WatchlistTable />
        </TerminalCard>
      </div>
    </DashboardLayout>
  );
}
