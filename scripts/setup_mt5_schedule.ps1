# Setup MT5 Data Update Scheduled Task
# Run this ONCE as Administrator to create the scheduled task

$taskName = "MetalMind MT5 Data Update"
$scriptPath = "C:\Users\Talha\ml-signals\scripts\mt5_data_update.py"
$pythonPath = "python"

# Create action
$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "$scriptPath --intervals 15m" `
    -WorkingDirectory "C:\Users\Talha\ml-signals"

# Create trigger: every 4 hours, starting now
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Hours 4) `
    -RepetitionDuration (New-TimeSpan -Days 365)

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Register the task
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Fetches latest 15m OHLCV candles from MT5 for Gold and Silver" `
    -RunLevel Highest

Write-Host "✅ Scheduled task '$taskName' created successfully!" -ForegroundColor Green
Write-Host "   Runs every 4 hours" -ForegroundColor Cyan
Write-Host "   Next run: $((Get-ScheduledTask -TaskName $taskName).Triggers[0].Start)" -ForegroundColor Cyan
