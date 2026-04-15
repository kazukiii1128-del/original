@echo off
cd /d "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"
set PYTHONPATH=z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\tools

C:\Python314\python.exe "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\tools\amazon_daily_report.py" ^
  >> "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki\logs\amazon_daily_report.log" 2>&1
