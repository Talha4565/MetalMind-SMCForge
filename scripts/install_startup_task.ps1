# Install MT5 auto-append as Windows startup task
# Run this once with admin privileges

$scriptPath = "C:\Users\Talha\ml-signals\scripts\mt5_startup_update.bat"
$taskName = "MT5-AutoAppend"

# Check if task already exists
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task '$taskName' already exists. Removing..."
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

# Create the task
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "MT5 spot data auto-append on startup"

Write-Host "✅ Task '$taskName' registered successfully"
Write-Host "   Runs at every login, updates gold + silver CSVs from MT5"
Write-Host "   No Yahoo Finance — pure spot prices"
