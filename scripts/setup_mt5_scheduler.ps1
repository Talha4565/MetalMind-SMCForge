# Setup Windows Task Scheduler for MT5 data updates
# Run this ONCE as Administrator

$taskName = "MetalMind-MT5-Update"
$scriptPath = "C:\Users\Talha\ml-signals\scripts\mt5_auto_update.bat"

# Create task action
$action = New-ScheduledTaskAction -Execute $scriptPath -WorkingDirectory "C:\Users\Talha\ml-signals"

# Run daily at 12 PM
$trigger = New-ScheduledTaskTrigger -Daily -At "12:00PM"

# Settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "MT5 spot data update + git push" -Force

Write-Host "✅ Task scheduled: $taskName"
Write-Host "   Runs daily at 12:00 PM"
Write-Host "   Script: $scriptPath"
Write-Host ""
Write-Host "Prerequisites:"
Write-Host "  1. MT5 terminal must be running"
Write-Host "  2. Demo account must be logged in"
Write-Host "  3. XAUUSD and XAGUSD in Market Watch"
