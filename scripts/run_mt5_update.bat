@echo off
REM Run MT5 Data Update — Manual trigger
REM Double-click this file to update CSV data from MT5

echo ========================================
echo MT5 Data Update
echo Time: %DATE% %TIME%
echo ========================================

cd /d C:\Users\Talha\ml-signals

python scripts\mt5_data_update.py --intervals 15m

echo.
echo ========================================
echo Done! Check Gold Dataset and Silver Dataset folders.
echo ========================================
pause
