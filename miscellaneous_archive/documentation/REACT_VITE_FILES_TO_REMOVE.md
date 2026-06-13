# React and Vite Files Inventory

This document contains a complete list of all React and Vite related files in the ml-signals project that should be removed.

## Root Configuration Files

| File | Path |
|------|------|
| tsconfig.json | frontend/tsconfig.json |
| tsconfig.node.json | frontend/tsconfig.node.json |
| vite.config.ts | frontend/vite.config.ts |
| package.json | frontend/package.json |
| package.simple.json | frontend/package.simple.json |
| package.full.json | frontend/package.full.json |
| package-lock.json | frontend/package-lock.json |
| yarn.lock | frontend/yarn.lock |
| pnpm-lock.yaml | frontend/pnpm-lock.yaml |
| node_modules/ | frontend/node_modules/ |
| index.html | frontend/index.html |
| commitlint.config.cjs | frontend/commitlint.config.cjs |
| .prettierrc | frontend/.prettierrc |
| .prettierignore | frontend/.prettierignore |

## Source Files (.tsx)

| File | Path |
|------|------|
| App.tsx | frontend/src/App.tsx |
| main.tsx | frontend/src/main.tsx |
| router.tsx | frontend/src/router.tsx |
| AppProviders.tsx | frontend/src/providers/AppProviders.tsx |
| Login.tsx | frontend/src/pages/Login.tsx |
| Register.tsx | frontend/src/pages/Register.tsx |
| Dashboard.tsx | frontend/src/pages/Dashboard.tsx |
| Profile.tsx | frontend/src/pages/Profile.tsx |
| ForgotPassword.tsx | frontend/src/pages/ForgotPassword.tsx |
| ResetPassword.tsx | frontend/src/pages/ResetPassword.tsx |
| NotFound.tsx | frontend/src/pages/NotFound.tsx |
| AuthGuard.tsx | frontend/src/guards/AuthGuard.tsx |
| CandlestickChart.tsx | frontend/src/components/trading/CandlestickChart.tsx |
| FeatureImportanceChart.tsx | frontend/src/components/trading/FeatureImportanceChart.tsx |
| PredictionCard.tsx | frontend/src/components/trading/PredictionCard.tsx |
| WatchlistWidget.tsx | frontend/src/components/trading/WatchlistWidget.tsx |
| FormInput.tsx | frontend/src/components/common/FormInput.tsx |
| LoadingSpinner.tsx | frontend/src/components/common/LoadingSpinner.tsx |
| OTPInput.tsx | frontend/src/components/common/OTPInput.tsx |
| PasswordInput.tsx | frontend/src/components/common/PasswordInput.tsx |
| SessionTimeoutWarning.tsx | frontend/src/components/common/SessionTimeoutWarning.tsx |

## TypeScript Files (.ts)

| File | Path |
|------|------|
| vite-env.d.ts | frontend/src/vite-env.d.ts |
| uiStore.ts | frontend/src/store/uiStore.ts |
| client.ts | frontend/src/api/client.ts |
| tokenManager.ts | frontend/src/lib/tokenManager.ts |
| socket.ts | frontend/src/lib/socket.ts |
| secureStorage.ts | frontend/src/lib/secureStorage.ts |
| theme.ts | frontend/src/styles/theme.ts |
| types/index.ts | frontend/src/types/index.ts |

## CSS Files

| File | Path |
|------|------|
| globals.css | frontend/src/styles/globals.css |

## Scripts and Documentation

| File | Path |
|------|------|
| verify-phase0.ps1 | frontend/verify-phase0.ps1 |
| PHASE_0_COMPLETE.md | frontend/PHASE_0_COMPLETE.md |
| PHASE_1_COMPLETE.md | frontend/PHASE_1_COMPLETE.md |
| PHASE_2_COMPLETE.md | frontend/PHASE_2_COMPLETE.md |
| PHASE_3_COMPLETE.md | frontend/PHASE_3_COMPLETE.md |

## Summary

| Category | Count |
|----------|-------|
| Root Config Files | 15 |
| .tsx Source Files | 21 |
| .ts Source Files | 9 |
| CSS Files | 1 |
| Scripts/Docs | 5 |
| **Total** | **51** |

## Directories to Remove

```
frontend/
├── index.html
├── package.json
├── package.simple.json
├── package.full.json
├── package-lock.json
├── yarn.lock
├── pnpm-lock.yaml
├── node_modules/
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── commitlint.config.cjs
├── .prettierrc
├── .prettierignore
├── verify-phase0.ps1
├── PHASE_0_COMPLETE.md
├── PHASE_1_COMPLETE.md
├── PHASE_2_COMPLETE.md
├── PHASE_3_COMPLETE.md
└── src/
    ├── vite-env.d.ts
    ├── main.tsx
    ├── App.tsx
    ├── router.tsx
    ├── types/
    │   └── index.ts
    ├── styles/
    │   ├── theme.ts
    │   └── globals.css
    ├── store/
    │   └── uiStore.ts
    ├── api/
    │   └── client.ts
    ├── lib/
    │   ├── tokenManager.ts
    │   ├── socket.ts
    │   └── secureStorage.ts
    ├── providers/
    │   └── AppProviders.tsx
    ├── pages/
    │   ├── Login.tsx
    │   ├── Register.tsx
    │   ├── Dashboard.tsx
    │   ├── Profile.tsx
    │   ├── ForgotPassword.tsx
    │   ├── ResetPassword.tsx
    │   └── NotFound.tsx
    ├── guards/
    │   └── AuthGuard.tsx
    └── components/
        ├── trading/
        │   ├── CandlestickChart.tsx
        │   ├── FeatureImportanceChart.tsx
        │   ├── PredictionCard.tsx
        │   └── WatchlistWidget.tsx
        └── common/
            ├── FormInput.tsx
            ├── LoadingSpinner.tsx
            ├── OTPInput.tsx
            ├── PasswordInput.tsx
            └── SessionTimeoutWarning.tsx
```

## Commands to Remove

### PowerShell (Windows)

```powershell
# Remove entire frontend directory
Remove-Item -Path "frontend" -Recurse -Force

# Or remove specific file types
Get-ChildItem -Path "frontend" -Include "*.tsx","*.ts","*.jsx","*.js" -Recurse | Remove-Item -Force
```

### Bash (Linux/Mac)

```bash
# Remove entire frontend directory
rm -rf frontend/

# Or remove specific file types
find frontend/ -type f \( -name "*.tsx" -o -name "*.ts" -o -name "*.jsx" -o -name "*.js" \) -delete
```