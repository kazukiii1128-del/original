@echo off
cd /d "z:\ORBI CLAUDE_0223\ORBITERS CLAUDE\ORBITERS CLAUDE\kazuki"
set PYTHONPATH=tools

C:\Python314\python.exe tools\rakuten_review_workflow.py ^
  --days 30 ^
  --from "littlefingerusa_2@shop.rakuten.co.jp" ^
  >> logs\rakuten_review.log 2>&1