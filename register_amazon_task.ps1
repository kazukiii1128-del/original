# Register Amazon Daily Report as a Windows Task Scheduler task
# Run this script as Administrator once

$taskName = "Amazon Daily Report"
$batPath = "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\run_amazon_daily_report.bat"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batPath`""
$trigger = New-ScheduledTaskTrigger -Daily -At "08:30AM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -StartWhenAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -RunLevel Highest `
    -Force

Write-Host "Task '$taskName' registered. Runs daily at 08:30 JST."
