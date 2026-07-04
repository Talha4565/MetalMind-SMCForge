'use client';

import Link from 'next/link';
import { Zap } from 'lucide-react';

export default function LandingNavbar() {
  return (
    <nav className="fixed top-0 w-full z-50 border-b border-border/30 bg-background/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center">
            <Zap className="w-4 h-4 text-white" />
          </div>
          <span className="text-sm font-black tracking-tight">METALMIND</span>
        </Link>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-xs font-medium uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Features</a>
          <a href="#backtest" className="text-xs font-medium uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Backtest</a>
          <a href="#about" className="text-xs font-medium uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">About</a>
          <a href="#contact" className="text-xs font-medium uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">Contact</a>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/auth/login" className="text-xs font-bold uppercase tracking-widest text-muted-foreground hover:text-foreground transition-colors">
            Sign in
          </Link>
          <Link href="/auth/register" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold uppercase tracking-widest rounded-lg transition-colors">
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  );
}
