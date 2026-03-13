# Kazuki Weekly Report - Windows Task Scheduler 등록
# 관리자 권한 파워쉘에서 실행:
#   cd "\\192.168.219.51\Orbiters\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\weekly"
#   .\setup_windows_task.ps1

$TaskName  = "KazukiWeeklyReport"
$UNCDir    = "\\192.168.219.51\Orbiters\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\weekly"
$BatchFile = "$UNCDir\run_weekly.bat"

if (-not (Test-Path $BatchFile)) {
    Write-Host "[ERROR] 파일을 찾을 수 없습니다: $BatchFile" -ForegroundColor Red
    exit 1
}

# 기존 태스크 삭제 (재등록 시)
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "기존 태스크 삭제됨"
}

# 매주 월요일 09:00 실행
$Trigger   = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"
$Action    = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFile`"" -WorkingDirectory $UNCDir
$Settings  = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable:$false
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal `
    -Description "Kazuki Japan Team 위클리 리포트 자동 생성 (매주 월요일 09:00)" | Out-Null

Write-Host ""
Write-Host "등록 완료: $TaskName" -ForegroundColor Green
Write-Host "실행 시간: 매주 월요일 09:00"
Write-Host ""
Write-Host "수동 테스트:"
Write-Host "  schtasks /run /tn $TaskName"
