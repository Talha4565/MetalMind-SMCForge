@echo off
REM MT5 Auto-Append — runs on Windows startup
REM Fetches latest spot data from MT5 and appends to CSV files
REM No Yahoo Finance — pure MT5 spot prices

echo [%date% %time%] Starting MT5 data update...

REM Check if MT5 is running
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I "terminal64.exe" >NUL
if %ERRORLEVEL% neq 0 (
    echo [%date% %time%] MT5 not running, skipping update
    exit /b 1
)

REM Run the MT5 update script
python "%~dp0mt5_update.py" --asset both

echo [%date% %time%] MT5 update complete
