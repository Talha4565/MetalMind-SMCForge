---
name: project-conventions
description: MetalMind SMCForge — Bloomberg-terminal design system, gold-token palette, Flask API patterns, component vocabulary, and architecture rules. Loaded automatically for every session.
user-invocable: false
---

# MetalMind SMCForge — Project Conventions

## Architecture

- **Frontend**: Next.js 14 (App Router) at `frontend-next/src/app/`
- **Backend**: Flask 3.0 + Flask-SocketIO at `api/`
- **Database**: SQLAlchemy + Alembic migrations at `migrations/`
- **ML**: XGBoost, SHAP, scikit-learn at `models/`
- **Auth**: next-auth (frontend) + Flask-JWT-Extended + TOTP 2FA (backend)

## Design system — "Bloomberg Terminal"

### Color palette

| Token | Value | Usage |
|-------|-------|-------|
| Background | `#040405` | Page background (near-black, warm) |
| Surface | `#0a0b0f` | Cards, panels, ticker |
| Gold accent | `#d4af37` | Primary CTA, LIVE indicator, gold labels |
| Gold hover | `#e5c158` | Button hover, link hover |
| Warm white | `#e8e4dc` | Body text, card values |
| Muted warm | `#8a8578` | Labels, secondary text, metadata |
| Emerald | `#16b979` | Buy signals, chart area fill, positive indicators |
| Red | `#e84040` | Sell signals, destructive, errors |

### Typography

- **Font**: Geist Sans (headings, body) + Geist Mono (data, labels, code)
- **Headings**: `font-black` (900 weight), tracking `-0.025em` to `-0.03em`
- **Data**: `font-mono` with `tabular-nums` for numbers
- **Labels**: `text-[9px]` to `text-[11px]`, `tracking-widest`, uppercase, `font-mono`
- **Body**: `text-lg` warm-gray, `leading-relaxed`

### Component vocabulary

| Component | When to use | Location |
|-----------|-------------|----------|
| `TerminalCard` | Dashboard panels, data containers | `components/Common/TerminalCard.tsx` |
| `TerminalStatRow` | Label-value pairs inside cards | Exported from `TerminalCard.tsx` |
| `TerminalSectionHeader` | Section dividers inside cards | Exported from `TerminalCard.tsx` |
| `TerminalButton` | All dashboard actions (amber primary) | Exported from `TerminalCard.tsx` |
| `LiveTicker` | Live XAU/USD price display | `components/Landing/LiveTicker.tsx` |

**Rule**: Never use shadcn `<Card>` on dashboard pages. Always use `TerminalCard`. The shadcn wrappers (`avatar`, `dialog`, `progress`, `separator`, `sheet`, `tabs`) were deleted — do not recreate them. Use the terminal-native equivalents.

### Landing page

The landing page at `app/page.tsx` is a self-contained hero with:
- SVG grain texture overlay (feTurbulence filter)
- Vault-light warm gold radial glow
- Metallic gold gradient on "machine precision" (multi-stop, brushed gold)
- Gold-foil metric cards (border `#d4af37/20`, hover glow)
- Dashboard preview mockup with responsive 3-panel terminal layout

The `components/Landing/` directory contains ONLY `LiveTicker.tsx`. All other landing sections were deleted as orphaned code.

### CSS

- `globals.css` defines the dark theme tokens under `:root, .dark`
- Reduced motion: `@media (prefers-reduced-motion: reduce)` resets all animations
- Tailwind v4 with `@theme inline` for token mapping
- Focus indicators: `outline: 2px solid var(--ring)` with amber glow

## API patterns

- Singleton `apiClient` from `lib/api-client.ts` — axios-based with JWT interceptor
- Memory-only token storage (never localStorage)
- Silent token refresh with concurrent-request deduplication
- All endpoints return typed responses (`api-types.ts`)
- Exception: `LiveTicker` uses `apiClient` directly for live prices

## Things that were deleted (do not recreate)

- 6 shadcn wrappers: avatar, dialog, progress, separator, sheet, tabs
- 8 orphaned Landing sections: LandingNavbar, HeroSection, FeaturesSection, BacktestSection, AboutSection, ContactSection, LandingFooter, StatsStrip
- Dead Dashboard components: SignalCard, SHAPExplainer
- Empty Risk/ directory
- middleware.ts (empty matcher)
- manage.py (unused Flask launcher)
- etl/__init__.py (unused version string)
- etl/factory.py, etl/config.py, etl/config_demo.py
