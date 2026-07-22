# MetalMind SMCForge — Project Instructions for Claude

## Before ANY code change, verify:

1. **Docker running?** `docker ps` — all 5 containers should be up (api, frontend, db, chromadb, etl)
2. **MT5 bar updater running?** Check `data/mt5_prices.json` age < 60s
3. **On main branch?** `git branch --show-current` — don't work on main directly unless it's docs/config
4. **Read the relevant file first** — never edit blind

## Skills to use:

| When | Skill |
|------|-------|
| Design/UI changes | `/impeccable` — critique, polish, audit, colorize, layout |
| Code complexity review | `/ponytail-review` or `/ponytail-audit` |
| Security audit | `security-reviewer` subagent |
| UI consistency | `ui-consistency-checker` subagent |
| Test generation | `/gen-test` |
| API docs/patterns | Reference `project-conventions` skill (auto-loaded) |
| Performance testing | `python scripts/benchmark_api.py` |
| ML/data questions | Check `reports/training_logs/` first |

## MCP servers available:

- **Playwright** — browser automation, visual testing, screenshots
- **GitHub** — PR management, CI checks, issue tracking
- **claude-flow** — agent orchestration

## Critical rules:

- **NEVER commit or push to GitHub unless the user explicitly says "commit" or "push".** No `git commit`, no `git push`, no `git add` followed by commit/push. Build, test, fix, write code — but never commit/push without explicit permission.
- **NEVER take screenshots without explicit user approval.** The screenshot skill is installed but must never be invoked autonomously. Always ask for permission before capturing any screen content.
- **Never edit `.env` files.** Blocked by hook.
- **Never edit CSV dataset files directly.** Use `mt5_bar_updater.py` or the pipeline.
- **Dashboard pages use `TerminalCard`, NOT shadcn Card.** Don't recreate deleted shadcn wrappers.
- **Gold accent is `#d4af37`, Silver accent is `#b0b8c8`.** Warm palette on dark backgrounds.
- **Don't reintroduce gradient text, dot-grid overlays, or glassmorphism.** These were stripped in the vault redesign.
- **The system is signal-generation only.** It cannot execute trades. Don't claim otherwise.

## Before committing:

1. Run `docker ps` — did you break anything?
2. Check `data/mt5_prices.json` age — is the price cache fresh?
3. Run ponytail-review on changed files — any dead code?
4. If changing frontend: test `/dashboard/gold` and `/dashboard/silver` both load
5. If changing backend: test `/api/health` returns 200

## Architecture at a glance:

```
MT5 (Windows host) → mt5_bar_updater.py → CSV datasets + mt5_prices.json
                                              ↓
Docker: Next.js :3000 ← Flask API :5000 ← PostgreSQL :5432 + ChromaDB :8100
```

- **Frontend**: `frontend-next/src/app/` — App Router pages
- **API**: `api/app/main.py` — Flask routes, `api/app/auth.py` — JWT auth, `api/app/profile.py` — user profile/2FA
- **ML**: `models/` — trained .pkl files, `run_pipeline.py` — CLI for retrain/update
- **Data**: `Gold Dataset/`, `Silver Dataset/` — OHLCV CSVs (4 timeframes each)
- **Config**: `config/settings.py` — all paths and asset definitions

## If something breaks:

1. Check Docker logs: `docker logs metalmind-api --tail 50`
2. Check MT5: is MetaTrader 5 running on the Windows host?
3. Check disk: `data/mt5_prices.json` exists and is < 60s old?
4. Restart: `docker compose restart api`
