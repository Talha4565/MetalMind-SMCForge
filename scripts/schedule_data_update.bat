@echo off
REM Schedule Data Update — Run this script every 4 hours via Windows Task Scheduler
REM
REM To set up:
REM 1. Open Task Scheduler (taskschd.msc)
REM 2. Create Basic Task
REM 3. Name: "MetalMind Data Update"
REM 4. Trigger: Daily, repeat every 4 hours
REM 5. Action: Start Program
REM    Program: python
REM    Arguments: C:\Users\Talha\ml-signals\scripts\fetch_historical_data.py --once
REM    Start in: C:\Users\Talha\ml-signals
REM

echo ========================================
echo MetalMind Data Update
echo Time: %DATE% %TIME%
echo ========================================

cd /d C:\Users\Talha\ml-signals

REM Fetch gold data
echo Fetching Gold data...
python scripts\fetch_historical_data.py --asset gold --once

REM Fetch silver data
echo Fetching Silver data...
python scripts\fetch_historical_data.py --asset silver --once

echo ========================================
echo Update complete
echo ========================================
