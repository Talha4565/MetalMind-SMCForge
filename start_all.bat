@echo off
echo ========================================
echo Starting ML-Signals Project
echo ========================================
echo.

:: Change to the script directory
cd /d %~dp0

:: Start Backend (Flask API on port 5000)
echo Starting Backend (Flask API on port 5000)...
start "ML-Signals Backend" cmd /k "cd /d %~dp0 && python start_api.py"

timeout /t 5 /nobreak >nul

:: Start Frontend (Next.js dev server on port 3000)
echo Starting Frontend (Next.js on port 3000)...
start "ML-Signals Frontend" cmd /k "cd /d %~dp0frontend-next && npm run dev"

echo.
echo ========================================
echo ML-Signals is starting!
echo ========================================
echo.
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:3000
echo Health Check: http://localhost:5000/api/health
echo.
echo Close the command windows to stop the services.
pause
