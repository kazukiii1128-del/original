# Register Rakuten Review Email as a Windows Task Scheduler task
# Run this script as Administrator once

$taskName = "Rakuten Review Email"
$batPath = "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\run_rakuten_review.bat"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00PM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 15) -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host "Task '$taskName' registered. Runs daily at 14:00 JST."
