@echo off
cd /d "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"
set PYTHONPATH=z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\tools

C:\Python314\python.exe "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\tools\rakuten_daily_report.py" ^
  --days 30 ^
  >> "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\logs\rakuten_daily_report.log" 2>&1
