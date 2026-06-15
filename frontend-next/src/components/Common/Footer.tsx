import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-slate-800/40 bg-[#0a0f1a]">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-emerald-600/80 flex items-center justify-center">
              <span className="text-white text-[8px] font-black">M</span>
            </div>
            <span className="text-xs text-slate-500">
              MetalMind SMCForge
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs text-slate-600">
            <Link href="/dashboard" className="hover:text-slate-400 transition-colors">Dashboard</Link>
            <Link href="/backtest" className="hover:text-slate-400 transition-colors">Backtest</Link>
            <Link href="/dashboard/profile" className="hover:text-slate-400 transition-colors">Profile</Link>
            <a href="https://github.com/Talha/ml-signals" className="hover:text-slate-400 transition-colors">GitHub</a>
          </div>

          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-slate-600">XGBoost live</span>
          </div>
        </div>
      </div>
    </footer>
  );
}