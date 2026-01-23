# Start ML-Signals Frontend (React)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting ML-Signals Frontend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path "frontend"

# Check and install dependencies
Write-Host "[1/2] Checking frontend dependencies..." -ForegroundColor Yellow
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
} else {
    Write-Host "Frontend dependencies installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/2] Starting React app on http://localhost:3000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the frontend." -ForegroundColor Gray
Write-Host ""

npm start
