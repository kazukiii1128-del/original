$unc  = "\\192.168.219.51\Orbiters"
$root = "$unc\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"
$log  = "$root\logs\rakuten_daily_report.log"
$py   = "C:\Python314\python.exe"
$script = "$root\tools\rakuten_daily_report.py"

# Mount Z: if not already available (needed when running as SYSTEM)
if (-not (Test-Path "Z:\")) {
    net use Z: $unc /persistent:no 2>$null
}

Set-Location $root
$env:PYTHONPATH = "$root\tools"

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
"[$timestamp] Starting Rakuten daily report" | Out-File -FilePath $log -Append -Encoding utf8

& $py $script --days 30 2>&1 | Tee-Object -FilePath $log -Append
