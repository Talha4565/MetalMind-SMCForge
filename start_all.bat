@echo off
echo ========================================
echo Starting ML-Signals Project
echo ========================================
echo.

:: Start Backend (Flask API on port 5000)
echo Starting Backend (Flask API on port 5000)...
start "ML-Signals Backend" cmd /k "cd /d %~dp0api && python app/main.py"

:: Wait for backend to initialize
timeout /t 3 /nobreak >nul

:: The React/Vite frontend dev server is no longer part of the active deployment.
:: Use the Flask-served UI on port 5000 instead.

echo.
echo ========================================
echo ML-Signals is starting!
echo ========================================
echo.
echo Backend API: http://localhost:5000
echo Frontend UI: http://localhost:5000
echo Health Check: http://localhost:5000/api/health
echo.
echo Login Credentials:
echo   Email: demo@metalmind.com
echo   Password: Demo123!@#
echo.
echo Close the command windows to stop the services.
pause
