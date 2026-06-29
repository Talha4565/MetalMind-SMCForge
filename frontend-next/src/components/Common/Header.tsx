'use client';

import { useRouter } from 'next/navigation';
import { Bell, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useSession } from 'next-auth/react';
import { useLogout } from '@/lib/hooks/useAuth';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import Link from 'next/link';
import { useEffect, useState } from 'react';

// Live clock
function TerminalClock() {
  const [time, setTime] = useState('');
  const [date, setDate] = useState('');

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false }));
      setDate(now.toLocaleDateString('en-US', { month: 'short', day: '2-digit', year: 'numeric' }).toUpperCase());
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="flex items-center gap-3 border-r border-terminal-rule pr-4">
      <div className="text-right">
        <p className="text-[13px] font-mono font-bold text-terminal-value tabular-nums leading-none">{time}</p>
        <p className="text-[9px] font-mono text-terminal-label tracking-widest mt-0.5">{date}</p>
      </div>
    </div>
  );
}

// Market status chip
function MarketStatus() {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const check = () => {
      const now = new Date();
      const h = now.getUTCHours();
      const m = now.getUTCMinutes();
      const mins = h * 60 + m;
      const day = now.getUTCDay();
      // NYSE: 14:30–21:00 UTC Mon–Fri
      setIsOpen(day >= 1 && day <= 5 && mins >= 870 && mins < 1260);
    };
    check();
    const id = setInterval(check, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 border ${isOpen ? 'border-terminal-buy/30 bg-terminal-buy/5' : 'border-terminal-sell/30 bg-terminal-sell/5'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${isOpen ? 'bg-terminal-buy animate-pulse' : 'bg-terminal-sell'}`} />
      <span className={`text-[9px] font-mono font-bold tracking-widest ${isOpen ? 'text-terminal-buy' : 'text-terminal-sell'}`}>
        {isOpen ? 'MARKET OPEN' : 'MARKET CLOSED'}
      </span>
    </div>
  );
}

export default function Header() {
  const { data: session } = useSession();
  const logout = useLogout();
  const router = useRouter();

  const isAuthenticated = !!session?.user?.email;
  const userHandle = session?.user?.email?.split('@')[0]?.toUpperCase() ?? 'GUEST';
  const userInitials = userHandle.slice(0, 2);

  return (
    <header className="h-10 border-b border-terminal-rule bg-sidebar flex items-center justify-between px-4 sticky top-0 z-40 shrink-0">
      {/* Left — breadcrumb + market status */}
      <div className="flex items-center gap-4">
        <MarketStatus />

        <div className="hidden md:flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-mono text-terminal-label tracking-widest">MODEL</span>
            <span className="text-[9px] font-mono font-bold text-terminal-data tracking-widest">XGBOOST</span>
          </div>
          <span className="text-terminal-rule text-[10px]">|</span>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-mono text-terminal-label tracking-widest">FEATURES</span>
            <span className="text-[9px] font-mono font-bold text-terminal-value tracking-widest">89</span>
          </div>
          <span className="text-terminal-rule text-[10px]">|</span>
          <div className="flex items-center gap-1.5">
            <span className="text-[9px] font-mono text-terminal-label tracking-widest">ASSETS</span>
            <span className="text-[9px] font-mono font-bold text-terminal-hold tracking-widest">XAU · XAG</span>
          </div>
        </div>
      </div>

      {/* Right — clock + user */}
      <div className="flex items-center gap-3">
        <TerminalClock />

        <button className="relative p-1 text-terminal-label hover:text-terminal-value transition-colors">
          <Bell className="w-3.5 h-3.5" />
          <span className="absolute top-0.5 right-0.5 w-1 h-1 bg-terminal-buy rounded-full" />
        </button>

        <div className="w-px h-4 bg-terminal-rule" />

        {isAuthenticated ? (
          <DropdownMenu>
            <DropdownMenuTrigger className="flex items-center gap-1.5 px-2 py-1 hover:bg-terminal-rule/50 transition-colors group outline-none">
              <div className="w-5 h-5 bg-terminal-hold flex items-center justify-center">
                <span className="text-black text-[8px] font-black font-mono">{userInitials}</span>
              </div>
              <span className="text-[9px] font-mono font-bold text-terminal-label group-hover:text-terminal-value tracking-widest hidden sm:block">
                {userHandle.slice(0, 12)}
              </span>
              <ChevronDown className="w-3 h-3 text-terminal-label" />
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align="end"
              className="w-44 bg-sidebar border border-terminal-rule rounded-none shadow-xl shadow-black/50 p-0"
            >
              <DropdownMenuGroup className="py-1">
                <DropdownMenuLabel className="px-3 py-2 border-b border-terminal-rule">
                  <p className="text-[9px] font-mono text-terminal-label tracking-widest">SIGNED IN AS</p>
                  <p className="text-[10px] font-mono font-bold text-terminal-value truncate mt-0.5">{session?.user?.email}</p>
                </DropdownMenuLabel>
                <DropdownMenuItem
                  onClick={() => router.push('/dashboard/profile')}
                  className="px-3 py-2 text-[10px] font-mono text-terminal-label hover:text-terminal-value hover:bg-terminal-rule cursor-pointer rounded-none"
                >
                  <User className="w-3 h-3 mr-2" />
                  PROFILE
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => router.push('/dashboard/risk')}
                  className="px-3 py-2 text-[10px] font-mono text-terminal-label hover:text-terminal-value hover:bg-terminal-rule cursor-pointer rounded-none"
                >
                  <Settings className="w-3 h-3 mr-2" />
                  RISK SETTINGS
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator className="bg-terminal-rule m-0" />
              <DropdownMenuItem
                onClick={logout}
                className="px-3 py-2 text-[10px] font-mono text-terminal-sell hover:bg-terminal-sell/10 cursor-pointer rounded-none"
              >
                <LogOut className="w-3 h-3 mr-2" />
                SIGN OUT
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
          <Link
            href="/auth/login"
            className="text-[9px] font-mono font-bold text-terminal-label hover:text-terminal-hold tracking-widest transition-colors px-2 py-1"
          >
            SIGN IN
          </Link>
        )}
      </div>
    </header>
  );
}
