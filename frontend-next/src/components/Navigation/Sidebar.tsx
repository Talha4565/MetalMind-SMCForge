'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Menu, Home, ShieldAlert, User, X, BarChart3, Activity } from 'lucide-react'
import { useSession } from 'next-auth/react'
import { cn } from '@/lib/utils'

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const { status } = useSession()
  const isAuthenticated = status === 'authenticated'
  const pathname = usePathname()

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: isAuthenticated ? '/backtest' : '/auth/login', label: 'Backtest', icon: BarChart3 },
    { href: '/dashboard/risk', label: 'Risk', icon: ShieldAlert },
    { href: isAuthenticated ? '/dashboard/pipeline' : '/auth/login', label: 'Pipeline', icon: Activity },
    { href: isAuthenticated ? '/dashboard/profile' : '/auth/login', label: 'Profile', icon: User },
  ]

  return (
    <>
      {/* Mobile toggle */}
      <div className="sm:hidden flex items-center justify-between p-3 border-b border-border bg-background">
        <Button variant="ghost" size="sm" onClick={() => setOpen(!open)}>
          <Menu className="w-4 h-4" />
        </Button>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-emerald-600 flex items-center justify-center">
            <span className="text-white text-[10px] font-black">M</span>
          </div>
        </div>
      </div>

      {/* Mobile overlay */}
      <div className={`sm:hidden ${open ? 'block' : 'hidden'} fixed inset-0 z-40`}>
        <div className="absolute inset-0 bg-black/60" onClick={() => setOpen(false)} />
        <aside className="relative h-full w-64 bg-sidebar border-r border-sidebar-border overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b border-border">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-emerald-600 flex items-center justify-center">
                <span className="text-white text-xs font-black">M</span>
              </div>
              <span className="text-sm font-bold text-foreground">MetalMind</span>
            </div>
            <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <nav className="p-3 space-y-1">
            {navItems.map(({ href, label, icon: Icon }) => (
              <Link
                key={label}
                href={href}
                className={cn(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                  pathname === href
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )}
              >
                <Icon className="w-4 h-4" />
                {label}
              </Link>
            ))}
          </nav>
        </aside>
      </div>

      {/* Desktop sidebar */}
      <aside className="hidden sm:flex flex-col w-56 bg-sidebar border-r border-sidebar-border sticky top-0 h-screen shrink-0">
        {/* Brand */}
        <div className="p-4 border-b border-sidebar-border">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-600/20">
              <span className="text-white text-sm font-black">M</span>
            </div>
            <div>
              <p className="text-sm font-bold text-sidebar-foreground">MetalMind</p>
              <p className="text-[9px] font-medium uppercase tracking-widest text-slate-500">SMCForge</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={label}
              href={href}
              className={cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                pathname === href
                  ? "bg-slate-800/60 text-white"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-muted-foreground">All systems operational</span>
          </div>
        </div>
      </aside>
    </>
  )
}
