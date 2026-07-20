# Schedule Data Update — PowerShell Script
# Run this script every 4 hours via Windows Task Scheduler
#
# To set up scheduled task:
# $action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\fetch_historical_data.py --once" -WorkingDirectory "C:\Users\Talha\ml-signals"
# $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4)
# Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "MetalMind Data Update" -Description "Fetches latest market data for ML pipeline"

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MetalMind Data Update" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

Set-Location "C:\Users\Talha\ml-signals"

# Fetch gold data
Write-Host "`nFetching Gold data..." -ForegroundColor Yellow
$goldResult = & python scripts\fetch_historical_data.py --asset gold --once 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Gold: SUCCESS" -ForegroundColor Green
} else {
    Write-Host "Gold: FAILED" -ForegroundColor Red
    Write-Host $goldResult
}

# Fetch silver data
Write-Host "`nFetching Silver data..." -ForegroundColor Yellow
$silverResult = & python scripts\fetch_historical_data.py --asset silver --once 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "Silver: SUCCESS" -ForegroundColor Green
} else {
    Write-Host "Silver: FAILED" -ForegroundColor Red
    Write-Host $silverResult
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Update complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
