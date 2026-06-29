'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, ShieldAlert, User, BarChart3, Activity, Eye, Menu, X } from 'lucide-react'
import { useSession } from 'next-auth/react'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { href: '/dashboard',           label: 'OVERVIEW',  short: 'OVR', icon: Home      },
  { href: '/dashboard/watchlist', label: 'WATCHLIST', short: 'WCH', icon: Eye       },
  { href: '/backtest',            label: 'BACKTEST',  short: 'BKT', icon: BarChart3 },
  { href: '/dashboard/risk',      label: 'RISK',      short: 'RSK', icon: ShieldAlert },
  { href: '/dashboard/pipeline',  label: 'PIPELINE',  short: 'PIP', icon: Activity  },
  { href: '/dashboard/profile',   label: 'PROFILE',   short: 'PRF', icon: User      },
]

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const { status } = useSession()
  const isAuthenticated = status === 'authenticated'
  const pathname = usePathname()

  const resolvedItems = NAV_ITEMS.map((item) => {
    const needsAuth = item.href !== '/dashboard' && item.href !== '/dashboard/risk'
    return {
      ...item,
      href: needsAuth && !isAuthenticated ? '/auth/login' : item.href,
    }
  })

  return (
    <>
      {/* ── Mobile toggle bar ── */}
      <div className="sm:hidden flex items-center justify-between px-3 py-2 border-b border-terminal-rule bg-sidebar">
        <div className="flex items-center gap-2">
          <span className="text-terminal-hold font-mono text-xs font-bold tracking-widest">MM</span>
          <span className="text-[10px] font-mono text-terminal-label uppercase tracking-[0.2em]">SMCForge</span>
        </div>
        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"}
          aria-expanded={mobileOpen}
          className="p-1.5 text-terminal-label hover:text-terminal-value transition-colors"
        >
          {mobileOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
        </button>
      </div>

      {/* ── Mobile drawer ── */}
      {mobileOpen && (
        <div className="sm:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/70" onClick={() => setMobileOpen(false)} />
          <aside className="relative h-full w-56 bg-sidebar border-r border-terminal-rule flex flex-col">
            <div className="flex items-center justify-between px-4 py-3 border-b border-terminal-rule">
              <div className="flex items-center gap-2">
                <span className="text-terminal-hold font-mono text-sm font-black tracking-widest">MM</span>
                <div>
                  <p className="text-[10px] font-bold text-sidebar-foreground font-mono tracking-widest">METALMIND</p>
                  <p className="text-[8px] text-terminal-label font-mono tracking-[0.25em]">SMCFORGE v1</p>
                </div>
              </div>
              <button onClick={() => setMobileOpen(false)} aria-label="Close navigation menu" className="text-terminal-label hover:text-terminal-value">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <nav className="flex-1 py-2">
              {resolvedItems.map(({ href, label, icon: Icon }) => {
                const active = pathname === href
                return (
                  <Link
                    key={label}
                    href={href}
                    onClick={() => setMobileOpen(false)}
                    className={cn(
                      'flex items-center gap-3 px-4 py-2.5 text-[11px] font-mono font-bold tracking-widest transition-all',
                      active
                        ? 'text-terminal-hold bg-terminal-rule border-l-2 border-terminal-hold'
                        : 'text-terminal-label hover:text-terminal-value hover:bg-terminal-rule/50'
                    )}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    {label}
                  </Link>
                )
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* ── Desktop sidebar ── */}
      <aside className="hidden sm:flex flex-col w-48 bg-sidebar border-r border-terminal-rule sticky top-0 h-screen shrink-0 z-30">
        {/* Brand */}
        <div className="px-4 py-4 border-b border-terminal-rule">
          <Link href="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-7 h-7 bg-terminal-hold flex items-center justify-center shrink-0">
              <span className="text-black text-[11px] font-black font-mono">MM</span>
            </div>
            <div>
              <p className="text-[10px] font-black text-sidebar-foreground font-mono tracking-[0.2em]">METALMIND</p>
              <p className="text-[8px] text-terminal-label font-mono tracking-[0.3em]">SMCFORGE v1</p>
            </div>
          </Link>
        </div>

        {/* Section label */}
        <div className="px-4 pt-4 pb-1">
          <p className="text-[8px] font-mono font-bold text-terminal-label tracking-[0.35em] uppercase">Navigation</p>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-2 pb-2 space-y-px overflow-y-auto">
          {resolvedItems.map(({ href, label, short, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={label}
                href={href}
                className={cn(
                  'flex items-center gap-2.5 px-2 py-2 text-[10px] font-mono font-bold tracking-widest transition-all group relative',
                  active
                    ? 'text-terminal-hold bg-terminal-rule border-l-2 border-terminal-hold pl-[7px]'
                    : 'text-terminal-label hover:text-terminal-value hover:bg-terminal-rule/50 border-l-2 border-transparent'
                )}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span>{label}</span>
                {active && (
                  <span className="ml-auto text-[8px] text-terminal-hold font-mono tracking-wider">{short}</span>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Footer status */}
        <div className="px-4 py-3 border-t border-terminal-rule space-y-1">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-terminal-buy animate-pulse shrink-0" />
            <span className="text-[8px] font-mono text-terminal-label tracking-[0.2em] uppercase">Systems OK</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-terminal-data shrink-0" />
            <span className="text-[8px] font-mono text-terminal-label tracking-[0.2em] uppercase">XAU · XAG Live</span>
          </div>
        </div>
      </aside>
    </>
  )
}
