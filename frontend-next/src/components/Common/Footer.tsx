import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded bg-primary flex items-center justify-center">
              <span className="text-primary-foreground text-[8px] font-black">M</span>
            </div>
            <span className="text-xs text-muted-foreground">
              MetalMind SMCForge
            </span>
          </div>

          <div className="flex items-center gap-6 text-xs text-muted-foreground">
            <Link href="/dashboard" className="hover:text-foreground transition-colors">Dashboard</Link>
            <Link href="/backtest" className="hover:text-foreground transition-colors">Backtest</Link>
            <Link href="/dashboard/profile" className="hover:text-foreground transition-colors">Profile</Link>
            <a href="https://github.com/Talha4565/MetalMind-SMCForge" className="hover:text-foreground transition-colors">GitHub</a>
          </div>

          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-primary" />
            <span className="text-[10px] text-muted-foreground">XGBoost live</span>
          </div>
        </div>
      </div>
    </footer>
  );
}