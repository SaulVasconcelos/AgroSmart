@echo off
cd /d "%~dp0"
if not exist "data\raw\sensores.jsonl" (
  py -3 main.py demo
)
py -3 main.py web
pause
