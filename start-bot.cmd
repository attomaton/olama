@echo off
cd /d "%~dp0"
set PYTHONUTF8=1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ollama.ps1" list
"%~dp0.venv\Scripts\python.exe" "%~dp0bot.py"
if errorlevel 1 pause
