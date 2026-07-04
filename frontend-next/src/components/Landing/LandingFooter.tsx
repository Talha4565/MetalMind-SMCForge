import Link from 'next/link';
import { Zap } from 'lucide-react';

export default function LandingFooter() {
  return (
    <footer className="border-t border-border/30 py-8 px-6">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-emerald-600 flex items-center justify-center">
            <Zap className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-bold tracking-tight">METALMIND SMCFORGE</span>
        </div>
        <div className="flex items-center gap-6">
          <Link href="/auth/login" className="text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Sign in</Link>
          <Link href="/dashboard" className="text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Dashboard</Link>
          <a href="https://github.com/Talha4565/MetalMind-SMCForge" className="text-[10px] uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Source</a>
        </div>
        <p className="text-[9px] text-muted-foreground/50">Not financial advice. For educational purposes only.</p>
      </div>
    </footer>
  );
}
