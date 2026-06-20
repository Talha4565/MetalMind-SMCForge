# Thorough project check report

**Project:** `C:\Users\Talha\ml-signals`  
**Date:** 2026-06-20T01:52:39.332271  
**Languages:** unknown  
**Source files:** 27576  

## Summary

| Severity | Count |
|---|---|
| Critical | 1 |
| Important | 2 |
| Nice-to-have | 2 |

**New since last run:** Possible hardcoded secret  

## Critical

### Possible hardcoded secret
- **Detail:** frontend-next\tsconfig.tsbuildinfo:1: {"fileNames":["./node_modules/typescript/lib/lib.es5.d.ts","./node_modules/typescript/lib/lib.es2015.d.ts","./node_modul
- **Suggestion:** Move to environment variables or a secrets manager

## Important

### Possible N+1 query pattern
- **Detail:** backtesting\export.py
- **Suggestion:** Use eager loading (select_related / prefetch_related) or batch queries

### Possible N+1 query pattern
- **Detail:** etl\alerts.py
- **Suggestion:** Use eager loading (select_related / prefetch_related) or batch queries

## Nice-to-have

### TODO/FIXME found
- **Detail:** run_etl.py:180: # TODO: Implement status check

### TODO/FIXME found
- **Detail:** miscellaneous_archive\planning-docs\FYP_PROGRESS_REPORT.md:232: - [ ] **09:00-10:00**: Code cleanup (remove TODO comments, unused imports)
