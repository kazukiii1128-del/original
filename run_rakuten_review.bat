@echo off
cd /d "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"
set PYTHONPATH=tools
set PYTHONIOENCODING=utf-8

echo [%date% %time%] === Rakuten Review Selector Start === >> logs\rakuten_review.log 2>&1

:: Step 1: 送信候補リストを .tmp\pending_review_emails.csv に出力
C:\Python314\python.exe tools\rakuten_review_workflow.py ^
  --days 30 ^
  --export ^
  >> logs\rakuten_review.log 2>&1

:: Step 2: Google Sheetsに書き込み + Teamsに通知
C:\Python314\python.exe tools\selector_notify.py ^
  >> logs\rakuten_review.log 2>&1

echo [%date% %time%] === Selector End (承認後に送信マンが実行) === >> logs\rakuten_review.log 2>&1
