# Start both ML-Signals Backend and Frontend
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting ML-Signals Project" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend in new window
Write-Host "Starting Backend (Flask API)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start_backend.ps1"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Frontend in new window
Write-Host "Starting Frontend (React)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-File", "$PSScriptRoot\start_frontend.ps1"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "ML-Signals is starting!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:5000" -ForegroundColor Cyan
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
Write-Host "Two PowerShell windows have been opened." -ForegroundColor Yellow
Write-Host "Close those windows to stop the services." -ForegroundColor Yellow
