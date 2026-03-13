@echo off
:: GROSMIMI JAPAN Twitter Scheduler - Startup Script
:: Runs the daemon in background, restarts if it crashes

cd /d "Z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"

:loop
echo %date% %time% - Starting twitter_scheduler daemon... >> .tmp\scheduler_restarts.log
python tools\twitter_scheduler.py --daemon >> .tmp\scheduler.log 2>&1
echo %date% %time% - Daemon exited, restarting in 10 seconds... >> .tmp\scheduler_restarts.log
timeout /t 10 /nobreak > nul
goto loop
