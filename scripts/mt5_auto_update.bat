@echo off
REM ============================================
REM MT5 Spot Data Auto-Updater
REM Runs: Fetch latest candles → Commit → Push
REM Schedule via Windows Task Scheduler (daily)
REM ============================================

cd /d C:\Users\Talha\ml-signals

echo [%date% %time%] Starting MT5 data update...

REM Fetch latest spot candles from MT5
python scripts/mt5_update.py --asset both
if %errorlevel% neq 0 (
    echo [%date% %time%] MT5 update FAILED
    exit /b 1
)

REM Stage changes
git add "Gold Dataset/" "Silver Dataset/"

REM Check if there are changes
git diff --staged --quiet
if %errorlevel% eq 0 (
    echo [%date% %time%] No new data to commit
    exit /b 0
)

REM Commit and push
git commit -m "data: MT5 spot update %date% %time%"
git push origin main

echo [%date% %time%] Data pushed to GitHub. Retrain will run at 3 AM UTC.
