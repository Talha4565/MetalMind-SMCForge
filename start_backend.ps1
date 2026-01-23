# Start ML-Signals Backend (Flask API)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting ML-Signals Backend" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path "api"

# Check and install dependencies
Write-Host "[1/2] Checking backend dependencies..." -ForegroundColor Yellow
$flaskInstalled = pip show flask 2>$null
if (-not $flaskInstalled) {
    Write-Host "Installing backend dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    pip install flask-limiter werkzeug
} else {
    Write-Host "Backend dependencies installed." -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/2] Starting Flask API on http://localhost:5000" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop the backend." -ForegroundColor Gray
Write-Host ""

python app/main.py
