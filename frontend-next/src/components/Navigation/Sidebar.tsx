'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Menu, Home, ListChecks, ShieldAlert, User, X } from 'lucide-react'
import { useSession } from 'next-auth/react'
import { cn } from '@/lib/utils'

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const { status } = useSession()
  const isAuthenticated = status === 'authenticated'
  const pathname = usePathname()

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Home },
    { href: isAuthenticated ? '/dashboard/watchlist' : '/auth/login', label: 'Watchlist', icon: ListChecks },
    { href: '/dashboard/risk', label: 'Risk', icon: ShieldAlert },
    { href: isAuthenticated ? '/dashboard/profile' : '/auth/login', label: 'Profile', icon: User },
  ]

  return (
    <>
      {/* Mobile toggle */}
      <div className="sm:hidden flex items-center justify-between p-3 border-b border-slate-800 bg-[#0d1220]">
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
        <aside className="relative h-full w-64 bg-[#0d1220] border-r border-slate-800/60 overflow-y-auto">
          <div className="flex items-center justify-between p-4 border-b border-slate-800/60">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-md bg-emerald-600 flex items-center justify-center">
                <span className="text-white text-xs font-black">M</span>
              </div>
              <span className="text-sm font-bold text-slate-200">MetalMind</span>
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
                  pathname === href || pathname.startsWith(href + '/')
                    ? "bg-slate-800/60 text-white"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
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
      <aside className="hidden sm:flex flex-col w-56 bg-[#0d1220] border-r border-slate-800/60 sticky top-0 h-screen shrink-0">
        {/* Brand */}
        <div className="p-4 border-b border-slate-800/60">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shadow-lg shadow-emerald-600/20">
              <span className="text-white text-sm font-black">M</span>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-100">MetalMind</p>
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
                pathname === href || pathname.startsWith(href + '/')
                  ? "bg-slate-800/60 text-white"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              )}
            >
              <Icon className="w-4 h-4" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-4 border-t border-slate-800/60">
          <div className="flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-slate-500">All systems operational</span>
          </div>
        </div>
      </aside>
    </>
  )
}
