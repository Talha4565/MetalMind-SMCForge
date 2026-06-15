'use client';

import { useRouter } from 'next/navigation';
import { Bell, User, Settings, LogOut } from 'lucide-react';
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
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import Link from 'next/link';
import ThemeToggle from './ThemeToggle';

export default function Header() {
  const { data: session } = useSession();
  const logout = useLogout();
  const router = useRouter();

  const isAuthenticated = !!session?.user?.email;
  const userInitials = session?.user?.email
    ?.split('@')[0]
    .split('')
    .slice(0, 2)
    .map(c => c.toUpperCase())
    .join('') || 'US';

  return (
    <header className="h-14 border-b border-border bg-background/95 backdrop-blur-xl flex items-center justify-between px-6 sticky top-0 z-40">
      {/* Left — brand */}
      <Link href="/dashboard" className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-md bg-emerald-600 flex items-center justify-center">
          <span className="text-white text-xs font-black">M</span>
        </div>
        <span className="text-sm font-bold text-foreground hidden sm:block">MetalMind</span>
      </Link>

      {/* Right */}
      <div className="flex items-center gap-3">
        <button className="relative text-muted-foreground hover:text-foreground transition-colors p-1.5">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-emerald-500 rounded-full" />
        </button>

        <ThemeToggle />

        <div className="w-px h-5 bg-border" />

        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <span className="flex cursor-pointer items-center gap-2 hover:opacity-80 transition-opacity">
                  <div className="text-right hidden sm:block">
                    <p className="text-xs font-medium text-slate-300">{session?.user?.email?.split('@')[0]}</p>
                  </div>
                  <Avatar className="h-8 w-8 border border-slate-700/50">
                    <AvatarFallback className="bg-muted text-muted-foreground text-[10px] font-bold">
                      {userInitials}
                    </AvatarFallback>
                  </Avatar>
                </span>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48 bg-popover border border-border">
                <DropdownMenuGroup>
                  <DropdownMenuLabel>
                    <p className="text-xs text-slate-400">{session?.user?.email}</p>
                  </DropdownMenuLabel>
                </DropdownMenuGroup>
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem
                  onClick={() => router.push('/dashboard/profile')}
                  className="text-foreground hover:bg-accent cursor-pointer text-xs"
                >
                  <User className="w-3.5 h-3.5 mr-2" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => router.push('/dashboard/risk')}
                  className="text-foreground hover:bg-accent cursor-pointer text-xs"
                >
                  <Settings className="w-3.5 h-3.5 mr-2" />
                  Risk Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator className="bg-border" />
                <DropdownMenuItem onClick={logout} className="text-red-400 hover:bg-red-600/10 cursor-pointer text-xs">
                  <LogOut className="w-3.5 h-3.5 mr-2" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Link href="/auth/login" className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
